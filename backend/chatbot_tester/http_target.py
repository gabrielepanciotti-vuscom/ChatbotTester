"""Generic HTTP adapter: any assistant that can be reached with one JSON POST per customer message.

Request:  {"contact", "channel", "text", "conversation_id", "attachments": [...]}
Response: {"messages": [...], "options": [...], "closed": bool}
A target with another wire shape writes its own adapter (a class with `send`) in its tree.
"""

from __future__ import annotations

import httpx

from .ports import TargetUnavailable
from .types import Message, Reply


class HttpTarget:
    def __init__(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._url, self._headers, self._timeout = url, headers or {}, timeout
        self._client = client or httpx.Client()

    def send(self, m: Message) -> Reply:
        body = {
            "contact": m.contact,
            "channel": m.channel,
            "text": m.text,
            "conversation_id": m.conversation_id,
            "attachments": list(m.attachments),
        }
        try:
            r = self._client.post(
                self._url, json=body, headers=self._headers, timeout=self._timeout
            )
        except httpx.HTTPError as e:
            raise TargetUnavailable(
                "chat", f"chat endpoint unreachable: {e.__class__.__name__}"
            ) from e
        if r.status_code != 200:
            raise TargetUnavailable("chat", f"chat endpoint answered HTTP {r.status_code}")
        d = r.json()
        return Reply(
            tuple(d.get("messages", [])), tuple(d.get("options", [])), bool(d.get("closed", False))
        )
