"""Saida estruturada sem payloads da fonte."""

import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    """Serializa contexto operacional de registros da aplicacao."""

    def format(self, record: logging.LogRecord) -> str:
        """Retorna um evento JSON por linha."""
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        for key in ("run_id", "endpoint", "stage", "rows", "duration_seconds"):
            if hasattr(record, key):
                event[key] = getattr(record, key)
        if record.exc_info:
            event["exception_type"] = (
                record.exc_info[0].__name__ if record.exc_info[0] else "unknown"
            )
        return json.dumps(event, ensure_ascii=False)


def configure_logging(level: int) -> None:
    """Configura somente o namespace f1, sem duplicar handlers em reruns."""
    logger = logging.getLogger("f1")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
