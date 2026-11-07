"""The reference fakes: a scripted target and an in-memory environment.

They are what the tester's own tests (and every adapter's contract test) run against.
"""

from __future__ import annotations

from collections import defaultdict

from .personas import normalize_number
from .ports import TargetUnavailable
from .types import Effects, Message, Reply


class FakeEnvironment:
    def __init__(self) -> None:
        self.broken = False
        self._eff: dict[str, Effects] = defaultdict(Effects)

    def record(self, conversation_id: str, kind: str, data: dict) -> None:
        self._eff[conversation_id].add(kind, data)

    def reset(self) -> None:
        if self.broken:
            raise TargetUnavailable("environment", "reset failed")
        self._eff.clear()

    def verification_codes(self, conversation_id: str) -> list[dict]:
        return list(self._eff[conversation_id].get("verification"))

    def effects(self, conversation_id: str) -> Effects:
        return self._eff[conversation_id]


class FakeTarget:
    GENERIC = Reply(("Hello, how can I help you?",))

    def __init__(
        self,
        env: FakeEnvironment,
        scripts: dict[str, list[dict]] | None = None,
        per_scenario: dict[str, list[dict]] | None = None,
    ) -> None:
        """`scripts` are keyed by number. `per_scenario` (keyed by scenario code) takes precedence:
        conversation ids start with the scenario code, so scenarios sharing a number in the same
        run each play their own script instead of the last one seeded for that number.
        A step is `{replies, options, closed, effects: [{kind, record}]}`."""
        self.broken = False
        self._env = env
        self._scripts = {normalize_number(k): v for k, v in (scripts or {}).items()}
        self._per_scenario = per_scenario
        self._pos: dict[str, int] = defaultdict(int)

    def _script(self, m: Message) -> list[dict] | None:
        if self._per_scenario is None:
            return self._scripts.get(normalize_number(m.contact))
        # longest code wins: "X-bad" must not match a conversation of "X-bad-2"
        codes = [
            c
            for c in self._per_scenario
            if m.conversation_id == c or m.conversation_id.startswith(c + "-")
        ]
        return self._per_scenario[max(codes, key=len)] if codes else None

    def reset(self) -> None:
        """Discard fake-chat state before an independent offline scenario."""
        if self.broken:
            raise TargetUnavailable("chat", "reset failed")
        self._pos.clear()

    def send(self, m: Message) -> Reply:
        if self.broken:
            raise TargetUnavailable("chat", "chat endpoint unreachable")
        steps = self._script(m)
        if not steps:
            return self.GENERIC
        k = min(self._pos[m.conversation_id], len(steps) - 1)
        self._pos[m.conversation_id] += 1
        step = steps[k]
        for e in step.get("effects", []):
            self._env.record(m.conversation_id, e["kind"], e["record"])
        return Reply(
            tuple(step.get("replies", [])),
            tuple(step.get("options", [])),
            bool(step.get("closed", False)),
        )
