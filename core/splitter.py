"""Indic-aware and Latin sentence boundary splitter.

Splits multi-sentence text into individual sentences while respecting:
- Standard punctuation: '.', '?', '!'
- Indic Danda and Double Danda: '।', '॥'
- Common abbreviations (Dr., Mr., Rs., e.g., i.e., etc.)
- Numbers (e.g., 3.14, 10,000.00)
- Preserves structure for reconstructive batch translation.
"""

import re
from typing import List

# Common abbreviations to avoid false splits
ABBREVIATIONS = (
    r"(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|St|vs|etc|eg|ie|vol|dept|approx|govt|pvt|ltd|co)"
)

# Regex pattern protecting abbreviations and initials
_ABBR_PATTERN = re.compile(rf"\b{ABBREVIATIONS}\.", re.IGNORECASE)
_NUM_PATTERN = re.compile(r"\b\d+\.\d+\b")
_INITIAL_PATTERN = re.compile(r"\b[A-Za-z]\.")

# Indic and Latin end-of-sentence delimiters
_PUNCT_SPLIT = re.compile(r"([.?!।॥]+(?:\s+|\n+|$))")


def split_sentences(text: str) -> List[str]:
    """Split text into sentences, handling Indic danda and Western punctuation."""
    if not text or not text.strip():
        return []

    text = text.strip()

    # If short or no terminal punctuation, return as single chunk
    if len(text) < 120 and not any(p in text for p in [".", "?", "!", "।", "॥", "\n"]):
        return [text]

    # Temporarily mask periods in numbers and known abbreviations
    masked = text
    matches = []

    def mask_match(m):
        matches.append(m.group(0))
        return f"__MASK_{len(matches) - 1}__"

    masked = _NUM_PATTERN.sub(mask_match, masked)
    masked = _ABBR_PATTERN.sub(mask_match, masked)
    masked = _INITIAL_PATTERN.sub(mask_match, masked)

    # Split on terminal delimiters or explicit newlines
    raw_parts = re.split(r"(?<=[.?!।॥\n])\s+", masked)

    # Unmask and clean
    sentences = []
    for part in raw_parts:
        part = part.strip()
        if not part:
            continue
        # Unmask
        for i, original in enumerate(matches):
            part = part.replace(f"__MASK_{i}__", original)
        part = part.strip()
        if part:
            sentences.append(part)

    # Fallback if splitting produced nothing
    if not sentences and text:
        return [text]

    return sentences


if __name__ == "__main__":
    test_text = (
        "ನಮಸ್ಕಾರ, ನೀವು ಹೇಗಿದ್ದೀರಿ? ನಾನು ಆರಾಮಾಗಿದ್ದೇನೆ. "
        "यह एक परीक्षण वाक्य है। हम ऑफ़लाइन अनुवाद कर रहे हैं! "
        "Dr. Sharma paid Rs. 500.50 at the store."
    )
    res = split_sentences(test_text)
    for i, s in enumerate(res):
        print(f"[{i+1}] {s}")
