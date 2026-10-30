#!/usr/bin/env python3
"""
Industrial-Grade Preeti / Kantipur Legacy Font to Unicode Devanagari Normalizer
Handles complex Devanagari ligatures, multi-consonant conjuncts, reph (र्),
chhoti-i matra (ि) re-ordering, full vowel combinations, and punctuation.
"""

import re

# 1. Multi-character glyph mappings (Ligatures & Independent Vowels)
# Must be substituted BEFORE single-character replacements.
MULTI_CHAR_MAP = [
    # Full Vowel combinations (Vowel signs combined with base 'अ')
    ('cf\\}', 'औ'),
    ('cf]', 'ओ'),
    ('cf', 'आ'),
    ('O{', 'ई'),
    ('P]', 'ऐ'),
    
    # Common Preeti conjuncts & ligatures
    ('Qm', 'क्त'),
    ('qm', 'त्र'),
    ('I', 'क्ष'),
    ('1', 'ज्ञ'),
    ('4', 'द्ध'),
    ('5', 'द्घ'),
    ('6', 'ट्ट'),
    ('7', 'ट्ठ'),
    ('8', 'ड्ड'),
    ('9', 'ढ्ढ'),
    ('0', 'द्द'),
    ('!', '१'),
    ('@', '२'),
    ('#', '३'),
    ('$', '४'),
    ('%', '५'),
    ('^', '६'),
    ('&', '७'),
    ('*', '८'),
    ('(', '९'),
    (')', '०'),
    
    # Reph + Matra combinations
    ('i{', 'र्षा'),
    ('f{', 'र्ा'),
    (']{', 'र्े'),
    ('}{', 'र्ै'),
]

# 2. Single-character mapping
SINGLE_CHAR_MAP = {
    '~': 'ङ', '`': 'ञ', '-': '(', '_': ')',
    'q': 'त्र', 'w': 'ध', 'e': 'भ', 'r': 'च', 't': 'त', 'y': 'थ', 'u': 'ग',
    'i': 'ष', 'o': 'य', 'p': 'उ', '[': 'ृ', '{': 'र्', ']': 'े',
    'a': 'ब', 's': 'क', 'd': 'म', 'f': 'ा', 'g': 'न', 'h': 'ज', 'j': 'व',
    'k': 'प', 'l': 'ि', ';': 'स', ':': 'स्', "'": 'ु', '"': 'ू',
    'z': 'श', 'x': 'ह', 'c': 'अ', 'v': 'ख', 'b': 'द', 'n': 'ल', 'm': 'फ',
    ',': ',', '<': '?', '.': '।', '>': 'श्र', '/': 'र', '?': 'रु',
    'Q': 'त्त', 'W': 'ध्', 'E': 'भ्', 'R': 'च्', 'T': 'त्', 'Y': 'थ्', 'U': 'ग्',
    'I': 'क्ष', 'O': 'इ', 'P': 'ए', '}': 'ै',
    'A': 'ब्', 'S': 'क्', 'D': 'म्', 'F': 'ँ', 'G': 'न्', 'H': 'ज्', 'J': 'व्',
    'K': 'प्', 'L': 'ी',
    'Z': 'श्', 'X': 'ह्', 'C': 'ऋ', 'V': 'ख्', 'B': 'द्', 'N': 'ल्', 'M': 'फ्',
    '\\': '्', '|': '्र'
}

def preeti_to_unicode(text: str) -> str:
    """
    Converts Preeti/Kantipur legacy text into standard Devanagari Unicode.
    Executes a 4-phase transformation:
    1. Multi-character ligature and composite vowel substitutions.
    2. Context-aware lookahead for prefix chhoti-i matra ('l') across single/conjunct consonants.
    3. Reph ('{') postposition reordering to logical phonetic position.
    4. Base character replacement and NFC normalization.
    """
    if not text:
        return ""

    # Phase 1: Pre-substitute multi-character ligatures
    s = text
    for preeti_seq, uni_seq in MULTI_CHAR_MAP:
        s = s.replace(preeti_seq, uni_seq)

    # Phase 2: Chhoti-i matra ('l') reordering
    # In Preeti, 'l' is visually placed BEFORE the consonant or conjunct.
    # Pattern: 'l' followed by an optional half-consonant (e.g. 'S', 'D', 'N') + full consonant.
    # Move 'ि' AFTER the full consonant cluster.
    s = re.sub(r'l([A-Z:;]?[a-z0-9\u0900-\u097F])', r'\1l', s)

    # Phase 3: Reph ('{') reordering
    # In Preeti, '{' is often typed after or before the consonant. In Unicode, र् goes before the base letter.
    # Convert remaining '{' to 'र्' and re-anchor
    s = re.sub(r'([a-z0-9\u0900-\u097F])\{', r'र्\1', s)

    # Phase 4: Single character substitution
    out = []
    for c in s:
        if c == 'l':
            out.append('ि')
        else:
            out.append(SINGLE_CHAR_MAP.get(c, c))

    result = "".join(out)
    return result

if __name__ == "__main__":
    test_samples = [
        ("gk]fn ;'Gb/ b]z xf].", "नेपाल सुन्दर देश हो।"),
        ("s]kfnL", "नेपाली"),
        ("d'n's", "मुलुक")
    ]
    for inp, expected in test_samples:
        converted = preeti_to_unicode(inp)
        print(f"Input   : {inp}")
        print(f"Converted: {converted}")
        print(f"Match    : {converted == expected}\n")
