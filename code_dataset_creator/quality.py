import re
from typing import Optional


class ExplanationQualityScorer:
    def __init__(self, output_lang: str = "en") -> None:
        """Skorlama sinyallerini secilen aciklama diline gore ayarlar."""
        self.output_lang = output_lang if output_lang in {"en", "tr"} else "en"

    def score(
        self,
        code: str,
        explanation: str,
        time_complexity: Optional[str],
        chunk_type: str,
    ) -> float:
        """Aciklama kalitesini ozgulluk ve kod uyumuna gore [0,1] araliginda puanlar."""
        score = 0.0
        lowered = explanation.lower()
        code_lowered = code.lower()

        if self.output_lang == "tr":
            method_markers = [
                "algoritma",
                "yaklasim",
                "iter",
                "dongu",
                "kosul",
                "dal",
                "adim",
            ]
            complexity_markers = ["o(", "karmasiklik", "dogrusal", "logaritmik", "lineer"]
            loop_markers = ["dongu", "iter", "tek gecis", "uzerinden gec"]
            condition_markers = ["kosul", "dallan", "if"]
            class_marker = "sinif"
            vague_markers = [
                "bu kod bir sey yapiyor",
                "cesitli gorevler",
                "bir miktar mantik",
                "genel",
                "temel fonksiyon",
                "belirsiz",
            ]
        else:
            method_markers = ["algorithm", "approach", "iterate", "branch", "condition", "loop"]
            complexity_markers = ["o(", "complexity", "linear", "log"]
            loop_markers = ["loop", "iterate", "pass over"]
            condition_markers = ["condition", "branch"]
            class_marker = "class"
            vague_markers = [
                "this code does something",
                "various tasks",
                "some logic",
                "generic",
                "basic function",
            ]

        # Uzunluk, gereksiz uzatmayi tesvik etmeden tamlik icin yumusak bir sinyaldir.
        words = len(re.findall(r"\w+", explanation))
        if words >= 18:
            score += 0.25
        elif words >= 12:
            score += 0.15
        elif words >= 8:
            score += 0.08

        # Yontem ve calisma yapisini belirten aciklamalari odullendir.
        if any(marker in lowered for marker in method_markers):
            score += 0.2

        # Karmasiklik bilgisi varsa ek puan ver.
        if time_complexity:
            score += 0.2
        elif any(tok in lowered for tok in complexity_markers):
            score += 0.12

        # Aciklamanin koddaki gercek sinyallerle uyumunu odullendir.
        if "for " in code_lowered or "while " in code_lowered:
            if any(tok in lowered for tok in loop_markers):
                score += 0.15
        if "if " in code_lowered and any(tok in lowered for tok in condition_markers):
            score += 0.1
        if chunk_type == "class" and class_marker in lowered:
            score += 0.05

        # Belirsiz ve dusuk bilgi tasiyan ifadeleri cezalandir.
        if any(marker in lowered for marker in vague_markers):
            score -= 0.25

        return max(0.0, min(1.0, round(score, 3)))
