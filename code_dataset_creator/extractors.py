import ast
import hashlib
import re
from pathlib import Path
from typing import Iterator, Optional

from .ai_client import AIExplainerClient
from .constants import SUPPORTED_EXTENSIONS
from .explainers import CodeExplainer
from .models import CodeChunk
from .signatures import candidate_signatures


class CodeExtractor:
    def __init__(
        self,
        source_dir: Path,
        min_chunk_lines: int,
        include_classes: bool,
        ai_client: Optional[AIExplainerClient] = None,
        explainer: Optional[CodeExplainer] = None,
        output_lang: str = "en",
    ) -> None:
        """Parca cikarma kurallarini ve aciklama altyapisini ayarlar."""
        self.source_dir = source_dir
        self.min_chunk_lines = min_chunk_lines
        self.include_classes = include_classes
        self.explainer = explainer or CodeExplainer(ai_client=ai_client, output_lang=output_lang)

    def extract_chunks(self, path: Path, text: str) -> Iterator[CodeChunk]:
        """Dosya icerigini dil-ozel parca cikarma stratejisine yonlendirir."""
        language = SUPPORTED_EXTENSIONS[path.suffix.lower()]
        rel_path = str(path.relative_to(self.source_dir))

        if language == "python":
            yield from self._extract_python_chunks(rel_path, text)
            return

        if language == "ruby":
            yield from self._extract_ruby_chunks(rel_path, language, text)
            return

        yield from self._extract_brace_language_chunks(rel_path, language, text)

    def _extract_python_chunks(self, rel_path: str, text: str) -> Iterator[CodeChunk]:
        """Python fonksiyon/metot/sinif parcalarini AST sinirlariyla cikarir."""
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return

        lines = text.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                chunk = self._build_python_node_chunk(
                    rel_path=rel_path,
                    language="python",
                    text_lines=lines,
                    node=node,
                    chunk_type="method" if self._is_method(node, tree) else "function",
                    name=node.name,
                )
                if chunk:
                    yield chunk

            if self.include_classes and isinstance(node, ast.ClassDef):
                chunk = self._build_python_node_chunk(
                    rel_path=rel_path,
                    language="python",
                    text_lines=lines,
                    node=node,
                    chunk_type="class",
                    name=node.name,
                )
                if chunk:
                    yield chunk

    def _is_method(self, target_node: ast.AST, tree: ast.AST) -> bool:
        """Verilen fonksiyon dugumu bir sinif govdesindeyse True dondurur."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for body_node in node.body:
                    if body_node is target_node:
                        return True
        return False

    def _build_python_node_chunk(
        self,
        rel_path: str,
        language: str,
        text_lines: list[str],
        node: ast.AST,
        chunk_type: str,
        name: str,
    ) -> Optional[CodeChunk]:
        """AST dugumunden, kalite filtrelerini gecerse CodeChunk olusturur."""
        start_line = getattr(node, "lineno", None)
        end_line = getattr(node, "end_lineno", None)
        if not start_line or not end_line:
            return None

        code = "\n".join(text_lines[start_line - 1 : end_line]).strip("\n")
        if not self._is_meaningful_chunk(name, code, chunk_type):
            return None

        explanation, complexity = self.explainer.explain_code(code, name, language, chunk_type)
        return CodeChunk(
            id=self._make_chunk_id(rel_path, name, start_line),
            path=rel_path,
            language=language,
            chunk_type=chunk_type,
            name=name,
            code=code,
            start_line=start_line,
            end_line=end_line,
            explanation=explanation,
            time_complexity=complexity,
        )

    def _extract_ruby_chunks(
        self,
        rel_path: str,
        language: str,
        text: str,
    ) -> Iterator[CodeChunk]:
        """Ruby def/end bloklarini satirlari tarayarak cikarir."""
        lines = text.splitlines()
        # def ile baslayan metot imzalarini bul.
        def_re = re.compile(
            r"^\s*(?:def\s+self\.)?def\s+([A-Za-z_][\w?!]*)\s*[\(\s]",
        )
        # Ruby'de class/module tanimlari da end ile kapanir.
        class_re = re.compile(
            r"^\s*(?:class|module)\s+([A-Za-z_][\w:]*)",
        )

        depth_stack: list[str] = []  # her acik blogun tipi
        for i, line in enumerate(lines):
            stripped = line.strip()

            # Ic ice if/do/while/begin de depth arttirir.
            if re.match(r"\b(if|unless|until|while|for|do|begin|case)\b", stripped):
                depth_stack.append("control")
                continue

            cm = class_re.match(line)
            if cm:
                depth_stack.append(f"class:{cm.group(1)}:{i}")
                continue

            dm = def_re.match(line)
            if dm:
                depth_stack.append(f"def:{dm.group(1)}:{i}")
                continue

            if stripped == "end" and depth_stack:
                frame = depth_stack.pop()
                parts = frame.split(":")
                kind = parts[0]
                if kind == "control":
                    continue
                if kind == "class" and not self.include_classes:
                    continue
                name = parts[1]
                start_idx = int(parts[2])
                code = "\n".join(lines[start_idx : i + 1]).strip("\n")
                chunk_type = "class" if kind == "class" else "function"
                if not self._is_meaningful_chunk(name, code, chunk_type):
                    continue
                explanation, complexity = self.explainer.explain_code(code, name, language, chunk_type)
                yield CodeChunk(
                    id=self._make_chunk_id(rel_path, name, start_idx + 1),
                    path=rel_path,
                    language=language,
                    chunk_type=chunk_type,
                    name=name,
                    code=code,
                    start_line=start_idx + 1,
                    end_line=i + 1,
                    explanation=explanation,
                    time_complexity=complexity,
                )

    def _extract_brace_language_chunks(
        self,
        rel_path: str,
        language: str,
        text: str,
    ) -> Iterator[CodeChunk]:
        """Suslu parantezli dillerde imza + parantez esleme ile parcalari cikarir."""
        lines = text.splitlines()
        signatures = candidate_signatures(lines, language, self.include_classes)

        for signature in signatures:
            start_idx = signature["line_index"]
            open_brace_idx = signature["open_brace_index"]
            end_idx = self._find_matching_brace(lines, open_brace_idx)
            if end_idx is None:
                continue

            code = "\n".join(lines[start_idx : end_idx + 1]).strip("\n")
            name = signature["name"]
            chunk_type = signature["kind"]

            if not self._is_meaningful_chunk(name, code, chunk_type):
                continue

            explanation, complexity = self.explainer.explain_code(code, name, language, chunk_type)
            start_line = start_idx + 1
            end_line = end_idx + 1
            yield CodeChunk(
                id=self._make_chunk_id(rel_path, name, start_line),
                path=rel_path,
                language=language,
                chunk_type=chunk_type,
                name=name,
                code=code,
                start_line=start_line,
                end_line=end_line,
                explanation=explanation,
                time_complexity=complexity,
            )


    def _find_matching_brace(self, lines: list[str], start_idx: int) -> Optional[int]:
        """start_idx noktasinda baslayan blogun kapanis parantezini bulur."""
        depth = 0
        in_string: Optional[str] = None
        escaped = False

        # String icindeki parantezler cikarmayi bozmasin diye tirnak durumunu takip et.
        for i in range(start_idx, len(lines)):
            for ch in lines[i]:
                if in_string:
                    if escaped:
                        escaped = False
                    elif ch == "\\":
                        escaped = True
                    elif ch == in_string:
                        in_string = None
                    continue

                if ch in {'"', "'", "`"}:
                    in_string = ch
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        return i

        return None

    def _is_meaningful_chunk(self, name: str, code: str, chunk_type: str) -> bool:
        """Onemsiz parcayi eler, mantik tasiyan kod bolumlerini tutar."""
        lines = [line for line in code.splitlines() if line.strip()]
        if len(lines) < self.min_chunk_lines:
            return False

        lowered_name = name.lower()
        if lowered_name.startswith("get") or lowered_name.startswith("set"):
            if len(lines) <= 8:
                return False

        if lowered_name in {"tostring", "hashcode", "equals", "repr"} and len(lines) <= 10:
            return False

        body_text = "\n".join(lines)
        token_count = len(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", body_text))
        if token_count < 18 and chunk_type != "class":
            return False

        logic_markers = [
            "if ",
            "for ",
            "while ",
            "switch",
            "try",
            "except",
            "catch",
            "return",
            "append",
            "sort",
            "map",
            "filter",
        ]
        marker_hits = sum(1 for marker in logic_markers if marker in body_text)
        if marker_hits == 0 and chunk_type != "class":
            return False

        return True

    def _make_chunk_id(self, rel_path: str, name: str, start_line: int) -> str:
        """Dosya yolu, sembol ve satirdan kararli bir parca kimligi uretir."""
        raw = f"{rel_path}:{name}:{start_line}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()
