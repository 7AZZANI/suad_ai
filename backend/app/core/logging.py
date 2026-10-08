"""Structured, human-readable logging.

Emits single-line key=value records that are greppable in dev and easy to
ship to a JSON pipeline in production.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

from app.core.config import settings

_CONFIGURED = False


class KeyValueFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = (
            f"ts={self.formatTime(record, '%Y-%m-%dT%H:%M:%S')} "
            f"level={record.levelname} "
            f"logger={record.name} "
            f'msg="{record.getMessage()}"'
        )
        extra = getattr(record, "context", None)
        if extra:
            base += " " + " ".join(f"{k}={v}" for k, v in extra.items())
        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        return base


def setup_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(KeyValueFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.log_level.upper())
    # Tame chatty libraries.
    for noisy in ("httpx", "httpcore", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)


def log_event(logger: logging.Logger, level: int, msg: str, **context: Any) -> None:
    """Log with structured context: ``log_event(log, logging.INFO, "x", a=1)``."""
    logger.log(level, msg, extra={"context": context})
