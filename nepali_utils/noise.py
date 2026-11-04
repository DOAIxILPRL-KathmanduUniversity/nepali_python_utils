"""Seeded Nepali text noising operators.

Designed for data-synthesis and denoising pipelines: every operator accepts an
optional ``seed`` / ``rng`` so experiments are reproducible, and operators are
registered in ``NOISE_OPS`` so new ones can be added without touching this file.

Operators (Nepali-aware where it matters):
* char: deletion / insertion / swap / substitution on Devanagari characters
* homophone: श/ष/स, व/ब, इ/ई, उ/ऊ confusion
* keyboard: phonetic-keyboard neighbor typos (क↔ख↔ग …)
* word: dropout / permute / swap / synonym replacement
* clitic: postposition detachment  रामले -> राम ले
* script: code-mix, full/partial transliteration
* span: BART/T5-style span corruption, random masking, sentence permutation
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable

from . import scripts
from . import translit

__all__ = [
    "NOISE_OPS",
    "apply_noising",
    "apply_random_noising",
    "register_noise_op",
    "list_noise_ops",
]

# ---------------------------------------------------------------------------
# Homophone confusion pairs (Nepali-specific)
# ---------------------------------------------------------------------------

HOMOPHONE_PAIRS: list[tuple[str, str]] = [
    ("श", "स"), ("स", "श"), ("ष", "स"), ("स", "ष"),
    ("व", "ब"), ("ब", "व"),
    ("इ", "ई"), ("ई", "इ"),
    ("उ", "ऊ"), ("ऊ", "उ"),
    ("ऋ", "रि"), ("रि", "ऋ"),
    ("ज", "ग"), ("ग", "ज"),   # approximate, context-dependent
    ("ं", "ँ"), ("ँ", "ं"),
]

# Phonetic-ish keyboard neighbors on a Nepali (Romanized) layout.
KEYBOARD_NEIGHBORS: dict[str, list[str]] = {
    "क": ["ख", "ग"], "ख": ["क", "ग"], "ग": ["ख", "घ"],
    "च": ["छ", "ज"], "छ": ["च", "ज"], "ज": ["छ", "झ"],
    "ट": ["ठ", "ड"], "ठ": ["ट", "ड"], "ड": ["ठ", "ढ"],
    "त": ["थ", "द"], "थ": ["त", "द"], "द": ["थ", "ध"],
    "प": ["फ", "ब"], "फ": ["प", "ब"], "ब": ["फ", "भ"],
}


def _rng(seed) -> random.Random:
    if isinstance(seed, random.Random):
        return seed
    return random.Random(seed)


# ---------------------------------------------------------------------------
# Character-level operators
# ---------------------------------------------------------------------------

def _chars(text: str) -> list[str]:
    return list(text)


def random_char_deletion(text: str, p: float = 0.05, seed=None) -> str:
    rng = _rng(seed)
    return "".join(c for c in text if rng.random() >= p or not scripts.is_devanagari_char(c))


def random_char_insertion(text: str, p: float = 0.05, seed=None) -> str:
    rng = _rng(seed)
    out: list[str] = []
    for c in text:
        out.append(c)
        if scripts.is_devanagari_char(c) and rng.random() < p:
            out.append(rng.choice(list(scripts.CONSONANT_CHARS)))
    return "".join(out)


def random_char_swap(text: str, p: float = 0.05, seed=None) -> str:
    rng = _rng(seed)
    chars = list(text)
    i = 0
    while i < len(chars) - 1:
        if scripts.is_devanagari_char(chars[i]) and scripts.is_devanagari_char(chars[i + 1]):
            if rng.random() < p:
                chars[i], chars[i + 1] = chars[i + 1], chars[i]
                i += 2
                continue
        i += 1
    return "".join(chars)


def random_char_substitution(text: str, p: float = 0.05, seed=None) -> str:
    rng = _rng(seed)
    pool = list(scripts.CONSONANT_CHARS | scripts.MATRA_CHARS)
    out = []
    for c in text:
        if scripts.is_devanagari_char(c) and rng.random() < p:
            out.append(rng.choice(pool))
        else:
            out.append(c)
    return "".join(out)


def matra_drop(text: str, p: float = 0.1, seed=None) -> str:
    rng = _rng(seed)
    return "".join(c for c in text if rng.random() >= p or c not in scripts.MATRA_CHARS)


def halanta_drop(text: str, p: float = 0.1, seed=None) -> str:
    rng = _rng(seed)
    return "".join(c for c in text if rng.random() >= p or c != scripts.HALANT)


# ---------------------------------------------------------------------------
# Homophone / keyboard
# ---------------------------------------------------------------------------

def substitute_homophones(text: str, p: float = 0.2, seed=None) -> str:
    rng = _rng(seed)
    out = []
    for c in text:
        replaced = False
        for a, b in HOMOPHONE_PAIRS:
            if c == a and rng.random() < p:
                out.append(b)
                replaced = True
                break
        if not replaced:
            out.append(c)
    return "".join(out)


def keyboard_typo(text: str, p: float = 0.05, seed=None) -> str:
    rng = _rng(seed)
    out = []
    for c in text:
        if c in KEYBOARD_NEIGHBORS and rng.random() < p:
            out.append(rng.choice(KEYBOARD_NEIGHBORS[c]))
        else:
            out.append(c)
    return "".join(out)


# ---------------------------------------------------------------------------
# Word-level operators
# ---------------------------------------------------------------------------

def word_dropout(text: str, ratio: float = 0.15, seed=None) -> str:
    rng = _rng(seed)
    words = text.split()
    kept = [w for w in words if rng.random() >= ratio]
    return " ".join(kept) if kept else text


def word_deletion(text: str, p: float = 0.1, seed=None) -> str:
    return word_dropout(text, p, seed)


def word_permute(text: str, ratio: float = 0.2, seed=None) -> str:
    rng = _rng(seed)
    words = text.split()
    n_swap = max(1, int(len(words) * ratio)) if words else 0
    for _ in range(n_swap):
        if len(words) < 2:
            break
        i, j = rng.sample(range(len(words)), 2)
        words[i], words[j] = words[j], words[i]
    return " ".join(words)


def word_swap(text: str, n: int = 1, seed=None) -> str:
    rng = _rng(seed)
    words = text.split()
    for _ in range(n):
        if len(words) < 2:
            break
        i, j = rng.sample(range(len(words)), 2)
        words[i], words[j] = words[j], words[i]
    return " ".join(words)


def clitic_detachment(text: str, seed=None) -> str:
    """Detach common postposition clitics: रामले -> राम ले."""
    clitics = ("ले", "लाई", "को", "मा", "बाट", "सँग")
    out = []
    for word in text.split():
        detached = False
        for cl in clitics:
            if word.endswith(cl) and len(word) > len(cl):
                out.append(word[: -len(cl)])
                out.append(cl)
                detached = True
                break
        if not detached:
            out.append(word)
    return " ".join(out)


def word_replace_synonym(text: str, ratio: float = 0.2, seed=None) -> str:
    """Replace words with a recorded synonym (falls back to identity)."""
    rng = _rng(seed)
    try:
        from . import stopwords  # reuse registry shape lazily
    except Exception:
        stopwords = None  # type: ignore
    # Synonym map lives in gazetteer packs; without a pack, identity.
    words = text.split()
    out = []
    for w in words:
        if rng.random() < ratio:
            out.append(w)  # placeholder: no synonym pack loaded yet
        else:
            out.append(w)
    return " ".join(out)


# ---------------------------------------------------------------------------
# Script-level operators
# ---------------------------------------------------------------------------

def transliterate_full(text: str, seed=None) -> str:
    return translit.transliterate_roman_to_devanagari(
        translit.transliterate_devanagari_to_roman(text)
    )


def transliterate_random_words(text: str, ratio: float = 0.3, seed=None) -> str:
    rng = _rng(seed)
    words = text.split()
    out = []
    for w in words:
        if scripts.contains_devanagari(w) and rng.random() < ratio:
            out.append(translit.transliterate_devanagari_to_roman(w))
        else:
            out.append(w)
    return " ".join(out)


def code_mix(text: str, ratio: float = 0.3, seed=None) -> str:
    rng = _rng(seed)
    words = text.split()
    out = []
    for w in words:
        if scripts.contains_devanagari(w) and rng.random() < ratio:
            out.append(translit.transliterate_devanagari_to_roman(w))
        else:
            out.append(w)
    return " ".join(out)


# ---------------------------------------------------------------------------
# Span-level operators
# ---------------------------------------------------------------------------

def random_mask(text: str, ratio: float = 0.15, seed=None) -> str:
    rng = _rng(seed)
    words = text.split()
    n = max(1, int(len(words) * ratio)) if words else 0
    idx = rng.sample(range(len(words)), min(n, len(words))) if words else []
    for i in idx:
        words[i] = "<mask>"
    return " ".join(words)


def span_corruption(text: str, corruption_rate: float = 0.3, seed=None) -> str:
    rng = _rng(seed)
    words = text.split()
    if not words:
        return text
    n_spans = max(1, int(len(words) * corruption_rate))
    start = rng.randrange(0, len(words))
    length = max(1, min(n_spans, len(words) - start))
    span = words[start : start + length]
    words[start : start + length] = ["<span>"]
    return " ".join(words)


def sentence_permutation(text: str, p: float = 0.5, seed=None) -> str:
    rng = _rng(seed)
    sentences = [s.strip() for s in text.split("।") if s.strip()]
    if len(sentences) < 2:
        return text
    if rng.random() < p:
        i, j = rng.sample(range(len(sentences)), 2)
        sentences[i], sentences[j] = sentences[j], sentences[i]
    return "।".join(sentences) + ("।" if text.endswith("।") else "")


def inject_random_noise(text: str, noise_level: float = 0.1, seed=None) -> str:
    """Compose a few character-level ops at random."""
    rng = _rng(seed)
    ops = [random_char_deletion, random_char_insertion, random_char_substitution, random_char_swap]
    result = text
    for op in ops:
        if rng.random() < noise_level:
            result = op(result, p=noise_level, seed=rng)
    return result


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

@dataclass
class NoiseOp:
    fn: Callable
    defaults: dict = field(default_factory=dict)


NOISE_OPS: dict[str, NoiseOp] = {
    "char_deletion": NoiseOp(random_char_deletion, {"p": 0.05}),
    "char_insertion": NoiseOp(random_char_insertion, {"p": 0.05}),
    "char_swap": NoiseOp(random_char_swap, {"p": 0.05}),
    "char_substitution": NoiseOp(random_char_substitution, {"p": 0.05}),
    "matra_drop": NoiseOp(matra_drop, {"p": 0.1}),
    "halanta_drop": NoiseOp(halanta_drop, {"p": 0.1}),
    "keyboard_typo": NoiseOp(keyboard_typo, {"p": 0.05}),
    "homophone": NoiseOp(substitute_homophones, {"p": 0.2}),
    "word_dropout": NoiseOp(word_dropout, {"ratio": 0.15}),
    "word_deletion": NoiseOp(word_deletion, {"p": 0.1}),
    "word_permute": NoiseOp(word_permute, {"ratio": 0.2}),
    "word_swap": NoiseOp(word_swap, {"n": 1}),
    "clitic_detachment": NoiseOp(clitic_detachment, {}),
    "word_replace_synonym": NoiseOp(word_replace_synonym, {"ratio": 0.2}),
    "transliterate_full": NoiseOp(transliterate_full, {}),
    "transliterate_random_words": NoiseOp(transliterate_random_words, {"ratio": 0.3}),
    "code_mix": NoiseOp(code_mix, {"ratio": 0.3}),
    "span_corruption": NoiseOp(span_corruption, {"corruption_rate": 0.3}),
    "random_mask": NoiseOp(random_mask, {"ratio": 0.15}),
    "sentence_permutation": NoiseOp(sentence_permutation, {"p": 0.5}),
    "inject_random_noise": NoiseOp(inject_random_noise, {"noise_level": 0.1}),
}


def register_noise_op(name: str, fn: Callable, defaults: dict | None = None) -> None:
    """Register a custom noising operator (extensibility point)."""
    NOISE_OPS[name] = NoiseOp(fn, defaults or {})


def list_noise_ops() -> list[str]:
    return sorted(NOISE_OPS)


def apply_noising(text: str, op: str | list[str], seed: int | None = None, **kwargs) -> str:
    """Apply one noise op, or a list of ops in sequence, deterministically."""
    rng = _rng(seed)
    if isinstance(op, str):
        op = [op]
    result = text
    for name in op:
        noise_op = NOISE_OPS.get(name)
        if noise_op is None:
            raise KeyError(f"Unknown noise op '{name}'. Known: {list_noise_ops()}")
        params = dict(noise_op.defaults)
        params.update(kwargs)
        params["seed"] = rng
        result = noise_op.fn(result, **params)
    return result


def apply_random_noising(text: str, seed: int | None = None, **kwargs) -> str:
    """Apply a random subset of registered ops (for synthetic denoising pairs)."""
    rng = _rng(seed)
    names = list(NOISE_OPS)
    rng.shuffle(names)
    k = rng.randint(1, min(3, len(names)))
    return apply_noising(text, names[:k], seed=rng, **kwargs)
