import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib import error, request

from .i18n import t


@dataclass
class AISettings:
    """Harici AI aciklama cagrilari icin calisma zamani ayarlari."""
    enabled: bool = False
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    base_url: str = "https://api.openai.com/v1/chat/completions"
    api_key: Optional[str] = None
    api_key_file: Optional[Path] = None
    timeout_seconds: int = 20
    verbose: bool = False
    output_lang: str = "en"  # "tr" veya "en"


class AIExplainerClient:
    def __init__(self, settings: AISettings) -> None:
        """Istek olusturma ve tekrar denemede kullanilacak AI ayarlarini saklar."""
        self.settings = settings

    def _resolve_api_key(self) -> Optional[str]:
        """API anahtarini oncelik siresiyle cozer: dogrudan deger > dosya > ortam degiskeni."""
        if self.settings.api_key:
            return self.settings.api_key
        if self.settings.api_key_file:
            try:
                return Path(self.settings.api_key_file).read_text(encoding="utf-8").strip()
            except OSError:
                return None
        return os.getenv("OPENAI_API_KEY")

    def is_ready(self) -> bool:
        """AI modu acik ve API anahtari mevcutsa True dondurur."""
        if not self.settings.enabled:
            return False
        return bool(self._resolve_api_key())

    def explain_code(
        self,
        code: str,
        name: str,
        language: str,
        chunk_type: str,
    ) -> Optional[tuple[str, Optional[str]]]:
        """Modelden aciklama ister ve kati JSON yanitini ayristirir."""
        if not self.is_ready() or self.settings.provider.lower() != "openai":
            return None

        api_key = self._resolve_api_key()
        if not api_key:
            return None

        if self.settings.output_lang == "en":
            system_prompt = (
                "You are a senior code analyst. Return strict JSON with keys: "
                "explanation (string), time_complexity (string or null). "
                "Use English for explanation text. Keep tone technical, precise, and concise."
            )
            user_prompt = (
                "Explain the code behavior accurately. Include the method/algorithm used. "
                "Report time complexity when inferable, otherwise null. Avoid vague statements.\n\n"
                f"Language: {language}\n"
                f"Chunk type: {chunk_type}\n"
                f"Name: {name}\n\n"
                f"Code:\n{code}"
            )
        else:
            system_prompt = (
                "You are a senior code analyst. Return strict JSON with keys: "
                "explanation (string), time_complexity (string or null). "
                "Use Turkish for explanation text. Keep tone technical, precise, and concise."
            )
            user_prompt = (
                "Kodun ne yaptigini teknik ve acik bicimde anlat. "
                "Yaklasim/algoritmayi belirt. Zaman karmasikligini cikarabiliyorsan yaz, "
                "cikaramiyorsan null don. Belirsiz cumleler kullanma.\n\n"
                f"Dil: {language}\n"
                f"Parca turu: {chunk_type}\n"
                f"Ad: {name}\n\n"
                f"Kod:\n{code}"
            )

        payload = {
            "model": self.settings.model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        req = request.Request(
            self.settings.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )

        if self.settings.verbose:
            from .colors import bold, cyan, dim
            code_preview = code[:120].replace("\n", " ")
            print(
                cyan(
                    t(
                        self.settings.output_lang,
                        "ai_request",
                        name=name,
                        language=language,
                        chunk_type=chunk_type,
                        model=self.settings.model,
                        code_len=len(code),
                        preview=code_preview,
                    )
                )
            )

        try:
            with request.urlopen(req, timeout=self.settings.timeout_seconds) as resp:
                body = resp.read().decode("utf-8")
        except (error.URLError, error.HTTPError, TimeoutError) as exc:
            if self.settings.verbose:
                from .colors import red
                print(red(t(self.settings.output_lang, "ai_request_failed", name=name, error=exc)))
            return None

        try:
            raw = json.loads(body)
            content = raw["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            explanation = parsed.get("explanation")
            complexity = parsed.get("time_complexity")
            if not isinstance(explanation, str) or not explanation.strip():
                return None
            if complexity is not None and not isinstance(complexity, str):
                complexity = None
            if self.settings.verbose:
                from .colors import green
                exp_preview = explanation.strip()[:100].replace("\n", " ")
                print(
                    green(
                        t(
                            self.settings.output_lang,
                            "ai_response",
                            name=name,
                            complexity=complexity or "?",
                            preview=exp_preview,
                        )
                    )
                )
            return explanation.strip(), complexity
        except (KeyError, IndexError, TypeError, json.JSONDecodeError):
            if self.settings.verbose:
                from .colors import red
                print(red(t(self.settings.output_lang, "ai_parse_failed", name=name)))
            return None
