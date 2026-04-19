"""Basit metin yerellestirme yardimcilari (en/tr)."""

from typing import Any


MESSAGES = {
    "en": {
        "summary_title": "Result Summary",
        "summary_added": "  ✓ Added            : {written}",
        "summary_total_suffix": " / {total} total chunks",
        "summary_quality": "  ~ Quality filtered : {count} skipped",
        "summary_duplicate": "  ~ Duplicate        : {count} skipped",
        "summary_output": "  Output file        : {path}",
        "file_header": "\n▶ {path}",
        "chunk_added": "  ✓ {name} ({chunk_type}, lines {start}-{end}) quality={quality:.2f}",
        "chunk_quality_skipped": "  ✗ {name} ({chunk_type}, lines {start}-{end}) quality={quality:.2f} < {threshold} - skipped",
        "chunk_duplicate_skipped": "  ~ {name} - duplicate, skipped",
        "ai_request": "    [AI ->] {name} ({language}/{chunk_type}) | model={model} | {code_len} chars | {preview}",
        "ai_response": "    [AI <-] {name} | complexity={complexity} | {preview}",
        "ai_request_failed": "    [AI x] {name} - request failed: {error}",
        "ai_parse_failed": "    [AI x] {name} - response parsing failed",
        "ai_progress": "  {spinner} AI analyzing chunks... processed={processed} added={added}",
        "ai_done": "  AI analysis completed: processed={processed}",
        "help_api_key_file": "Path to API key file (.env or plain text)",
        "help_verbose": "Print each extracted chunk and AI request/response logs",
        "help_lang": "Output language: en (English, default) or tr (Turkish)",
        "clone_start": "Cloning repository to /tmp: {url}",
        "clone_done": "Repository cloned: {path}",
        "clone_failed": "Git clone failed",
        "cleanup_done": "Temporary repository removed: {path}",
        "cleanup_skipped": "Temporary repository kept: {path}",
    },
    "tr": {
        "summary_title": "Sonuc Ozeti",
        "summary_added": "  ✓ Eklenen          : {written}",
        "summary_total_suffix": " / {total} toplam parca",
        "summary_quality": "  ~ Kalite filtresi  : {count} atlandi",
        "summary_duplicate": "  ~ Tekrar (kopya)   : {count} atlandi",
        "summary_output": "  Cikti dosyasi      : {path}",
        "file_header": "\n▶ {path}",
        "chunk_added": "  ✓ {name} ({chunk_type}, satir {start}-{end}) kalite={quality:.2f}",
        "chunk_quality_skipped": "  ✗ {name} ({chunk_type}, satir {start}-{end}) kalite={quality:.2f} < {threshold} - atlandi",
        "chunk_duplicate_skipped": "  ~ {name} - tekrar, atlandi",
        "ai_request": "    [AI ->] {name} ({language}/{chunk_type}) | model={model} | {code_len} karakter | {preview}",
        "ai_response": "    [AI <-] {name} | complexity={complexity} | {preview}",
        "ai_request_failed": "    [AI x] {name} - istek basarisiz: {error}",
        "ai_parse_failed": "    [AI x] {name} - yanit ayrisitirilamadi",
        "ai_progress": "  {spinner} AI parcalari analiz ediyor... islenen={processed} eklenen={added}",
        "ai_done": "  AI analizi tamamlandi: islenen={processed}",
        "help_api_key_file": "API anahtarini iceren dosya yolu (.env veya duz metin)",
        "help_verbose": "Cikartilan her parcayi ve AI istek/cevabini terminale yazdir",
        "help_lang": "Cikti dili: en (Ingilizce, varsayilan) veya tr (Turkce)",
        "clone_start": "Depo /tmp altina klonlaniyor: {url}",
        "clone_done": "Depo klonlandi: {path}",
        "clone_failed": "Git klonlama basarisiz",
        "cleanup_done": "Gecici depo silindi: {path}",
        "cleanup_skipped": "Gecici depo korundu: {path}",
    },
}


def t(lang: str, key: str, **kwargs: Any) -> str:
    """Dile gore metni dondurur; bulunamazsa Ingilizceye duser."""
    table = MESSAGES.get(lang, MESSAGES["en"])
    template = table.get(key, MESSAGES["en"].get(key, key))
    return template.format(**kwargs)
