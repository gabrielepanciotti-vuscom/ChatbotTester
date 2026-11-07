import httpx
import pytest
from chatbot_tester.http_target import HttpTarget
from chatbot_tester.ports import TargetUnavailable
from chatbot_tester.types import Message

M = Message("+00 555 000 0001", "chat", "hi", "c1")


def _target(handler):
    return HttpTarget(
        "http://bot.test/chat", client=httpx.Client(transport=httpx.MockTransport(handler))
    )


def test_maps_the_reply():
    t = _target(
        lambda r: httpx.Response(
            200, json={"messages": ["a", "b"], "options": ["x"], "closed": True}
        )
    )
    r = t.send(M)
    assert r.messages == ("a", "b") and r.options == ("x",) and r.closed


def test_http_error_is_unavailable_chat():
    with pytest.raises(TargetUnavailable) as e:
        _target(lambda r: httpx.Response(503)).send(M)
    assert e.value.source == "chat"


def test_network_error_is_unavailable_chat():
    def boom(r):
        raise httpx.ConnectError("down")

    with pytest.raises(TargetUnavailable):
        _target(boom).send(M)
