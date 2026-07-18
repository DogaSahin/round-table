from __future__ import annotations

from typing import Any, cast

from fastapi import FastAPI, Request
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


def install_error_handlers(app: FastAPI) -> None:
    """Registers the single handler that maps every AppError subclass to the
    shared envelope. Call once from the app factory."""
    app.add_exception_handler(AppError, _app_error_handler)
