from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.shared.errors import Conflict, Forbidden, NotFound, Validation, install_error_handlers


def _make_app() -> FastAPI:
    app = FastAPI()
    install_error_handlers(app)

    @app.get("/not-found")
    def _not_found() -> None:
        raise NotFound("campaign 7 does not exist")

    @app.get("/forbidden")
    def _forbidden() -> None:
        raise Forbidden("not a member of this game")

    @app.get("/validation")
    def _validation() -> None:
        raise Validation("name is required", details={"field": "name"})

    @app.get("/conflict")
    def _conflict() -> None:
        raise Conflict("slug already taken")

    return app


def test_not_found_envelope() -> None:
    client = TestClient(_make_app())
    resp = client.get("/not-found")
    assert resp.status_code == 404
    assert resp.json() == {
        "error": {
            "code": "not_found",
            "message": "campaign 7 does not exist",
            "details": {},
        }
    }


def test_validation_envelope_carries_details() -> None:
    client = TestClient(_make_app())
    resp = client.get("/validation")
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["details"] == {"field": "name"}


def test_forbidden_and_conflict_status_codes() -> None:
    client = TestClient(_make_app())
    assert client.get("/forbidden").status_code == 403
    assert client.get("/conflict").status_code == 409
