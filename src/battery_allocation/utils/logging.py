"""Structured logging configuration."""

from __future__ import annotations

import logging
import sys


def setup_logging(level: str = "INFO", fmt: str = "text") -> None:
    root = logging.getLogger()
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if fmt == "json":
        formatter = logging.Formatter(
            '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}'
        )
    else:
        formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")

    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(level.upper())

    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
