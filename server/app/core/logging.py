"""Structured logging with secret redaction.

Redaction is applied at the formatter, not at call sites. Relying on every
future call site to remember not to log a token is how secrets end up in logs;
filtering centrally means a mistake upstream is still caught.
"""

from __future__ import annotations

import json
import logging
import re
import sys

# Substrings that mark a field as sensitive, matched case-insensitively.
SENSITIVE = ("authorization", "token", "api_key", "apikey", "secret",
             "password", "clerk_secret", "cookie", "bearer")

_BEARER = re.compile(r"(bearer\s+)[A-Za-z0-9._\-]+", re.IGNORECASE)
_LONGKEY = re.compile(r"\b[A-Za-z0-9_\-]{32,}\b")


def redact(text: str) -> str:
    text = _BEARER.sub(r"\1<redacted>", text)
    if any(s in text.lower() for s in SENSITIVE):
        text = _LONGKEY.sub("<redacted>", text)
    return text


class RedactingJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": redact(record.getMessage()),
        }
        for key in ("request_id", "user_id", "route_id", "path", "status_code",
                    "duration_ms"):
            v = getattr(record, key, None)
            if v is not None:
                payload[key] = v
        if record.exc_info:
            payload["exception"] = redact(self.formatException(record.exc_info))
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(RedactingJsonFormatter())
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    # Access logs duplicate our middleware logging.
    logging.getLogger("uvicorn.access").disabled = True
