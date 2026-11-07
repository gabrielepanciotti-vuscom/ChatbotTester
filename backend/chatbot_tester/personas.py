from __future__ import annotations

import re
from pathlib import Path

import yaml

from .types import Persona


def normalize_number(number: str) -> str:
    """Digits only, international `00` prefix dropped; compared by suffix (see `same_number`)."""
    digits = re.sub(r"\D", "", number or "")
    return digits[2:] if digits.startswith("00") else digits


def same_number(a: str, b: str) -> bool:
    # shortcut: suffix match (>= 7 digits) replaces country prefixes; use a phone lib if it bites.
    x, y = normalize_number(a), normalize_number(b)
    if not x or not y:
        return False
    short, long_ = sorted((x, y), key=len)
    return len(short) >= 7 and long_.endswith(short)


def load(path) -> list[Persona]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    out, seen = [], set()
    for r in data.get("personas", []):
        if r["case_name"] in seen:
            raise ValueError(f"duplicate case_name: {r['case_name']}")
        seen.add(r["case_name"])
        out.append(
            Persona(
                case_name=r["case_name"],
                customer_id=str(r["customer_id"]),
                first_name=r["first_name"],
                last_name=r["last_name"],
                national_id=r.get("national_id", ""),
                phones=tuple(r.get("phones") or ()),
                emails=tuple(r.get("emails") or ()),
                address=r.get("address") or "",
                data=r.get("data") or {},
            )
        )
    return out


def by_contact(personas: list[Persona], contact: str) -> list[Persona]:
    return [p for p in personas if any(same_number(t, contact) for t in p.phones)]


def personal_values(p: Persona) -> list[str]:
    return [v for v in (p.first_name, p.last_name, p.national_id, p.address, *p.emails) if v]
