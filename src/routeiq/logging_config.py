"""Logging setup for the RouteIQ pipeline.

Every pipeline run writes a timestamped log file to `logs/` and mirrors
output to the console, so a run is auditable after the fact without
re-executing it.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from routeiq.config import LOG_FILE_PREFIX, LOGS_DIR

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(name: str = "routeiq_phase1") -> logging.Logger:
    """Configure and return the pipeline's root logger.

    Idempotent per process: calling this more than once will not attach
    duplicate handlers to the same logger instance.

    Args:
        name: Logger name, used both for the `logging.Logger` and as a
            prefix-free identifier in log lines.

    Returns:
        A configured `logging.Logger` writing to both console and a
        timestamped file under `logs/`.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path: Path = LOGS_DIR / f"{LOG_FILE_PREFIX}_{timestamp}.log"

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False

    logger.info("Logging initialized. Log file: %s", log_path)
    return logger
