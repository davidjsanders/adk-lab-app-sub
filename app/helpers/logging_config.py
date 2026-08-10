import json
import logging
import re


def redact_pii(text: str) -> str:
    """Redact sensitive PII and auth tokens from log strings."""
    if not isinstance(text, str):
        return text
    # Redact email addresses
    text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[REDACTED_EMAIL]", text)
    # Redact Bearer tokens and secret keys
    text = re.sub(r"(Bearer\s+)[A-Za-z0-9\-\._~\+\/]+=*", r"\1[REDACTED_TOKEN]", text)
    text = re.sub(r"(key|secret|password|token)=\"[^\"]+\"", r'\1="[REDACTED]"', text, flags=re.IGNORECASE)
    return text


class JsonFormatter(logging.Formatter):
    """Structured JSON log formatter with PII redaction and Intent-vs-Outcome tracking for observability."""

    def format(self, record: logging.LogRecord) -> str:
        msg = redact_pii(record.getMessage())
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": msg,
            "module": record.module,
            "line": record.lineno,
            "intent": getattr(record, "intent", "N/A"),
            "outcome": getattr(record, "outcome", "N/A"),
        }
        if record.exc_info:
            log_obj["exception"] = redact_pii(self.formatException(record.exc_info))
        return json.dumps(log_obj)


def setup_logging(level=logging.INFO, json_format=True):
    """Configures root logger with structured JSON formatting for observability.

    Args:
        level: Minimum logging level (e.g. logging.INFO or logging.DEBUG).
        json_format: Boolean indicating whether to output structured JSON logs.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear pre-existing handlers to prevent duplicate lines
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler()
    if json_format:
        handler.setFormatter(JsonFormatter())
    else:
        log_format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        handler.setFormatter(logging.Formatter(log_format))

    root_logger.addHandler(handler)

