"""Unicode Script Pre-Router & Language Detection.

Detects Indic scripts deterministically in microseconds via Unicode ranges.
Uses FastText (or stopword heuristics) only for Latin disambiguation (English vs Spanish/French).
"""

import os
import re
from typing import Optional, Tuple

# Mapping from simple language codes to NLLB-200 language tokens
NLLB_LANG_CODES = {
    "kn": "kan_Knda",  # Kannada
    "hi": "hin_Deva",  # Hindi
    "ta": "tam_Taml",  # Tamil
    "te": "tel_Telu",  # Telugu
    "ml": "mal_Mlym",  # Malayalam
    "en": "eng_Latn",  # English
    "es": "spa_Latn",  # Spanish
    "fr": "fra_Latn",  # French
}

LANG_DISPLAY_NAMES = {
    "kn": "Kannada (ಕನ್ನಡ)",
    "hi": "Hindi (हिन्दी)",
    "ta": "Tamil (தமிழ்)",
    "te": "Telugu (తెలుగు)",
    "ml": "Malayalam (മലയാളം)",
    "en": "English",
    "es": "Spanish (Español)",
    "fr": "French (Français)",
}

# Unicode Ranges for Indic Scripts
SCRIPT_RANGES = {
    "kn": re.compile(r"[\u0C80-\u0CFF]"),  # Kannada
    "hi": re.compile(r"[\u0900-\u097F]"),  # Devanagari (Hindi)
    "ta": re.compile(r"[\u0B80-\u0BFF]"),  # Tamil
    "te": re.compile(r"[\u0C00-\u0C7F]"),  # Telugu
    "ml": re.compile(r"[\u0D00-\u0D7F]"),  # Malayalam
}

LATIN_RANGE = re.compile(r"[A-Za-z\u00C0-\u024F]")

# Common Spanish stopwords for ultra-fast, zero-dependency Latin disambiguation
SPANISH_MARKERS = {
    "el", "la", "de", "que", "y", "en", "un", "una", "los", "las", "del", "se", "por",
    "con", "para", "como", "estar", "tener", "pero", "más", "este", "esta", "hola",
    "gracias", "buenos", "días", "por favor", "¿", "¡", "ñ", "á", "é", "í", "ó", "ú"
}

# Common French markers
FRENCH_MARKERS = {
    "le", "la", "les", "de", "et", "en", "un", "une", "des", "du", "qui", "dans",
    "pour", "avec", "sur", "mais", "ce", "cette", "bonjour", "merci", "est", "sont",
    "à", "è", "ê", "ç", "œ"
}

_fasttext_model = None


def _load_fasttext():
    global _fasttext_model
    if _fasttext_model is not None:
        return _fasttext_model

    model_path = os.path.join(os.path.dirname(__file__), "..", "models", "lid.176.ftz")
    if os.path.exists(model_path):
        try:
            import fasttext
            # Silence fasttext warnings
            fasttext.FastText.eprint = lambda x: None
            _fasttext_model = fasttext.load_model(model_path)
            return _fasttext_model
        except Exception:
            pass
    return None


def detect_language(text: str) -> Tuple[str, float]:
    """Detect language of input text.
    
    Returns (lang_code, confidence).
    Priority:
    1. Deterministic Unicode range check for Indic scripts.
    2. Latin disambiguation (FastText or token-based heuristic for EN vs ES/FR).
    """
    if not text or not text.strip():
        return "en", 0.0

    # Count character frequency per script
    counts = {lang: len(pattern.findall(text)) for lang, pattern in SCRIPT_RANGES.items()}
    total_indic = sum(counts.values())

    if total_indic > 0:
        # Determine dominant Indic script
        dominant_lang = max(counts, key=counts.get)
        confidence = counts[dominant_lang] / max(1, total_indic)
        return dominant_lang, min(1.0, confidence)

    # Check for Latin characters
    latin_matches = len(LATIN_RANGE.findall(text))
    if latin_matches > 0:
        # Try FastText if available
        ft = _load_fasttext()
        if ft:
            try:
                preds = ft.predict(text.replace("\n", " "), k=3)
                labels = [l.replace("__label__", "") for l in preds[0]]
                scores = preds[1]
                for l, s in zip(labels, scores):
                    if l in ["en", "es", "fr"]:
                        return l, float(s)
            except Exception:
                pass

        # Fast heuristic fallback for Latin script
        words = set(re.findall(r"\w+", text.lower()))
        spanish_hits = len(words.intersection(SPANISH_MARKERS)) or any(c in text for c in "¿¡ñáéíóú")
        french_hits = len(words.intersection(FRENCH_MARKERS)) or any(c in text for c in "àèêçœ")

        if spanish_hits > 0 and spanish_hits >= french_hits:
            return "es", 0.90
        elif french_hits > 0:
            return "fr", 0.90
        else:
            return "en", 0.95

    return "en", 0.50


def is_romanized_indic(text: str, target_indic_lang: str) -> bool:
    """Detect if user is typing Romanized transliteration (e.g. 'namaskara' with Kannada target)."""
    if not text or not target_indic_lang:
        return False
    # If text is purely Latin letters but user selected an Indic language as source
    has_indic = any(bool(p.search(text)) for p in SCRIPT_RANGES.values())
    has_latin = bool(LATIN_RANGE.search(text))
    return has_latin and not has_indic and target_indic_lang in SCRIPT_RANGES


def get_nllb_code(code: str) -> str:
    """Convert 2-letter ISO code to NLLB-200 code token."""
    return NLLB_LANG_CODES.get(code.lower(), "eng_Latn")
