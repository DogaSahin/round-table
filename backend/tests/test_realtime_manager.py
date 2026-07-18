from __future__ import annotations

import asyncio
from typing import Any

from app.core.realtime.manager import ConnectionManager


class _FakeWebSocket:
    def __init__(self, fail: bool = False) -> None:
        self.sent: list[dict[str, Any]] = []
        self.fail = fail

    async def send_json(self, message: dict[str, Any]) -> None:
        if self.fail:
            raise RuntimeError("boom")
        self.sent.append(message)


def test_subscribe_and_publish_delivers_to_subscriber() -> None:
    mgr = ConnectionManager()
    ws = _FakeWebSocket()
    mgr.subscribe("topic1", ws)
    asyncio.run(mgr.publish("topic1", {"a": 1}))
    assert ws.sent == [{"a": 1}]


def test_publish_to_topic_with_no_subscribers_is_noop() -> None:
    mgr = ConnectionManager()
    asyncio.run(mgr.publish("empty", {"a": 1}))


def test_unsubscribe_removes_from_all_topics() -> None:
    mgr = ConnectionManager()
    ws = _FakeWebSocket()
    mgr.subscribe("t1", ws)
    mgr.subscribe("t2", ws)
    mgr.unsubscribe(ws)
    asyncio.run(mgr.publish("t1", {"a": 1}))
    assert ws.sent == []


def test_publish_drops_dead_socket_and_continues() -> None:
    mgr = ConnectionManager()
    good = _FakeWebSocket()
    bad = _FakeWebSocket(fail=True)
    mgr.subscribe("t", bad)
    mgr.subscribe("t", good)
    asyncio.run(mgr.publish("t", {"a": 1}))
    assert good.sent == [{"a": 1}]
    # bad was dropped by the first publish; a second publish must not error
    # and must still reach the surviving subscriber.
    asyncio.run(mgr.publish("t", {"a": 2}))
    assert good.sent == [{"a": 1}, {"a": 2}]


def test_multiple_subscribers_same_topic_all_receive() -> None:
    mgr = ConnectionManager()
    ws1, ws2 = _FakeWebSocket(), _FakeWebSocket()
    mgr.subscribe("t", ws1)
    mgr.subscribe("t", ws2)
    asyncio.run(mgr.publish("t", {"x": 1}))
    assert ws1.sent == [{"x": 1}]
    assert ws2.sent == [{"x": 1}]
