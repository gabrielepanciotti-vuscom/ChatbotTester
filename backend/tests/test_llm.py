from chatbot_tester.llm import LlmJudge, LlmPlayer
from chatbot_tester.types import Reply, Rule, Transcript, Turn

T = Transcript("S", "c", [Turn(0, "hi", Reply(("hello",)))])


def test_player_unknown_means_no_line():
    assert LlmPlayer(lambda *a: "UNKNOWN").next_line(T, "x") is None
    assert LlmPlayer(lambda *a: "ok then").next_line(T, "x") == "ok then"


def test_player_failure_means_no_line():
    def boom(*a):
        raise RuntimeError("x")

    assert LlmPlayer(boom).next_line(T, "x") is None


def test_judge_parses_and_stays_inside_notes_dir(tmp_path):
    (tmp_path / "n.md").write_text("fact", encoding="utf-8")
    seen = {}

    def complete(service, system, user):
        seen["user"] = user
        return '```json\n{"findings": [{"turn": 0, "evidence": "wrong"}]}\n```'

    rule = Rule(
        "R",
        "",
        "llm",
        "rubric",
        {"rubric": "r", "notes": ["n.md", "../outside.md"]},
        "avvisa",
        "attiva",
    )
    assert LlmJudge(complete, tmp_path).judge(T, rule) == ["turn 0: wrong"]
    assert "fact" in seen["user"]
