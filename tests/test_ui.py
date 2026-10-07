"""Tkinter smoke tests for the desktop launcher and main window."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from androidnova.config.manager import AppConfig, save_config
from androidnova.ui.main_window import create_window


@unittest.skipIf(os.environ.get("CI") == "true" and sys.platform != "win32", "Tk display is not guaranteed on non-Windows CI")
class MainWindowSmokeTests(unittest.TestCase):
    def test_main_window_opens_and_builds(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root_dir = Path(directory)
            config_path = root_dir / "config.json"
            save_config(AppConfig(), config_path)
            root = create_window(config_path, root_dir)
            try:
                root.update_idletasks()
                root.update()
                self.assertEqual(root.title(), "AndroidNova Emulator")
            finally:
                root.destroy()


if __name__ == "__main__":
    unittest.main()
