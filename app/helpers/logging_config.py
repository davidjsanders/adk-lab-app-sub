import json
import logging


class JsonFormatter(logging.Formatter):
    """Structured JSON log formatter for enhanced observability and tracing."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
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

