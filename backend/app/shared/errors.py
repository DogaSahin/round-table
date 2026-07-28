from __future__ import annotations

from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base for every typed application error. Carries the fields the shared
    JSON error envelope needs: an error code, an HTTP status, a human
    message, and optional structured details."""

    code: str = "internal_error"
    status_code: int = 500

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFound(AppError):
    code = "not_found"
    status_code = 404


class Forbidden(AppError):
    code = "forbidden"
    status_code = 403


class Validation(AppError):
    code = "validation_error"
    status_code = 422


class Conflict(AppError):
    code = "conflict"
    status_code = 409


def _app_error_handler(request: Request, exc: Exception) -> JSONResponse:
    error = cast(AppError, exc)
    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": {
                "code": error.code,
                "message": error.message,
                "details": error.details,
            }
        },
    )


def _request_validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Maps FastAPI's own body-validation errors (raised automatically when a
    Pydantic request schema's field constraints fail, e.g. min_length, or a
    custom `field_validator` raises ValueError) onto the same shared envelope
    as Validation(AppError), so callers never need to special-case this path
    vs. an application-raised Validation error.

    `error.errors()` isn't always JSON-serializable as-is: a custom
    `field_validator` that raises `ValueError` produces an entry with
    `ctx.error` set to the actual exception instance, which the default JSON
    encoder can't handle. Run it through `jsonable_encoder` (same as
    FastAPI's own default handler) — the human-readable `msg` field already
    carries the exception's message, so nothing is lost.
    """
    error = cast(RequestValidationError, exc)
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": Validation.code,
                "message": "Request validation failed.",
                "details": {"errors": jsonable_encoder(error.errors())},
            }
        },
    )


def install_error_handlers(app: FastAPI) -> None:
    """Registers the handlers that map every AppError subclass, and FastAPI's
    own request-validation errors, to the shared envelope. Call once from the
    app factory."""
    app.add_exception_handler(AppError, _app_error_handler)
    app.add_exception_handler(RequestValidationError, _request_validation_error_handler)
