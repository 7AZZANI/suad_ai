"""Structured error model + FastAPI exception handlers.

All failures surface as a consistent JSON envelope:

    {"error": {"code": "...", "message": "...", "details": {...}}}
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger("app.errors")


class AppError(Exception):
    """Base class for all expected, structured application errors."""

    code = "app_error"
    status_code = 400

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_response(self) -> JSONResponse:
        return JSONResponse(
            status_code=self.status_code,
            content={
                "error": {
                    "code": self.code,
                    "message": self.message,
                    "details": self.details,
                }
            },
        )


class ConfigurationError(AppError):
    code = "configuration_error"
    status_code = 500


class ProviderError(AppError):
    """A configured external/local provider failed or is unreachable."""

    code = "provider_error"
    status_code = 502


class ProviderNotConfigured(AppError):
    code = "provider_not_configured"
    status_code = 503


class PermissionDenied(AppError):
    code = "permission_denied"
    status_code = 403


class ApprovalRequired(AppError):
    """A risky action needs explicit human approval before it runs."""

    code = "approval_required"
    status_code = 412


class NotFoundError(AppError):
    code = "not_found"
    status_code = 404


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        logger.warning("app_error code=%s msg=%s", exc.code, exc.message)
        return exc.to_response()

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed.",
                    "details": {"errors": exc.errors()},
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "http_error",
                    "message": str(exc.detail),
                    "details": {},
                }
            },
        )

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred.",
                    "details": {},
                }
            },
        )
