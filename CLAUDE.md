# ChatbotTester — Life node (public)

Plays a customer against any conversational assistant and returns the standard verdict. General
engine only: no company, person, host or credential here; everything specific lives in the tree.
See `README.md`. Node type `cli` for now; API, staff UI (`@suite/design-system`) and DB are not built yet.

## Commands
```bash
cd backend && python -m pytest -q
python -m chatbot_tester --offline --json   # exit 0 ok/avvisi, 1 bloccante, 2 non_collaudato
```

## Rules
- Nucleus never names a company or target (`tests/test_nucleus_boundary.py`).
- New check = a function registered with `register`; prefer a rule over generic checks (`effect_present`…) before new code.
- A rule with `judge: llm` or status `da_validare` can warn, never block. Nothing to play is `non_collaudato`, never `ok`.
- Fixtures are fictitious; code, comments and docs in English; wire keys of the verdict stay Italian (collaudo standard).
