"""LLM player and judge. `complete(service, task, input) -> text` is injected; no model is named."""

from __future__ import annotations

import json
import logging
import shlex
import subprocess
from pathlib import Path

import httpx

from .types import Rule, Transcript

log = logging.getLogger(__name__)
MAX_NOTE_CHARS = 30_000
TIMEOUT_S = 330


class LlmRun:
    """Runs one task on a routed service through the `llm-run` CLI (queue lives in its config)."""

    def __init__(self, command: str, timeout: int = TIMEOUT_S) -> None:
        self._command, self._timeout = shlex.split(command), timeout

    def __call__(self, service: str, task: str, text: str) -> str:
        p = subprocess.run(
            [*self._command, "run", "--servizio", service, task],
            input=text,
            capture_output=True,
            text=True,
            timeout=self._timeout,
            check=False,
        )
        if p.returncode != 0:
            raise RuntimeError(f"llm-run {service} exit {p.returncode}: {p.stderr[-300:]}")
        return p.stdout.strip()


class LlmHttp:
    """Same contract as `LlmRun`, through the gateway HTTP endpoint (hosts without the CLI)."""

    def __init__(self, url: str, timeout: int = TIMEOUT_S) -> None:
        self._url, self._timeout = url, timeout

    def __call__(self, service: str, task: str, text: str) -> str:
        r = httpx.post(
            self._url,
            json={"servizio": service, "testo": f"{task}\n\n{text}"},
            timeout=self._timeout,
        )
        if r.status_code != 200:
            raise RuntimeError(f"gateway {service} HTTP {r.status_code}: {r.text[-300:]}")
        return str(r.json().get("testo", "")).strip()


def dialogue(t: Transcript) -> str:
    lines = []
    for turn in t.turns:
        lines.append(f"[{turn.index}] CUSTOMER: {turn.user}")
        lines += [f"[{turn.index}] ASSISTANT: {m}" for m in turn.reply.messages]
        if turn.reply.options:
            lines.append(f"[{turn.index}] OPTIONS: " + " | ".join(turn.reply.options))
    return "\n".join(lines)


class LlmPlayer:
    """Plays the customer for a turn no deterministic recognizer could handle."""

    def __init__(
        self,
        complete,
        service: str = "chatbotTester.player",
        language: str = "English",
        persona_brief: str = "a customer of the company behind the assistant",
    ) -> None:
        self._complete, self._service = complete, service
        self._system = (
            f"You are {persona_brief}, writing to a virtual assistant. Reply with ONE short line, "
            f"in {language}, consistent with this intent: {{intent}}. Do not invent personal data. "
            "If you do not know what to reply, write exactly UNKNOWN."
        )

    def next_line(self, transcript: Transcript, intent: str) -> str | None:
        try:
            text = self._complete(
                self._service,
                self._system.format(intent=intent),
                dialogue(transcript) or "(no message yet)",
            )
        except Exception:  # noqa: BLE001 - the engine turns None into non_verificabile
            log.exception("LLM player failed")
            return None
        return None if not text or text == "UNKNOWN" else text


class LlmJudge:
    """Judges a transcript against a rule's rubric and the reference notes it cites."""

    def __init__(self, complete, notes_dir: Path, service: str = "chatbotTester.judge") -> None:
        self._complete, self._service, self._notes = complete, service, Path(notes_dir)

    def _reference(self, rule: Rule) -> str:
        base = self._notes.resolve()
        parts: list[str] = []
        for rel in rule.params.get("notes", []):
            p = (base / rel).resolve()
            if p != base and base not in p.parents:
                continue  # never read outside the notes dir
            for f in sorted(p.rglob("*.md")) if p.is_dir() else [p]:
                if f.is_file():
                    parts.append(f"### {f.name}\n{f.read_text(encoding='utf-8')}")
        return "\n\n".join(parts)[:MAX_NOTE_CHARS]

    def judge(self, transcript: Transcript, rule: Rule) -> list[str]:
        system = (
            "You are a tester. Judge the conversation against the rubric, using ONLY the reference "
            "notes as the source of truth. Reply with JSON only: "
            '{"findings": [{"turn": <int>, "evidence": "<text>"}]}; an empty list when conforming.'
        )
        user = (
            f"RUBRIC:\n{rule.params.get('rubric', rule.title)}\n\n"
            f"REFERENCE NOTES:\n{self._reference(rule)}\n\nCONVERSATION:\n{dialogue(transcript)}"
        )
        raw = self._complete(self._service, system, user).strip()
        if raw.startswith("```"):
            raw = raw.strip("`").removeprefix("json").strip()
        try:
            return [f"turn {d['turn']}: {d['evidence']}" for d in json.loads(raw)["findings"]]
        except (ValueError, KeyError, TypeError) as e:
            raise ValueError(f"invalid judge reply: {raw[:100]!r}") from e
