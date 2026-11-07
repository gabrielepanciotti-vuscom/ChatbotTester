from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .types import Beat, Reply


@dataclass(frozen=True)
class Phrasebook:
    """Words the deterministic player says/understands; override per language in the suite file."""

    yes: str = "Yes"
    no: str = "No"
    yes_values: tuple[str, ...] = ("yes", "y")
    code_words: tuple[str, ...] = ("code", "otp", "pin")


def fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().lower()


def answer(
    beat: Beat, last: Reply, codes: list[dict], book: Phrasebook | None = None
) -> str | None:
    """The customer's line for a reactive beat, or None when no deterministic rule applies."""
    book = book or Phrasebook()
    text = "\n".join(last.messages)
    if beat.wait == "verification_code":
        words = "|".join(re.escape(w) for w in book.code_words)
        if not re.search(rf"\b({words})\b", text, re.I) or not codes:
            return None
        return str(codes[-1]["code"])
    if beat.wait == "menu":
        target = fold(beat.value or "")
        for o in last.options:
            if fold(o) == target:
                return o
        for line in text.splitlines():
            m = re.match(r"\s*(\d+)[\.\)]\s*(.+)", line)
            if m and target and target in fold(m.group(2)):
                return m.group(1)
        return None
    if beat.wait == "yes_no":
        if "?" not in text:
            return None
        return book.yes if fold(beat.value or "") in book.yes_values else book.no
    return None
