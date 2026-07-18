# backend/tests/test_realtime_routes.py
from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from app.core.realtime.manager import manager
from app.main import app


def test_ws_receives_message_published_to_connected_topic() -> None:
    with TestClient(app).websocket_connect("/ws?topic=combat:5") as ws:
        asyncio.run(manager.publish("combat:5", {"action": "combat_changed"}))
        data = ws.receive_json()
        assert data == {"action": "combat_changed"}


def test_ws_subscribe_action_adds_additional_topic() -> None:
    with TestClient(app).websocket_connect("/ws?topic=combat:5") as ws:
        ws.send_json({"action": "subscribe", "topic": "combat:6"})
        asyncio.run(manager.publish("combat:6", {"action": "combat_changed"}))
        data = ws.receive_json()
        assert data == {"action": "combat_changed"}


def test_ws_ignores_non_subscribe_frames() -> None:
    with TestClient(app).websocket_connect("/ws?topic=combat:5") as ws:
        ws.send_json({"action": "token.move", "x": 1, "y": 2})
        # The forged frame above must not be echoed or acted on; publishing
        # on the connected topic through the real server-side path must
        # still reach this client.
        asyncio.run(manager.publish("combat:5", {"action": "combat_changed"}))
        data = ws.receive_json()
        assert data == {"action": "combat_changed"}


def test_ws_defaults_to_broadcast_topic_when_no_query_param() -> None:
    with TestClient(app).websocket_connect("/ws") as ws:
        asyncio.run(manager.publish("broadcast", {"action": "broadcast_changed", "campaign_id": 1}))
        data = ws.receive_json()
        assert data == {"action": "broadcast_changed", "campaign_id": 1}


def test_ws_disconnect_unsubscribes_without_error() -> None:
    with TestClient(app).websocket_connect("/ws?topic=combat:7"):
        pass
    # After the context exits the client disconnects; publishing to the now-
    # unsubscribed topic must not raise.
    asyncio.run(manager.publish("combat:7", {"action": "combat_changed"}))
