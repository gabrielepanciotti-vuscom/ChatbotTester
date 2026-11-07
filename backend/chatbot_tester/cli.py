"""chatbot-tester: run a suite from the shell. Exit 0 ok/avvisi, 1 bloccante, 2 non_collaudato."""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

from .fakes import FakeEnvironment, FakeTarget
from .http_target import HttpTarget
from .personas import load as load_personas
from .recognizers import Phrasebook
from .round import SERVICE, run_round
from .suite import EXAMPLES, load_phrasebook, load_rules, load_scenarios

EXIT = {"ok": 0, "avvisi": 0, "bloccante": 1, "non_collaudato": 2}


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="chatbot-tester")
    p.add_argument(
        "--suite",
        help="directory with rules.yaml, scenarios.yaml, personas.yaml (default: bundled examples)",
    )
    p.add_argument(
        "--service", default=SERVICE, help="service id in the response, e.g. <target>.conversation"
    )
    p.add_argument("--target-url", help="HTTP target (see http_target.py); omitted with --offline")
    p.add_argument("--offline", action="store_true", help="self-test against the reference fake")
    p.add_argument("--code", help="play one scenario")
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)

    root = Path(a.suite) if a.suite else EXAMPLES
    rules, personas = load_rules(root / "rules.yaml"), load_personas(root / "personas.yaml")
    scenarios = load_scenarios(root / "scenarios.yaml")
    book = (
        load_phrasebook(root / "scenarios.yaml")
        if (root / "scenarios.yaml").exists()
        else Phrasebook()
    )
    scenarios = [
        s for s in scenarios if s.fake_only == a.offline and (not a.code or s.code == a.code)
    ]
    env = FakeEnvironment()
    if a.offline:
        target = FakeTarget(env, per_scenario={s.code: list(s.target_script) for s in scenarios})
        # self-test of the tester: judge as if every pending rule were validated
        rules = {
            k: dataclasses.replace(r, status="attiva") if r.status == "da_validare" else r
            for k, r in rules.items()
        }
        prepare = lambda: (target.reset(), env.reset())  # noqa: E731
    elif a.target_url:
        target, prepare = HttpTarget(a.target_url), None
    else:
        p.error("give --target-url, or --offline")
    r, _ = run_round(
        scenarios,
        rules,
        personas,
        target,
        env,
        None,
        None,
        _now,
        lambda c: f"{c}-{uuid.uuid4().hex[:8]}",
        a.service,
        prepare,
        book,
    )
    if a.json:
        print(json.dumps(r, ensure_ascii=False))
    else:
        print(
            f"{r['servizio']}: {r['esito']} "
            f"(blocking {len(r['bloccanti'])}, warnings {len(r['avvisi'])})"
        )
        for f in r["fonti_non_disponibili"]:
            print(f"  source unavailable: {f}")
    return EXIT[r["esito"]]


if __name__ == "__main__":
    sys.exit(main())
