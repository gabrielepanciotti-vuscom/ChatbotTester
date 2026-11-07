from __future__ import annotations

from .checks import CHECKS
from .ports import TextJudge
from .types import Finding, Persona, Rule, Scenario, Transcript


def _unverifiable(r: Rule, s: Scenario, reason: str) -> Finding:
    return Finding(
        r.code,
        "non_verificabile",
        "avvisa",
        r.title or r.code,
        "nessuno",
        r.status == "da_validare",
        reason,
        r.requirement,
        s.code,
    )


def judge(
    t: Transcript,
    s: Scenario,
    rules: dict[str, Rule],
    personas: list[Persona],
    text_judge: TextJudge | None,
) -> list[Finding]:
    if t.unverifiable:
        return [
            Finding(
                f"{s.code}-NOT-VERIFIABLE",
                "non_verificabile",
                "avvisa",
                "scenario not completed",
                "nessuno",
                False,
                t.unverifiable,
                None,
                s.code,
            )
        ]
    out: list[Finding] = []
    for code in s.rules:
        r = rules.get(code)
        if r is None or r.status == "disattivata":
            continue
        # an LLM judgement or an unvalidated rule can warn, never block
        severity = "avvisa" if (r.judge == "llm" or r.status == "da_validare") else r.severity
        try:
            if r.judge == "llm":
                if text_judge is None:
                    out.append(_unverifiable(r, s, "LLM judge unavailable"))
                    continue
                evidence = text_judge.judge(t, r)
            else:
                evidence = CHECKS[r.check](t, s, r.params, personas)
        except Exception as e:  # a broken check must never read as "ok"
            out.append(_unverifiable(r, s, f"check failed: {e!r}"))
            continue
        for ev in evidence:
            out.append(
                Finding(
                    r.code,
                    "difforme",
                    severity,
                    r.title or r.code,
                    "fornitore",
                    r.status == "da_validare",
                    ev,
                    r.requirement,
                    s.code,
                )
            )
    return out
