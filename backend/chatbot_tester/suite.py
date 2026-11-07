"""A test suite as data: rules, scenarios and personas in YAML (see examples/)."""

from __future__ import annotations

from pathlib import Path

import yaml

from .recognizers import Phrasebook
from .types import Beat, Rule, Scenario

EXAMPLES = Path(__file__).parent / "examples"


def load_rules(path) -> dict[str, Rule]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return {
        r["code"]: Rule(
            code=r["code"],
            requirement=r.get("requirement", ""),
            judge=r.get("judge", "objective"),
            check=r["check"],
            params=r.get("params") or {},
            severity=r.get("severity", "avvisa"),
            status=r.get("status", "da_validare"),
            title=r.get("title", ""),
        )
        for r in data.get("rules", [])
    }


def load_scenarios(path) -> list[Scenario]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return [
        Scenario(
            code=s["code"],
            group=s.get("group", ""),
            description=s.get("description", ""),
            contact=s["contact"],
            channel=s.get("channel", "chat"),
            beats=tuple(
                Beat(
                    b["kind"],
                    b.get("text"),
                    b.get("wait"),
                    b.get("value"),
                    tuple(b.get("attachments") or ()),
                )
                for b in s["beats"]
            ),
            rules=tuple(s.get("rules") or ()),
            persona=s.get("persona"),
            target_script=tuple(s.get("target_script") or ()),
            fake_only=bool(s.get("fake_only", False)),
        )
        for s in data.get("scenarios", [])
    ]


def load_phrasebook(path) -> Phrasebook:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    p = data.get("phrasebook") or {}
    return Phrasebook(**{k: (tuple(v) if isinstance(v, list) else v) for k, v in p.items()})
