import hashlib
import json
from pathlib import Path
from typing import Iterator, Optional

from .ai_client import AIExplainerClient, AISettings
from .colors import cyan, dim, green, red
from .constants import SKIP_DIRS, SUPPORTED_EXTENSIONS
from .extractors import CodeExtractor
from .filters import is_valid_source
from .i18n import t
from .quality import ExplanationQualityScorer


class CodeDatasetCreator:
    def __init__(
        self,
        source_dir: Path,
        output_file: Path,
        min_file_lines: int = 5,
        min_chunk_lines: int = 4,
        include_classes: bool = True,
        ai_settings: Optional[AISettings] = None,
        min_quality_score: float = 0.45,
        verbose: bool = False,
        output_lang: str = "en",
    ) -> None:
        """Tek calisma icin cikarma, AI ve kalite filtre ayarlarini hazirlar."""
        self.source_dir = source_dir
        self.output_file = output_file
        self.min_file_lines = min_file_lines
        self.min_quality_score = min_quality_score
        self.verbose = verbose
        self.output_lang = output_lang
        self.quality_scorer = ExplanationQualityScorer(output_lang=output_lang)
        self.ai_settings = ai_settings or AISettings(enabled=False)
        ai_client = AIExplainerClient(self.ai_settings)
        self.extractor = CodeExtractor(
            source_dir=source_dir,
            min_chunk_lines=min_chunk_lines,
            include_classes=include_classes,
            ai_client=ai_client,
            output_lang=output_lang,
        )

    def run(self) -> tuple[int, int, int]:
        """JSONL orneklerini uretir; (eklenen, kalite_atlanan, tekrar_atlanan) dondurur."""
        chunks_written = 0
        skipped_quality = 0
        skipped_duplicate = 0
        seen_hashes: set[str] = set()
        ai_processed = 0
        ai_spinner_idx = 0
        ai_spinner = ["|", "/", "-", "\\"]
        show_ai_progress = self.ai_settings.enabled and not self.verbose

        def _render_ai_progress() -> None:
            nonlocal ai_spinner_idx
            if not show_ai_progress:
                return
            frame = ai_spinner[ai_spinner_idx % len(ai_spinner)]
            ai_spinner_idx += 1
            msg = t(
                self.output_lang,
                "ai_progress",
                spinner=frame,
                processed=ai_processed,
                added=chunks_written,
            )
            print("\r" + cyan(msg), end="", flush=True)

        with self.output_file.open("w", encoding="utf-8") as out:
            for file_path in self._iter_source_files():
                file_text = self._safe_read(file_path)
                if file_text is None:
                    continue

                # Dusuk bilgi tasiyan dosyalari parcalama oncesi ele.
                if not is_valid_source(file_path, file_text, self.min_file_lines):
                    continue

                if self.verbose:
                    rel = file_path.relative_to(self.source_dir)
                    print(cyan(t(self.output_lang, "file_header", path=rel)))

                for chunk in self.extractor.extract_chunks(file_path, file_text):
                    if show_ai_progress:
                        ai_processed += 1
                        _render_ai_progress()

                    # Egitim verisine yazmadan once zayif aciklamalari ele.
                    quality = self.quality_scorer.score(
                        code=chunk.code,
                        explanation=chunk.explanation,
                        time_complexity=chunk.time_complexity,
                        chunk_type=chunk.chunk_type,
                    )
                    if quality < self.min_quality_score:
                        skipped_quality += 1
                        if self.verbose:
                            print(red(t(
                                self.output_lang,
                                "chunk_quality_skipped",
                                name=chunk.name,
                                chunk_type=chunk.chunk_type,
                                start=chunk.start_line,
                                end=chunk.end_line,
                                quality=quality,
                                threshold=self.min_quality_score,
                            )))
                        continue
                    chunk.quality_score = quality

                    # Dosyalar/variyantlar arasinda ayni kod govdesini tekillestir.
                    chunk_hash = hashlib.sha256(chunk.code.encode("utf-8")).hexdigest()
                    if chunk_hash in seen_hashes:
                        skipped_duplicate += 1
                        if self.verbose:
                            print(dim(t(self.output_lang, "chunk_duplicate_skipped", name=chunk.name)))
                        continue
                    seen_hashes.add(chunk_hash)

                    if self.verbose:
                        print(green(t(
                            self.output_lang,
                            "chunk_added",
                            name=chunk.name,
                            chunk_type=chunk.chunk_type,
                            start=chunk.start_line,
                            end=chunk.end_line,
                            quality=quality,
                        )))

                    out.write(json.dumps(chunk.__dict__, ensure_ascii=False) + "\n")
                    chunks_written += 1

                    if show_ai_progress:
                        _render_ai_progress()

        if show_ai_progress:
            done_msg = t(self.output_lang, "ai_done", processed=ai_processed)
            print("\r" + green(done_msg) + " " * 12)

        return chunks_written, skipped_quality, skipped_duplicate

    def _iter_source_files(self) -> Iterator[Path]:
        """Uzanti ve dizin filtrelerinden gecen aday kaynak dosyalari dondurur."""
        for path in self.source_dir.rglob("*"):
            if path.is_dir():
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            yield path

    def _safe_read(self, path: Path) -> Optional[str]:
        """Metin dosyasini guvenli okur; okunamazsa veya binary ise None doner."""
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return None
        except OSError:
            return None
