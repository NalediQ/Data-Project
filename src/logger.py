"""
Centralised logging. Every pipeline stage imports `get_logger` instead of
calling `print`, so runs are auditable from the log file as well as stdout.
"""
from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

_configured = False


def get_logger():
    global _configured
    if not _configured:
        logger.remove()  # drop the default handler to avoid duplicate lines
        logger.add(sys.stderr, level="INFO",
                    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                           "<level>{level: <8}</level> | {message}")
        logger.add(LOG_DIR / "pipeline.log", level="DEBUG", rotation="1 MB",
                    retention="14 days")
        _configured = True
    return logger
