"""Early runtime logging for frozen Windows builds."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path


def _log_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "androidnova.log"
    return Path.cwd() / "androidnova.log"


try:
    logging.basicConfig(
        filename=_log_path(),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        encoding="utf-8",
    )
    logging.getLogger("androidnova.bootstrap").info(
        "startup: frozen=%s executable=%s cwd=%s pid=%s",
        getattr(sys, "frozen", False),
        sys.executable,
        os.getcwd(),
        os.getpid(),
    )
except Exception:
    pass
