# backend/app/core/realtime/routes.py
from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.realtime.manager import manager

router = APIRouter()


@router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket, topic: str = "broadcast") -> None:
    await websocket.accept()
    manager.subscribe(topic, websocket)
    try:
        while True:
            message = await websocket.receive_json()
            if message.get("action") == "subscribe":
                manager.subscribe(message.get("topic", topic), websocket)
            # Any other inbound frame is ignored: subscribers only ever
            # read; publishing happens exclusively from server-side routes.
            # Echoing an arbitrary client frame back onto a topic would let
            # any socket forge state (e.g. a fake token.move) for every
            # other subscriber to that topic.
    except WebSocketDisconnect:
        pass
    finally:
        manager.unsubscribe(websocket)
