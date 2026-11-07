from __future__ import annotations

from collections.abc import Callable

from .engine import play
from .judge import judge
from .ports import Environment, Player, Target, TargetUnavailable, TextJudge
from .recognizers import Phrasebook
from .types import Finding, Persona, Rule, Scenario, Transcript
from .verdict import build

SERVICE = "chatbot.conversation"  # the default; callers pass the target's own service id


def run_round(
    scenarios: list[Scenario],
    rules: dict[str, Rule],
    personas: list[Persona],
    target: Target,
    env: Environment,
    player: Player | None,
    text_judge: TextJudge | None,
    now: Callable[[], str],
    new_id: Callable[[str], str],
    service: str = SERVICE,
    prepare_scenario: Callable[[], None] | None = None,
    book: Phrasebook | None = None,
) -> tuple[dict, list[Transcript]]:
    if not scenarios:
        # Nothing to play is not a pass: the standard never reads "ok" without evidence.
        return build(service, [], ["scenari"], [], [], now()), []
    try:
        env.reset()
    except TargetUnavailable as e:
        return build(service, [], [e.source], [], [s.code for s in scenarios], now()), []

    findings: list[Finding] = []
    transcripts: list[Transcript] = []
    used: dict[str, Rule] = {}
    for index, s in enumerate(scenarios):
        if index and prepare_scenario is not None:
            try:
                prepare_scenario()
            except TargetUnavailable as e:
                return build(
                    service, findings, [e.source], list(used.values()), [s.code], now()
                ), transcripts
        t = play(s, target, env, player, new_id(s.code), book)
        transcripts.append(t)
        findings.extend(judge(t, s, rules, personas, text_judge))
        if t.unverifiable:
            continue  # rules of an unplayed scenario were not judged
        for code in s.rules:
            r = rules.get(code)
            if r is not None and r.status != "disattivata":
                used[code] = r

    sources: list[str] = []
    if transcripts and all((t.unverifiable or "").startswith("chat") for t in transcripts):
        sources.append("chat")
    return build(service, findings, sources, list(used.values()), [], now()), transcripts
