from __future__ import annotations

from .ports import Environment, Player, Target, TargetUnavailable
from .recognizers import Phrasebook, answer
from .types import Message, Reply, Scenario, Transcript, Turn

MAX_TURNS = 20


def play(
    scenario: Scenario,
    target: Target,
    env: Environment,
    player: Player | None,
    conversation_id: str,
    book: Phrasebook | None = None,
) -> Transcript:
    book = book or Phrasebook()
    t = Transcript(scenario=scenario.code, conversation_id=conversation_id)
    last = Reply(())
    try:
        for b in scenario.beats:
            if len(t.turns) >= MAX_TURNS:
                break
            if b.kind == "fixed":
                text = b.text or ""
            else:
                codes = (
                    env.verification_codes(conversation_id) if b.wait == "verification_code" else []
                )
                text = answer(b, last, codes, book)
                if text is None and player is not None and b.wait == "free":
                    text = player.next_line(t, b.value or "")
                    if text is not None:
                        t.player_turns.append(len(t.turns))
                if text is None:
                    t.unverifiable = f"beat {b.wait} unresolved at turn {len(t.turns)}"
                    break
            last = target.send(
                Message(scenario.contact, scenario.channel, text, conversation_id, b.attachments)
            )
            if b.wait == "verification_code":
                t.verified_at_turn = len(t.turns)
            t.turns.append(Turn(len(t.turns), text, last))
            if last.closed:
                break
        t.effects = env.effects(conversation_id)
    except TargetUnavailable as e:
        t.unverifiable = str(e)
    return t
