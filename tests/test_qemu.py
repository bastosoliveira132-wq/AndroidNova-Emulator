import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from androidnova.config.manager import AppConfig, PathConfig, QEMUConfig, VMConfig
from androidnova.qemu.manager import QEMUManager, QEMUError


class QEMUCommandTests(unittest.TestCase):
    def make_config(self, media: Path) -> AppConfig:
        return AppConfig(
            vm=VMConfig(ram_mb=4096, cpu_count=4, audio=False, network=True),
            paths=PathConfig(android_image=str(media), serial_log=str(media.parent / "qemu.log")),
            qemu=QEMUConfig(acceleration=False, media_type="auto"),
        )

    def test_iso_media_uses_cdrom_and_adb_forward(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            iso = Path(directory) / "android-x86_64.iso"
            iso.write_bytes(b"test")
            config = self.make_config(iso)
            command = QEMUManager(config).build_command()
            self.assertIn("-cdrom", command)
            self.assertIn(str(iso), command)
            self.assertTrue(any("hostfwd=tcp:127.0.0.1:5555-:5555" in arg for arg in command))
            self.assertIn("-serial", command)

    def test_disk_media_uses_configured_format(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            disk = Path(directory) / "android.qcow2"
            disk.write_bytes(b"test")
            config = self.make_config(disk)
            command = QEMUManager(config).build_command()
            self.assertTrue(any(f"file={disk},format=qcow2,if=virtio" == arg for arg in command))

    def test_missing_media_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.iso"
            manager = QEMUManager(self.make_config(missing))
            with self.assertRaises(QEMUError):
                manager.validate_media()

    def test_custom_adb_port_is_forwarded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            iso = Path(directory) / "android.iso"
            iso.write_bytes(b"test")
            config = self.make_config(iso)
            config.adb.port = 4444
            command = QEMUManager(config).build_command()
            self.assertTrue(any("hostfwd=tcp:127.0.0.1:4444-:4444" in arg for arg in command))


if __name__ == "__main__":
    unittest.main()
