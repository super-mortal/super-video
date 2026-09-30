"""Shared text segmentation utilities for narration subtitle units.

Provides character classification patterns (CJK, Latin) and the sentence
punctuation set, plus a `tokenize` function that splits a line of narration
text into subtitle units of roughly `chars_per_unit` CJK characters,
breaking on spaces and sentence punctuation.
"""
from __future__ import annotations

import re

CJK_RE = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]')
LATIN_RE = re.compile(r'[A-Za-z0-9]')
SENTENCE_PUNCT = set("。！？，；：、…—")


def tokenize(text: str, chars_per_unit: int = 4) -> list[str]:
    """Split text into subtitle units of about `chars_per_unit` CJK chars.

    Spaces and sentence punctuation force a break; consecutive Latin
    alphanumerics are kept as one unit.
    """
    atoms: list[tuple[str, str]] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in (" ", "\u3000"):
            atoms.append(("space", ""))
            i += 1
        elif ch in SENTENCE_PUNCT:
            atoms.append(("punct", ch))
            i += 1
        elif LATIN_RE.match(ch):
            j = i
            while j < len(text) and LATIN_RE.match(text[j]):
                j += 1
            atoms.append(("latin", text[i:j]))
            i = j
        else:
            atoms.append(("cjk", ch))
            i += 1
    tokens: list[str] = []
    cur = ""
    for kind, val in atoms:
        if kind == "space":
            if cur:
                tokens.append(cur)
                cur = ""
            continue
        if kind == "punct":
            cur += val
            if cur:
                tokens.append(cur)
                cur = ""
            continue
        cur += val
        if len(CJK_RE.findall(cur)) >= chars_per_unit:
            tokens.append(cur)
            cur = ""
    if cur:
        tokens.append(cur)
    return tokens
