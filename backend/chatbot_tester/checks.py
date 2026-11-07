"""Objective checks: generic over the effect kinds, so a target-specific rule is data, not code.

A check is `fn(transcript, scenario, params, personas) -> list[evidence]` (empty = conforming).
Domain checks register themselves with `register`; the nucleo knows no domain.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable

from .personas import by_contact, normalize_number, personal_values, same_number
from .types import Persona, Scenario, Transcript

Check = Callable[[Transcript, Scenario, dict, list[Persona]], list[str]]
CHECKS: dict[str, Check] = {}


def register(fn: Check) -> Check:
    CHECKS[fn.__name__] = fn
    return fn


def _tokens(s: str) -> list[str]:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"['’`]", "", s)  # D'Angelo -> dangelo
    return [x for x in re.split(r"[^a-z0-9]+", s) if x]


def _contains(text: list[str], value: list[str]) -> bool:
    """Whole-token match, so a short name never matches inside another word."""
    n = len(value)
    return n > 0 and any(text[i : i + n] == value for i in range(len(text) - n + 1))


def _texts(t: Transcript, up_to: int | None = None):
    for turn in t.turns:
        if up_to is not None and turn.index > up_to:
            break
        yield turn.index, " ".join(turn.reply.messages)


def _personas_in_play(s: Scenario, params: dict, personas: list[Persona]) -> list[Persona]:
    found = by_contact(personas, s.contact)
    for name in {params.get("case_name"), s.persona} - {None}:
        found += [p for p in personas if p.case_name == name and p not in found]
    return found


@register
def no_personal_data_before_verification(t, s, p, personas):
    in_play = _personas_in_play(s, p, personas)
    limit = t.verified_at_turn - 1 if t.verified_at_turn is not None else None
    out = []
    for i, text in _texts(t, limit):
        tt = _tokens(text)
        for who in in_play:
            for v in personal_values(who):
                tv = _tokens(v)
                if len("".join(tv)) >= 3 and _contains(tt, tv):
                    out.append(f"turn {i}: personal data of {who.case_name} before verification")
                    break
    return out


@register
def verification_only_to_registered_contacts(t, s, p, personas):
    # Only the contacts of the personas in play: a code sent to another customer's number is a leak.
    in_play = _personas_in_play(s, p, personas)
    phones = [x for who in in_play for x in who.phones]
    emails = {e.lower() for who in in_play for e in who.emails}
    out = []
    for v in t.effects.get("verification"):
        d = v.get("recipient", "")
        known = d.lower() in emails if "@" in d else any(same_number(d, x) for x in phones)
        if not known:
            out.append(f"verification code sent to an unregistered contact (turn {v.get('turn')})")
    return out


@register
def no_profile_changes(t, s, p, personas):
    return [f"profile change: {m}" for m in t.effects.get("profile_change")]


@register
def effect_present(t, s, p, personas):
    """`kind` occurs at least `min` times; one record carries every field in `fields`."""
    kind, fields = p["kind"], p.get("fields", [])
    records = t.effects.get(kind)
    if len(records) < p.get("min", 1):
        return [f"no {kind} created, expected {p.get('min', 1)}"]
    if fields and not any(
        all(r.get(f) not in (None, "", [], False) for f in fields) for r in records
    ):
        return [f"{kind} without {', '.join(fields)}"]
    return []


@register
def effect_absent(t, s, p, personas):
    n = len(t.effects.get(p["kind"]))
    return [f"{p['kind']} created but not expected ({n})"] if n else []


@register
def effect_unique(t, s, p, personas):
    refs = [r.get(p["key"]) for r in t.effects.get(p["kind"])]
    return [
        f"duplicate {p['kind']} for {p['key']} {r}"
        for r in sorted({str(r) for r in refs if refs.count(r) > 1})
    ]


@register
def summary_before_effect(t, s, p, personas):
    """Every `kind` record follows a turn whose reply matches `pattern` (recap and confirmation)."""
    pattern = re.compile(p["pattern"], re.I)
    out = []
    for rec in t.effects.get(p["kind"]):
        turn = rec.get("turn", len(t.turns))
        if not any(pattern.search(x) for i, x in _texts(t) if i < turn):
            out.append(f"{p['kind']} sent at turn {turn} without recap and confirmation")
    return out


@register
def max_menu_options(t, s, p, personas):
    m = p.get("max", 10)
    return [
        f"turn {x.index}: menu with {len(x.reply.options)} options"
        for x in t.turns
        if len(x.reply.options) > m
    ]


@register
def first_reply_mentions(t, s, p, personas):
    if not t.turns:
        return ["no reply to the first message"]
    body = _fold(" ".join(t.turns[0].reply.messages) + " " + " ".join(t.turns[0].reply.options))
    missing = [w for w in p.get("words", []) if _fold(w) not in body]
    return [f"first reply without: {', '.join(missing)}"] if missing else []


def _fold(s: str) -> str:
    return re.sub(
        r"[^a-z0-9]+",
        "",
        unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower(),
    )


__all__ = ["CHECKS", "register", "normalize_number"]
