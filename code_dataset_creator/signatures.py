"""Dil-ozel fonksiyon/sinif imza tespiti modulu."""

import re


# ---------------------------------------------------------------------------
# Her dil icin (imza_regex, parantez_bekleniyor_mu) eslesmeleri.
# Parantez beklenmiyorsa imza satiri zaten blogun baslangicindir.
# ---------------------------------------------------------------------------

# --- Python: AST kullanildigi icin burada tanimli degil ---

# --- Go: func name(...) { ---
_GO_FUNC = re.compile(
    r"^\s*func\s+(?:\([^)]*\)\s+)?([A-Za-z_][\w]*)\s*\([^{]*\)\s*(?:\([^)]*\)\s*)?(?:[\w\[\]\*,\s]+\s*)?\{"
)
_GO_CLASS = None  # Go'da class yoktur; struct type tanimi farkli islenir

# --- Rust: fn name(...) { veya pub fn name(...) { ---
_RUST_FUNC = re.compile(
    r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?(?:unsafe\s+)?fn\s+([A-Za-z_][\w]*)\s*(?:<[^>]*>)?\s*\([^{]*\)\s*(?:->[^{]+)?\{"
)
_RUST_IMPL = re.compile(
    r"^\s*(?:pub\s+)?impl(?:<[^>]*)?\s+([A-Za-z_][\w]*)[^{]*\{"
)

# --- JavaScript / TypeScript: cok cesitli imza bicimi ---
_JS_FUNC = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*([A-Za-z_][\w]*)\s*\([^{]*\)\s*\{"
)
_JS_ARROW = re.compile(
    r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_][\w]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*(?::\s*[\w<>\[\]|]+\s*)?\=>\s*\{"
)
_JS_METHOD = re.compile(
    r"^\s*(?:(?:public|private|protected|static|async|abstract|override)\s+)*(?:get\s+|set\s+)?([A-Za-z_][\w]*)\s*\([^{;]*\)\s*(?::\s*[\w<>\[\]|&\s]+\s*)?\{"
)
_JS_CLASS = re.compile(
    r"^\s*(?:export\s+)?(?:abstract\s+)?class\s+([A-Za-z_][\w]*)(?:\s+extends\s+[A-Za-z_][\w.]*)?[^{]*\{"
)

# --- Java / C# / Kotlin: modifier* tip ad( ---
_JAVA_FUNC = re.compile(
    r"^\s*(?:(?:public|private|protected|static|final|abstract|synchronized|override|virtual|async|sealed|partial|readonly|extern|new|unsafe|volatile)\s+)*"
    r"(?:[\w<>\[\],\s\?]+\s+)+([A-Za-z_][\w]*)\s*\([^;{]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{"
)
_JAVA_CLASS = re.compile(
    r"^\s*(?:(?:public|private|protected|static|final|abstract|sealed|partial)\s+)*"
    r"(?:class|interface|enum|record)\s+([A-Za-z_][\w]*)(?:<[^>]*)?\s*(?:extends\s+[\w.<>]+)?(?:\s+implements\s+[^{]+)?\{"
)

# --- C / C++: tip ad( { ---
_C_FUNC = re.compile(
    r"^\s*(?:static\s+|inline\s+|extern\s+|constexpr\s+|virtual\s+|explicit\s+)*"
    r"(?:[\w:<>\*&\[\]\s]+\s+)+\*?([A-Za-z_][\w]*)\s*\([^;{}]*\)\s*(?:const\s*)?(?:noexcept\s*)?\{"
)
_CPP_CLASS = re.compile(
    r"^\s*(?:template\s*<[^>]*>\s*)?(?:class|struct)\s+([A-Za-z_][\w]*)(?:\s*:[^{]+)?\s*\{"
)

# --- PHP: function / method ---
_PHP_FUNC = re.compile(
    r"^\s*(?:(?:public|private|protected|static|abstract|final)\s+)*function\s+([A-Za-z_][\w]*)\s*\([^{]*\)\s*(?::\s*[\w\?\\]+\s*)?\{"
)
_PHP_CLASS = re.compile(
    r"^\s*(?:abstract\s+|final\s+)?(?:class|interface|trait|enum)\s+([A-Za-z_][\w]*)(?:\s+extends\s+\S+)?(?:\s+implements\s+[^{]+)?\{"
)

# --- Genel suslu parantez dilleri icin son care regex ---
_GENERIC_FUNC = re.compile(
    r"^\s*(?:public|private|protected|static|async|final|virtual|inline|constexpr|export\s+)?"
    r"(?:[\w:<>,\[\]\*&\s]+\s+)?([A-Za-z_][\w]*)\s*\([^;{}]*\)\s*\{\s*$"
)
_GENERIC_CLASS = re.compile(
    r"^\s*(?:export\s+)?(?:abstract\s+)?class\s+([A-Za-z_][\w]*)[^\{]*\{\s*$"
)

# Kontrol akisi anahtar kelimeleri — hic birinin fonksiyon gibi eslesmesin.
_CONTROL_KEYWORDS = frozenset(
    {"if", "else", "for", "while", "do", "switch", "try", "catch", "finally",
     "with", "match", "case", "when", "loop", "foreach"}
)


def candidate_signatures(lines: list[str], language: str, include_classes: bool) -> list[dict]:
    """Dile gore uygun regex setini kullanarak imza adaylarini dondurur.

    Dondurulen sozlukler: line_index, open_brace_index, name, kind
    """
    if language == "go":
        return _scan_brace_sigs(lines, include_classes, _GO_FUNC, _GO_CLASS)
    if language == "rust":
        return _scan_brace_sigs(lines, include_classes, _RUST_FUNC, _RUST_IMPL)
    if language in {"javascript", "typescript"}:
        return _scan_js_sigs(lines, include_classes)
    if language in {"java", "csharp"}:
        return _scan_brace_sigs(lines, include_classes, _JAVA_FUNC, _JAVA_CLASS)
    if language in {"c", "cpp"}:
        return _scan_brace_sigs(lines, include_classes, _C_FUNC, _CPP_CLASS)
    if language == "php":
        return _scan_brace_sigs(lines, include_classes, _PHP_FUNC, _PHP_CLASS)
    # Diger tum suslu parantezli diller icin genel regex.
    return _scan_brace_sigs(lines, include_classes, _GENERIC_FUNC, _GENERIC_CLASS)


# ---------------------------------------------------------------------------
# Tarama yardimcilari
# ---------------------------------------------------------------------------

def _make_sig(i: int, name: str, kind: str) -> dict:
    return {"line_index": i, "open_brace_index": i, "name": name, "kind": kind}


def _scan_brace_sigs(
    lines: list[str],
    include_classes: bool,
    func_re,
    class_re,
) -> list[dict]:
    """Tek bir fonksiyon + sinif regex ciftini butun satirlara uygular."""
    results: list[dict] = []
    for i, line in enumerate(lines):
        if "{" not in line:
            continue

        if include_classes and class_re:
            m = class_re.match(line)
            if m:
                results.append(_make_sig(i, m.group(1), "class"))
                continue

        m = func_re.match(line)
        if m:
            name = m.group(1)
            if name.lower() not in _CONTROL_KEYWORDS:
                results.append(_make_sig(i, name, "function"))

    return results


def _scan_js_sigs(lines: list[str], include_classes: bool) -> list[dict]:
    """JS/TS icin function, arrow, metot ve class imzalarini tarar."""
    results: list[dict] = []
    for i, line in enumerate(lines):
        if "{" not in line:
            continue

        if include_classes:
            m = _JS_CLASS.match(line)
            if m:
                results.append(_make_sig(i, m.group(1), "class"))
                continue

        # Oncelik sirasi: named function > arrow > method
        m = _JS_FUNC.match(line)
        if m:
            name = m.group(1)
            if name.lower() not in _CONTROL_KEYWORDS:
                results.append(_make_sig(i, name, "function"))
            continue

        m = _JS_ARROW.match(line)
        if m:
            name = m.group(1)
            if name.lower() not in _CONTROL_KEYWORDS:
                results.append(_make_sig(i, name, "function"))
            continue

        m = _JS_METHOD.match(line)
        if m:
            name = m.group(1)
            if name.lower() not in _CONTROL_KEYWORDS:
                results.append(_make_sig(i, name, "method"))

    return results
