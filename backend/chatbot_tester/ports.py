from __future__ import annotations

from typing import Protocol

from .types import Effects, Message, Reply, Rule, Transcript


class TargetUnavailable(Exception):
    def __init__(self, source: str, reason: str) -> None:
        super().__init__(f"{source}: {reason}")
        self.source, self.reason = source, reason


class Target(Protocol):
    """Any bot or assistant under test: send one customer message, get its reply."""

    def send(self, message: Message) -> Reply: ...


class Environment(Protocol):
    """The target's backend as the tester sees it: reset, codes it sent, effects it caused."""

    def reset(self) -> None: ...
    def verification_codes(self, conversation_id: str) -> list[dict]: ...
    def effects(self, conversation_id: str) -> Effects: ...


class Player(Protocol):
    def next_line(self, transcript: Transcript, intent: str) -> str | None: ...


class TextJudge(Protocol):
    def judge(self, transcript: Transcript, rule: Rule) -> list[str]: ...
