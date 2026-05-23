import logging
import sys

from pythonjsonlogger import json as jsonlogger

from app.core.config import settings


def configure_logging() -> None:
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(settings.log_level)

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s "
        "%(method)s %(path)s %(status_code)s %(duration_ms)s"
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
