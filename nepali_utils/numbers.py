"""Nepali number utilities.

* Devanagari <-> ASCII digit folding
* Integer -> Nepali words (एक, दस, सय, हजार, लाख, करोड)
* Nepali month names (Bikram Sambat calendar)

The integer-to-words table is self-contained and small; full BS<->AD calendar
conversion is intentionally *not* reimplemented here — the mature `nepali`
PyPI package already owns that (endorsed, not forked).
"""

from __future__ import annotations

__all__ = [
    "DIGITS_DEVANAGARI", "DIGITS_ASCII",
    "to_devanagari_digits", "to_ascii_digits",
    "int_to_nepali_words", "nepali_months",
]

DIGITS_DEVANAGARI = "०१२३४५६७८९"
DIGITS_ASCII = "0123456789"

_TO_DEVA = str.maketrans(DIGITS_ASCII, DIGITS_DEVANAGARI)
_TO_ASCII = str.maketrans(DIGITS_DEVANAGARI, DIGITS_ASCII)


def to_devanagari_digits(text: str) -> str:
    return text.translate(_TO_DEVA)


def to_ascii_digits(text: str) -> str:
    return text.translate(_TO_ASCII)


_UNITS = [
    "", "एक", "दुई", "तीन", "चार", "पाँच", "छ", "सात", "आठ", "नौ",
]
_TEENS = ["दस", "एघार", "बार", "तेह्र", "चौध", "पन्ध्र", "सोह्र", "सत्र", "अठार", "उन्नाइस"]
_TENS = ["", "", "बीस", "तिस", "चौबिस", "पचास", "साठी", "सत्तरी", "आसी", "नब्बे"]


def _below_thousand(n: int) -> str:
    if n == 0:
        return ""
    if n < 10:
        return _UNITS[n]
    if n < 20:
        return _TEENS[n - 10]
    if n < 100:
        ten, unit = divmod(n, 10)
        return _TENS[ten] + ((" " + _UNITS[unit]) if unit else "")
    hundred, rest = divmod(n, 100)
    return _UNITS[hundred] + " सय" + ((" " + _below_thousand(rest)) if rest else "")


def int_to_nepali_words(n: int) -> str:
    """Convert a non-negative integer to Nepali words.

    Uses the लाख / करोड grouping (Nepali numbering convention).
    """
    if n < 0:
        raise ValueError("negative numbers are not supported")
    if n == 0:
        return "शून्य"

    parts: list[str] = []
    # करोड (10^7)
    if n >= 10_000_000:
        crore, n = divmod(n, 10_000_000)
        parts.append(_below_thousand(crore).strip() + " करोड")
    # लाख (10^5)
    if n >= 100_000:
        lakh, n = divmod(n, 100_000)
        parts.append(_below_thousand(lakh).strip() + " लाख")
    # हजार (10^3)
    if n >= 1000:
        hajar, n = divmod(n, 1000)
        parts.append(_below_thousand(hajar).strip() + " हजार")
    if n > 0:
        parts.append(_below_thousand(n).strip())
    return " ".join(p for p in parts if p).strip()


def nepali_months() -> list[str]:
    """Bikram Sambat month names in order (बैशाख … चैत्र)."""
    return [
        "बैशाख", "जेठ", "असार", "श्रावण", "भाद्र", "आश्विन",
        "कार्तिक", "मंसिर", "पौष", "माघ", "फाल्गुन", "चैत्र",
    ]
