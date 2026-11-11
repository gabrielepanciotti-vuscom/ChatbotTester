# Life window deploy order: not deployable yet, reply sent

Refs #1 (stays open: it is the deployment itself).

## What was done
- Life (life-personal-pc) asked for a production deploy on dev-linux with embed mode. ChatbotTester is
  CLI-only (no API, frontend or DB), so per the order no stub was shipped: issue #1 lists what is missing
  and the canonical ports (front 3441, back 10107, db 11219).
- Reply sent on the Network bus to life-personal-pc (conversation 5924): not ready, what is missing,
  door target `10.231.0.1:3441`.
- To send it, three root causes were fixed:
  1. `~/.claude/scripts/hub-valorizza-env.py` read the bus admin password from `~/work/Network`, but on
     dev-linux the bus runs from the standby checkout `~/standby/minipc/personal/Network`: every node got 401.
     It now tries the checkout of the running `network-backend` container first and keeps the first password
     the bus accepts (`f9520d5e`, test `scripts/tests/test_hub_valorizza_env.py`).
  2. ChatbotTester had no path for `work-dev-linux` in any instance graph, so no bus identity. Path override
     added in `life-personal/life.graph.json` (`57e8f3a`).
  3. `.env` was not git-ignored here (`e58bf4d`).

## How it works
The bus identity of a node comes from `suite_core.nodes instances agents`: a node gets one only if an
instance graph gives it a path on this device. The identity script writes `HUB_URL/HUB_AGENT_ID/HUB_AGENT_KEY`
into the node's ignored `.env`; `hub_send.py` speaks with it, only inside its tenant.

## Structure
- `.gitignore` (this repo)
- `~/.claude/scripts/hub-valorizza-env.py`, `~/.claude/scripts/tests/test_hub_valorizza_env.py`
- `life-personal/life.graph.json` (added), `life-vuscom/life.graph.json` (added then removed, `559ab630`)

## How to verify
```bash
python3 ~/.claude/scripts/hub-valorizza-env.py          # last line: ok 95, no 401
python3 ~/.claude/scripts/hub_send.py list              # conversation 5924 open
```

## Decisions
- ChatbotTester is the generic tool skeleton; the VUS COM chatbot tester is Vicky (Gabriele, 11/11/2026).
  So the node lives in the `personal` instance, not `vuscom`, and its identity is in tenant `life-personal`.
- No stub deploy: the order said to report what is missing instead.

## Open
- The old `chatbotTester-work-dev-linux` agent may still exist in tenant `life-vuscom` on the bus.
- Project standard artifacts missing (`avvia-progetto`).
