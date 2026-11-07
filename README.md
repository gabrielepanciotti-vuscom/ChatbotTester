# ChatbotTester

Plays a customer against a conversational assistant (any bot behind a `Target`), judges the
conversation and the side effects it caused, and answers with the standard verdict:
`ok | avvisi | bloccante | non_collaudato`.

```bash
cd backend && python -m pytest -q                 # tests (the tester tests itself)
python -m chatbot_tester --offline --json         # self-test against the reference fake (exit 1: the -bad scenarios block)
python -m chatbot_tester --suite <dir> --target-url https://bot.example.com/chat --service acme.conversation
```

## Layers

| Layer | Where | Holds |
|---|---|---|
| Nucleus | `backend/chatbot_tester/` | types, ports, engine, recognizers, generic checks, judge, verdict, reference fakes, generic HTTP target, LLM player/judge. No company or target names (a test enforces it). |
| Local | the tree (`<instance>/config/chatbot-tester/` and its own adapters) | `rules.yaml`, `scenarios.yaml`, `personas.yaml`, the adapter to a specific bot and its backend, domain-specific checks (`register`), tracker sync, staff UI wiring |

## The target interface

`Target.send(Message) -> Reply` (the bot) and `Environment` (`reset`, `verification_codes`, `effects`: what the
bot's backend did). A bot that speaks the JSON shape of `http_target.py` needs no code. Any other bot
(a Coordinator bot included) writes a class with `send` in its tree. `FakeTarget` + `FakeEnvironment` are the
reference fakes: an adapter passes the same contract tests as they do.

## Rules as data

A rule names a `check` and its `params`; effects are generic (`by_kind`), so «a ticket with an attachment»,
«one lead per reference» or «no data before verification» are YAML, not code. A domain check is a function
registered with `chatbot_tester.checks.register` from the tree. LLM rules (`judge: llm`) are always warnings.

The response keys (`esito`, `bloccanti`, `avvisi`, `fonti_non_disponibili`, …) are the shared collaudo standard
and stay as they are.
