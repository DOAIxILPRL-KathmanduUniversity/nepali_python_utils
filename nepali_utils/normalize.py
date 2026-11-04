"""Unicode-hygiene normalization for Nepali Devanagari text.

Deterministic, stdlib-only, offline-safe. Every function below is unambiguous
orthographic cleanup (no linguistic guesswork):

* NFC composition
* zero-width / bidi / soft-hyphen artifact removal
* whitespace + blank-line collapsing
* danda canonicalization (ASCII bar |  ->  ।, multiple danda variants)
* smart-quote / dash folding
* Devanagari vs ASCII digit folding (optional)

These are safe to apply to any Nepali text pipeline before linguistic modules run.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "ZERO_WIDTH_CHARS",
    "remove_zero_width",
    "collapse_whitespace",
    "normalize_danda",
    "fold_smart_punctuation",
    "to_nfc",
    "fold_digits",
    "normalize_nepali_text",
    "devanagari_ratio",
]

ZERO_WIDTH_CHARS = frozenset("\u200b\u200c\u200d\u200e\u200f\ufeff\u00ad")

_WS_RE = re.compile(r"[ \t\u00a0]+")
_NEWLINE_RE = re.compile(r"\n{3,}")
_DANDA_RE = re.compile(r"[।॥|¦¦]+")


def remove_zero_width(text: str) -> str:
    """Remove zero-width / bidi / soft-hyphen artifacts."""
    if not text:
        return text
    return "".join(ch for ch in text if ch not in ZERO_WIDTH_CHARS)


def collapse_whitespace(text: str) -> str:
    """Collapse runs of spaces/tabs/NBSP to one; limit blank lines; trim."""
    text = _WS_RE.sub(" ", text)
    text = _NEWLINE_RE.sub("\n\n", text)
    return text.strip()


def normalize_danda(text: str) -> str:
    """Canonicalize end-of-sentence punctuation to Devanagari danda (।).

    ASCII bar, single/double danda variants all fold to ।.  Multiple dandas
    collapse to one.
    """
    return _DANDA_RE.sub("।", text)


def fold_smart_punctuation(text: str) -> str:
    """Fold curly quotes/dashes/ellipsis to plain ASCII equivalents."""
    mapping = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-", "\u2026": "...",
    }
    return "".join(mapping.get(ch, ch) for ch in text)


def to_nfc(text: str) -> str:
    """Unicode NFC composition."""
    return unicodedata.normalize("NFC", text)


_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def fold_digits(text: str, to_ascii: bool = True) -> str:
    """Fold Devanagari digits to ASCII digits (or back)."""
    if to_ascii:
        return text.translate(_DEVANAGARI_DIGITS)
    _ASCII_TO_DEVA = str.maketrans("0123456789", "०१२३४५६७८९")
    return text.translate(_ASCII_TO_DEVA)


def devanagari_ratio(text: str) -> float:
    """Fraction of characters in the Devanagari block (U+0900–U+097F)."""
    if not text:
        return 0.0
    devanagari = sum(1 for ch in text if "\u0900" <= ch <= "\u097f")
    return devanagari / len(text)


def normalize_nepali_text(
    text: str,
    *,
    nfc: bool = True,
    zero_width: bool = True,
    whitespace: bool = True,
    danda: bool = True,
    smart_punct: bool = True,
    digits_to_ascii: bool = False,
) -> str:
    """Canonical Nepali text normalization (all unambiguous fixes only).

    Parameters are independent so pipelines can pick the subset they need.
    """
    if not isinstance(text, str):
        text = str(text)
    if nfc:
        text = to_nfc(text)
    if zero_width:
        text = remove_zero_width(text)
    if smart_punct:
        text = fold_smart_punctuation(text)
    if whitespace:
        text = collapse_whitespace(text)
    if danda:
        text = normalize_danda(text)
    if digits_to_ascii:
        text = fold_digits(text, to_ascii=True)
    return text
