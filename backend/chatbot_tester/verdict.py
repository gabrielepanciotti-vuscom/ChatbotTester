"""The standard collaudo response. Wire keys and values are the shared standard, kept as is."""

from __future__ import annotations

import hashlib

from .types import Finding, Rule


def outcome_of(findings: list[Finding], unavailable_sources: list[str]) -> str:
    if any(x.severity == "blocca" and x.outcome == "difforme" for x in findings):
        return "bloccante"
    if unavailable_sources or any(x.outcome == "non_verificabile" for x in findings):
        return "non_collaudato"
    return "avvisi" if findings else "ok"


def _version(rules: list[Rule]) -> str:
    key = "|".join(
        sorted(f"{r.code}:{r.severity}:{r.status}:{sorted(r.params.items())}" for r in rules)
    )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]


def build(
    service: str,
    findings: list[Finding],
    unavailable_sources: list[str],
    rules: list[Rule],
    skipped: list[str],
    generated_at: str,
) -> dict:
    esito = outcome_of(findings, unavailable_sources)
    blocking = [x for x in findings if x.severity == "blocca" and x.outcome == "difforme"]
    return {
        "servizio": service,
        "esito": esito,
        "collaudato": esito != "non_collaudato",
        "salto": list(skipped),
        "regole": {
            "versione": _version(rules),
            "totale": len(rules),
            "da_validare": sum(1 for r in rules if r.status == "da_validare"),
        },
        "bloccanti": [x.as_dict() for x in blocking],
        "avvisi": [x.as_dict() for x in findings if x not in blocking],
        "fonti_non_disponibili": list(unavailable_sources),
        "generato_il": generated_at,
    }
