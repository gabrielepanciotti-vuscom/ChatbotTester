from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Persona:
    """A fictitious customer the tester plays and whose data it knows."""

    case_name: str
    customer_id: str
    first_name: str
    last_name: str
    national_id: str
    phones: tuple[str, ...]
    emails: tuple[str, ...]
    address: str
    data: dict = field(default_factory=dict)  # free-form, domain specific


@dataclass(frozen=True)
class Beat:
    """One script line: `fixed` text, or `reactive` (answers what the assistant just asked)."""

    kind: str  # "fixed" | "reactive"
    text: str | None = None  # fixed
    wait: str | None = None  # reactive: "verification_code" | "menu" | "yes_no" | "free"
    value: str | None = None  # menu label to pick, "yes"/"no", or the intent for "free"
    attachments: tuple[str, ...] = ()


@dataclass(frozen=True)
class Scenario:
    code: str
    group: str  # free grouping label (use case, area)
    description: str
    contact: str  # the customer's number or address
    channel: str
    beats: tuple[Beat, ...]
    rules: tuple[str, ...]
    persona: str | None = None  # Persona.case_name, when the number alone is ambiguous
    target_script: tuple[dict, ...] = ()  # only for reference-fake scenarios
    fake_only: bool = False


@dataclass(frozen=True)
class Message:
    contact: str
    channel: str
    text: str
    conversation_id: str
    attachments: tuple[str, ...] = ()


@dataclass(frozen=True)
class Reply:
    messages: tuple[str, ...]
    options: tuple[str, ...] = ()
    closed: bool = False


@dataclass(frozen=True)
class Turn:
    index: int
    user: str
    reply: Reply


@dataclass
class Effects:
    """Side effects observed on the target's backend, by kind (e.g. `verification`, `ticket`)."""

    by_kind: dict[str, list[dict]] = field(default_factory=dict)

    def get(self, kind: str) -> list[dict]:
        return self.by_kind.get(kind, [])

    def add(self, kind: str, record: dict) -> None:
        self.by_kind.setdefault(kind, []).append(dict(record))


@dataclass
class Transcript:
    scenario: str
    conversation_id: str
    turns: list[Turn] = field(default_factory=list)
    effects: Effects = field(default_factory=Effects)
    verified_at_turn: int | None = None
    player_turns: list[int] = field(default_factory=list)  # turns written by the LLM player
    unverifiable: str | None = None  # reason, if the run could not complete


@dataclass(frozen=True)
class Finding:
    code: str
    outcome: str  # "difforme" | "non_verificabile"
    severity: str  # "blocca" | "avvisa"
    message: str
    owner: str  # who must act: the supplier, the house team, or nobody
    pending_validation: bool
    evidence: str | None = None
    source: str | None = None
    case: str | None = None

    def as_dict(self) -> dict:
        # wire keys are the shared collaudo standard (Italian), kept as is
        return {
            "codice": self.code,
            "esito": self.outcome,
            "gravita": self.severity,
            "messaggio": self.message,
            "intervento": self.owner,
            "da_validare": self.pending_validation,
            "evidenza": self.evidence,
            "fonte": self.source,
            "caso": self.case,
        }


@dataclass(frozen=True)
class Rule:
    code: str
    requirement: str
    judge: str  # "objective" | "llm"
    check: str  # key of the check registry, or "rubric" for the LLM judge
    params: dict
    severity: str  # "blocca" | "avvisa"
    status: str  # "da_validare" | "attiva" | "disattivata"
    title: str = ""
