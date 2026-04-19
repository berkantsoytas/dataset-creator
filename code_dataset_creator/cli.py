import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

from .ai_client import AISettings
from .colors import bold, cyan, dim, green, red, yellow
from .creator import CodeDatasetCreator
from .i18n import t


def parse_args() -> argparse.Namespace:
    """Veri seti uretimi icin komut satiri argumanlarini cozer ve dondurur."""
    parser = argparse.ArgumentParser(
        description="Convert source code repositories to high-quality JSONL training data"
    )
    parser.add_argument(
        "--source",
        type=str,
        default=".",
        help="Source directory path or git repository URL",
    )
    parser.add_argument(
        "--clone-base-dir",
        type=Path,
        default=Path("/tmp"),
        help="Base directory for temporary git clone when --source is a URL",
    )
    parser.add_argument(
        "--keep-cloned-repo",
        action="store_true",
        help="Do not delete temporary cloned repository after analysis",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dataset.jsonl"),
        help="Output JSONL file path",
    )
    parser.add_argument(
        "--min-file-lines",
        type=int,
        default=5,
        help="Skip files shorter than this many lines",
    )
    parser.add_argument(
        "--min-chunk-lines",
        type=int,
        default=4,
        help="Skip code chunks shorter than this many non-empty lines",
    )
    parser.add_argument(
        "--exclude-classes",
        action="store_true",
        help="Do not include class-level chunks",
    )
    parser.add_argument(
        "--use-ai",
        action="store_true",
        help="Enable AI-based code explanation generation",
    )
    parser.add_argument(
        "--ai-provider",
        default="openai",
        help="AI provider name (currently: openai)",
    )
    parser.add_argument(
        "--ai-model",
        default="gpt-4o-mini",
        help="Model name used by the AI provider",
    )
    parser.add_argument(
        "--ai-base-url",
        default="https://api.openai.com/v1/chat/completions",
        help="Completion endpoint URL",
    )
    parser.add_argument(
        "--ai-timeout-seconds",
        type=int,
        default=20,
        help="AI request timeout in seconds",
    )
    parser.add_argument(
        "--ai-api-key-file",
        type=Path,
        default=None,
        help=t("en", "help_api_key_file"),
    )
    parser.add_argument(
        "--min-quality-score",
        type=float,
        default=0.45,
        help="Minimum explanation quality score in range [0,1]",
    )
    verbose_group = parser.add_mutually_exclusive_group()
    verbose_group.add_argument(
        "--verbose",
        dest="verbose",
        action="store_true",
        help=t("en", "help_verbose"),
    )
    verbose_group.add_argument(
        "--no-verbose",
        dest="verbose",
        action="store_false",
        help="Disable verbose output",
    )
    parser.set_defaults(verbose=True)
    parser.add_argument(
        "--lang",
        choices=["tr", "en"],
        default="en",
        help=t("en", "help_lang"),
    )
    return parser.parse_args()


def _looks_like_git_url(value: str) -> bool:
    lowered = value.lower()
    if lowered.startswith(("http://", "https://", "ssh://", "git@")):
        return True
    return lowered.endswith(".git")


def _resolve_source_dir(source_arg: str, lang: str, clone_base_dir: Path) -> Tuple[Path, Optional[Path]]:
    """Yerel yol veya git URL'den calisacagimiz kaynak dizini cozer."""
    if not _looks_like_git_url(source_arg):
        return Path(source_arg), None

    try:
        clone_base_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise SystemExit(f"Cannot create clone base dir '{clone_base_dir}': {exc}") from exc

    tmp_root = Path(tempfile.mkdtemp(prefix="dataset-creator-", dir=str(clone_base_dir)))
    clone_dir = tmp_root / "repo"
    print(cyan(t(lang, "clone_start", url=source_arg)))

    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", source_arg, str(clone_dir)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError as exc:
        shutil.rmtree(tmp_root, ignore_errors=True)
        raise SystemExit(f"git command not found: {exc}") from exc
    except subprocess.CalledProcessError as exc:
        err = (exc.stderr or "").strip()
        shutil.rmtree(tmp_root, ignore_errors=True)
        if err:
            raise SystemExit(f"{t(lang, 'clone_failed')}: {err}") from exc
        raise SystemExit(t(lang, "clone_failed")) from exc

    print(green(t(lang, "clone_done", path=clone_dir)))
    return clone_dir, tmp_root


def main() -> None:
    """CLI argumanlarindan calisma ayarlarini kurar ve uretimi baslatir."""
    args = parse_args()
    ai_settings = AISettings(
        enabled=args.use_ai,
        provider=args.ai_provider,
        model=args.ai_model,
        base_url=args.ai_base_url,
        timeout_seconds=args.ai_timeout_seconds,
        api_key_file=args.ai_api_key_file,
        verbose=args.verbose,
        output_lang=args.lang,
    )

    source_dir, tmp_root = _resolve_source_dir(args.source, args.lang, args.clone_base_dir)

    try:
        creator = CodeDatasetCreator(
            source_dir=source_dir,
            output_file=args.output,
            min_file_lines=args.min_file_lines,
            min_chunk_lines=args.min_chunk_lines,
            include_classes=not args.exclude_classes,
            ai_settings=ai_settings,
            min_quality_score=args.min_quality_score,
            verbose=args.verbose,
            output_lang=args.lang,
        )

        written, skipped_q, skipped_dup = creator.run()
    finally:
        if tmp_root is not None:
            if args.keep_cloned_repo:
                print(dim(t(args.lang, "cleanup_skipped", path=tmp_root)))
            else:
                shutil.rmtree(tmp_root, ignore_errors=True)
                print(dim(t(args.lang, "cleanup_done", path=tmp_root)))

    total_seen = written + skipped_q + skipped_dup
    print()
    print(bold("─" * 52))
    print(bold(f"  {t(args.lang, 'summary_title')}"))
    print(bold("─" * 52))
    print(green(t(args.lang, "summary_added", written=written)) + dim(t(args.lang, "summary_total_suffix", total=total_seen)))
    print(yellow(t(args.lang, "summary_quality", count=skipped_q)))
    print(dim(t(args.lang, "summary_duplicate", count=skipped_dup)))
    print(bold("─" * 52))
    print(t(args.lang, "summary_output", path=args.output))
    print(bold("─" * 52))


if __name__ == "__main__":
    main()
