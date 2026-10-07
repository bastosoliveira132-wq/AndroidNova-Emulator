"""AndroidNova application entry point."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from androidnova.config.manager import load_config
from androidnova.ui.main_window import create_window


LOGGER = logging.getLogger(__name__)


def application_root() -> Path:
    """Return the writable application directory for source and PyInstaller builds."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def bundled_example_path(root: Path) -> Path:
    """Locate the bundled example configuration in source and PyInstaller builds."""
    candidates = [root / "config" / "example.json"]
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.insert(0, Path(meipass) / "config" / "example.json")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


def _log_uncaught_exception(exc_type, exc_value, exc_traceback) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    LOGGER.critical("Unhandled AndroidNova exception", exc_info=(exc_type, exc_value, exc_traceback))
    try:
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    except Exception:
        pass


ROOT = application_root()
CONFIG_DIR = ROOT / "config"
CONFIG_PATH = CONFIG_DIR / "local.json"
sys.excepthook = _log_uncaught_exception


def ensure_config() -> Path:
    if CONFIG_PATH.exists():
        LOGGER.info("Using configuration: %s", CONFIG_PATH)
        return CONFIG_PATH
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    example_path = bundled_example_path(ROOT)
    if not example_path.is_file():
        raise FileNotFoundError(f"Bundled example configuration not found: {example_path}")
    data = json.loads(example_path.read_text(encoding="utf-8"))
    CONFIG_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    LOGGER.info("Created configuration from bundled example: %s", CONFIG_PATH)
    return CONFIG_PATH


def main() -> None:
    LOGGER.info("AndroidNova startup: root=%s frozen=%s", ROOT, getattr(sys, "frozen", False))
    config_path = ensure_config()
    load_config(config_path)
    root = create_window(config_path, ROOT)
    LOGGER.info("Tkinter window created successfully")
    root.mainloop()


if __name__ == "__main__":
    main()
