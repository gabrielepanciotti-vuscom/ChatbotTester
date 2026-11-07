"""The tester tests itself: each `-bad` scenario is blocked, each `-good` one passes."""

import dataclasses

from chatbot_tester.cli import main
from chatbot_tester.fakes import FakeEnvironment, FakeTarget
from chatbot_tester.personas import load as load_personas
from chatbot_tester.ports import TargetUnavailable
from chatbot_tester.round import run_round
from chatbot_tester.suite import EXAMPLES, load_rules, load_scenarios
from chatbot_tester.types import Beat, Rule, Scenario

RULES = load_rules(EXAMPLES / "rules.yaml")
PERSONAS = load_personas(EXAMPLES / "personas.yaml")
SCENARIOS = load_scenarios(EXAMPLES / "scenarios.yaml")
NOW = lambda: "2026-11-06T10:00:00Z"  # noqa: E731


def _run(scenarios, rules=RULES, env=None, target=None):
    env = env or FakeEnvironment()
    target = target or FakeTarget(
        env, per_scenario={s.code: list(s.target_script) for s in scenarios}
    )
    return run_round(scenarios, rules, PERSONAS, target, env, None, None, NOW, lambda c: f"{c}-1")


def test_every_rule_has_a_bad_and_a_good_scenario():
    codes = {s.code for s in SCENARIOS}
    for r in RULES:
        assert f"{r}-bad" in codes and f"{r}-good" in codes, r


def test_bad_scenarios_block_and_good_ones_pass():
    for s in SCENARIOS:
        r, _ = _run([s])
        if s.code.endswith("-bad"):
            assert r["esito"] == "bloccante", (s.code, r)
            assert {b["codice"] for b in r["bloccanti"]} == set(s.rules)
        else:
            assert r["esito"] == "ok", (s.code, r)


def test_cli_offline_exit_zero_when_all_pairs_behave():
    # the bundled offline run mixes -bad scenarios on purpose: it must exit 1 (blocking found)
    assert main(["--offline", "--json"]) == 1


def test_no_scenarios_is_not_collaudato():
    r, tr = _run([])
    assert r["esito"] == "non_collaudato" and r["fonti_non_disponibili"] == ["scenari"] and tr == []


def test_reset_failure_is_not_collaudato():
    env = FakeEnvironment()
    env.broken = True
    r, tr = _run(SCENARIOS[:1], env=env)
    assert (
        r["esito"] == "non_collaudato"
        and r["fonti_non_disponibili"] == ["environment"]
        and tr == []
    )


def test_target_down_marks_chat_source():
    env = FakeEnvironment()
    target = FakeTarget(env)
    target.broken = True
    r, _ = _run(SCENARIOS[:1], env=env, target=target)
    assert r["esito"] == "non_collaudato" and "chat" in r["fonti_non_disponibili"]


def test_pending_rule_only_warns_and_disabled_rule_is_skipped():
    bad = next(s for s in SCENARIOS if s.code == "R-INTRO-bad")
    pending = {"R-INTRO": dataclasses.replace(RULES["R-INTRO"], status="da_validare")}
    r, _ = _run([bad], rules=pending)
    assert r["esito"] == "avvisi" and r["bloccanti"] == [] and r["avvisi"][0]["da_validare"] is True
    off = {"R-INTRO": dataclasses.replace(RULES["R-INTRO"], status="disattivata")}
    r, _ = _run([bad], rules=off)
    assert r["esito"] == "ok" and r["regole"]["totale"] == 0


def test_llm_rule_without_judge_is_not_verifiable():
    rule = Rule("R-LLM", "", "llm", "rubric", {"rubric": "x"}, "avvisa", "attiva")
    s = Scenario("S", "g", "d", "+00 555 000 0001", "chat", (Beat("fixed", "hi"),), ("R-LLM",))
    r, _ = _run([s], rules={"R-LLM": rule})
    assert r["esito"] == "non_collaudato"


def test_unresolved_reactive_beat_is_not_verifiable():
    s = Scenario(
        "S",
        "g",
        "d",
        "+00 555 000 0001",
        "chat",
        (Beat("fixed", "hi"), Beat("reactive", wait="menu", value="nothing")),
        (),
    )
    r, tr = _run([s])
    assert r["esito"] == "non_collaudato" and tr[0].unverifiable


def test_check_raising_never_reads_as_ok():
    s = Scenario("S", "g", "d", "+00 555 000 0001", "chat", (Beat("fixed", "hi"),), ("R-X",))
    rule = Rule("R-X", "", "objective", "effect_present", {}, "blocca", "attiva")  # missing "kind"
    r, _ = _run([s], rules={"R-X": rule})
    assert r["esito"] == "non_collaudato"


def test_target_unavailable_carries_source():
    e = TargetUnavailable("chat", "down")
    assert e.source == "chat" and "down" in str(e)
