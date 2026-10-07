import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from androidnova.config.manager import AppConfig, load_config, save_config


class ConfigTests(unittest.TestCase):
    def test_round_trip(self) -> None:
        config = AppConfig()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            save_config(config, path)
            loaded = load_config(path)
            self.assertEqual(loaded.to_dict(), config.to_dict())

    def test_round_trip_preserves_vm_paths_and_adb(self) -> None:
        config = AppConfig()
        config.paths.qemu = r"C:\Program Files\qemu\qemu-system-x86_64.exe"
        config.paths.adb = r"C:\Android\platform-tools\adb.exe"
        config.paths.android_image = r"C:\Users\gabriel\Downloads\android-x86_64-9.0-r2.iso"
        config.vm.ram_mb = 6144
        config.vm.cpu_count = 6
        config.vm.resolution = "1920x1080"
        config.vm.audio = False
        config.vm.network = True
        config.adb.port = 5557
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            save_config(config, path)
            loaded = load_config(path)
            self.assertEqual(loaded.paths.qemu, config.paths.qemu)
            self.assertEqual(loaded.paths.adb, config.paths.adb)
            self.assertEqual(loaded.paths.android_image, config.paths.android_image)
            self.assertEqual(loaded.vm.ram_mb, 6144)
            self.assertEqual(loaded.vm.cpu_count, 6)
            self.assertEqual(loaded.vm.resolution, "1920x1080")
            self.assertFalse(loaded.vm.audio)
            self.assertTrue(loaded.vm.network)
            self.assertEqual(loaded.adb.port, 5557)

    def test_validation_rejects_invalid_ram(self) -> None:
        with self.assertRaises(ValueError):
            AppConfig.from_dict({"vm": {"ram_mb": 128}})

    def test_json_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            save_config(AppConfig(), path)
            json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
