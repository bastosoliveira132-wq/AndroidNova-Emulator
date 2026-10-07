"""AndroidNova application entry point."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from androidnova.config.manager import load_config, save_config
from androidnova.ui.main_window import create_window

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"
CONFIG_PATH = CONFIG_DIR / "local.json"
EXAMPLE_PATH = CONFIG_DIR / "example.json"


def ensure_config() -> Path:
    if CONFIG_PATH.exists():
        return CONFIG_PATH
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
    CONFIG_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return CONFIG_PATH


def main() -> None:
    config_path = ensure_config()
    load_config(config_path)
    root = create_window(config_path)
    root.mainloop()


if __name__ == "__main__":
    main()
