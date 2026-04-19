import re
from typing import Optional

from .ai_client import AIExplainerClient


class CodeExplainer:
    def __init__(self, ai_client: Optional[AIExplainerClient] = None, output_lang: str = "en") -> None:
        """Aciklayiciyi, istege bagli AI destekli analiz istemcisiyle baslatir."""
        self.ai_client = ai_client
        self.output_lang = output_lang  # "tr" veya "en"

    def explain_code(
        self,
        code: str,
        name: str,
        language: str,
        chunk_type: str,
    ) -> tuple[str, Optional[str]]:
        """Once AI, olmazsa sezgisel yedekle aciklama ve karmasiklik dondurur."""
        # Ayarliysa once model tabanli analiz dener, basarisizsa deterministik kurallara duser.
        if self.ai_client:
            ai_result = self.ai_client.explain_code(code, name, language, chunk_type)
            if ai_result is not None:
                return ai_result

        action = self._infer_primary_action(code)
        structures = self._infer_data_structures(code)
        complexity = self._estimate_complexity(code)
        control_flow = self._infer_control_flow(code)

        if self.output_lang == "en":
            first_sentence = (
                f"This {chunk_type} '{name}' in {language} {action}."
                if chunk_type != "class"
                else f"This class '{name}' in {language} defines related behavior and state around {action}."
            )
            approach_bits = []
            if structures:
                approach_bits.append("It uses " + ", ".join(structures) + " to organize intermediate state")
            if control_flow:
                approach_bits.append(control_flow)
            if complexity:
                approach_bits.append(f"Estimated time complexity is {complexity}")
            if not approach_bits:
                approach_bits.append("It applies a direct step-by-step implementation with explicit control flow")
        else:
            action_tr = self._infer_primary_action_tr(code)
            first_sentence = (
                f"Bu {language} {chunk_type}'i '{name}', {action_tr}."
                if chunk_type != "class"
                else f"Bu '{name}' sinifi {language} dilinde {action_tr} etrafinda ilgili davranis ve durumu tanimlar."
            )
            approach_bits = []
            if structures:
                structures_tr = self._translate_structures(structures)
                approach_bits.append("Ara durumu organize etmek icin " + ", ".join(structures_tr) + " kullanir")
            if control_flow:
                approach_bits.append(self._infer_control_flow_tr(code))
            if complexity:
                approach_bits.append(f"Tahmini zaman karmasikligi: {complexity}")
            if not approach_bits:
                approach_bits.append("Acik kontrol akisiyla dogrudan adim adim bir uygulama sunar")

        explanation = first_sentence + " " + ". ".join(approach_bits) + "."
        return explanation, complexity

    def _infer_primary_action(self, code: str) -> str:
        """Sozcuk ipuclarindan kodun baskin islemini tahmin eder (Ingilizce)."""
        lowered = code.lower()
        action_rules = [
            ("sort",     "orders input data according to a comparison rule"),
            ("search",   "looks up target values within a collection"),
            ("parse",    "parses structured input into program data"),
            ("validate", "checks whether input satisfies required constraints"),
            ("merge",    "combines multiple inputs into a unified result"),
            ("token",    "processes text into token-level units"),
            ("graph",    "operates on graph-like relationships"),
            ("tree",     "traverses or transforms tree-structured data"),
            ("cache",    "stores and reuses previously computed values"),
            ("hash",     "uses hash-based lookup or identity mapping"),
            ("path",     "computes or validates path-oriented data"),
        ]
        for key, description in action_rules:
            if key in lowered:
                return description
        if "for " in lowered or "while " in lowered:
            return "iterates through input elements to compute a result"
        return "implements a focused unit of business or utility logic"

    def _infer_primary_action_tr(self, code: str) -> str:
        """Sozcuk ipuclarindan kodun baskin islemini tahmin eder (Turkce)."""
        lowered = code.lower()
        action_rules = [
            ("sort",     "giris verisini bir karsilastirma kuralina gore siralar"),
            ("search",   "koleksiyon icinde hedef degerleri arar"),
            ("parse",    "yapilandirilmis girisi program verisine donusturur"),
            ("validate", "girisin gerekli kisitlari karsilayip karsilamadigini kontrol eder"),
            ("merge",    "birden fazla girisi tek bir sonucta birlestir"),
            ("token",    "metni token duzeyinde birimlerle isler"),
            ("graph",    "graf benzeri iliskiler uzerinde islem yapar"),
            ("tree",     "agac yapisindaki veriyi gezer veya donusturur"),
            ("cache",    "onceden hesaplanan degerleri saklar ve yeniden kullanir"),
            ("hash",     "hash tabanli arama veya kimlik esleme kullanir"),
            ("path",     "yol odakli veriyi hesaplar veya dogrular"),
        ]
        for key, description in action_rules:
            if key in lowered:
                return description
        if "for " in lowered or "while " in lowered:
            return "sonuc hesaplamak icin giris ogelerini iter"
        return "odakli bir is veya yardimci mantik birimi uygular"

    def _infer_data_structures(self, code: str) -> list[str]:
        """Uygulamada kullanilan olasi veri yapilarini tahmin eder."""
        lowered = code.lower()
        structures = []
        if any(t in lowered for t in ["dict", "map<", "hashmap", "unordered_map", "object"]):
            structures.append("hash maps")
        if any(t in lowered for t in ["list", "array", "vector", "[]", "slice"]):
            structures.append("sequential collections")
        if any(t in lowered for t in ["set", "hashset", "unordered_set"]):
            structures.append("sets")
        if any(t in lowered for t in ["queue", "deque"]):
            structures.append("queues")
        if any(t in lowered for t in ["stack", "push", "pop"]):
            structures.append("stack-like operations")
        return structures

    def _translate_structures(self, structures: list[str]) -> list[str]:
        """Ingilizce veri yapisi adlarini Turkceye cevir."""
        mapping = {
            "hash maps": "hash tablolari",
            "sequential collections": "sirali koleksiyonlar",
            "sets": "kumeler",
            "queues": "kuyruklar",
            "stack-like operations": "yigin benzeri islemler",
        }
        return [mapping.get(s, s) for s in structures]

    def _infer_control_flow(self, code: str) -> Optional[str]:
        """Parcadaki temel kontrol akisi yapilarini ozetler (Ingilizce)."""
        lowered = code.lower()
        parts = []
        if "if " in lowered:
            parts.append("conditional branches")
        if "for " in lowered or "while " in lowered:
            parts.append("iterative loops")
        if "try" in lowered or "catch" in lowered or "except" in lowered:
            parts.append("error-handling paths")
        if "return" in lowered:
            parts.append("explicit return checkpoints")
        if not parts:
            return None
        return "The implementation relies on " + ", ".join(parts)

    def _infer_control_flow_tr(self, code: str) -> Optional[str]:
        """Parcadaki temel kontrol akisi yapilarini ozetler (Turkce)."""
        lowered = code.lower()
        parts = []
        if "if " in lowered:
            parts.append("kosullu dallar")
        if "for " in lowered or "while " in lowered:
            parts.append("donguler")
        if "try" in lowered or "catch" in lowered or "except" in lowered:
            parts.append("hata yonetim bloklari")
        if "return" in lowered:
            parts.append("acik donus noktalari")
        if not parts:
            return None
        return "Uygulama su yapilara dayanir: " + ", ".join(parts)

    def _estimate_complexity(self, code: str) -> Optional[str]:
        """Basit yapi kaliplarindan zaman karmasikligini tahmin eder."""
        lowered = code.lower()

        nested_loop_patterns = [
            r"for .*:\n\s+for ",
            r"while .*:\n\s+for ",
            r"for .*\{\s*\n\s*for ",
            r"while .*\{\s*\n\s*while ",
        ]
        if any(re.search(pattern, lowered, flags=re.DOTALL) for pattern in nested_loop_patterns):
            return "O(n^2) in the common case"

        if "sort(" in lowered or ".sort(" in lowered:
            return "O(n log n)"

        if "for " in lowered or "while " in lowered:
            if "for " in lowered and "if " in lowered and "break" not in lowered:
                return "O(n)"
            return "O(n) for a single pass over input"

        if any(token in lowered for token in ["dict", "map", "hash"]):
            return "O(1) average-time lookups for key operations"

        return None
