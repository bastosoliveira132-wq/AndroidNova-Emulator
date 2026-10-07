import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from androidnova.config.manager import AppConfig, PathConfig, QEMUConfig, VMConfig
from androidnova.qemu.manager import QEMUManager, QEMUError, resolve_qemu_executable


def write_test_iso(path: Path) -> None:
    data = bytearray(0x8001 + 5)
    data[0x8001:0x8006] = b"CD001"
    path.write_bytes(data)


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
            write_test_iso(iso)
            config = self.make_config(iso)
            command = QEMUManager(config).build_command()
            self.assertIn("-cdrom", command)
            self.assertIn(str(iso.resolve()), command)
            self.assertIn("-boot", command)
            self.assertIn("order=d", command)
            self.assertTrue(any("hostfwd=tcp:127.0.0.1:5555-:5555" in arg for arg in command))
            self.assertIn("-serial", command)

    def test_disk_media_uses_configured_format(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            disk = Path(directory) / "android.qcow2"
            disk.write_bytes(b"test")
            config = self.make_config(disk)
            command = QEMUManager(config).build_command()
            self.assertTrue(any(f"file={disk.resolve()},format=qcow2,if=virtio" == arg for arg in command))

    def test_missing_media_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.iso"
            manager = QEMUManager(self.make_config(missing))
            with self.assertRaises(QEMUError):
                manager.validate_media()

    def test_empty_media_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            iso = Path(directory) / "empty.iso"
            iso.write_bytes(b"")
            with self.assertRaisesRegex(QEMUError, "vazia"):
                QEMUManager(self.make_config(iso)).validate_media()

    def test_invalid_iso_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            iso = Path(directory) / "invalid.iso"
            iso.write_bytes(b"not an iso")
            with self.assertRaisesRegex(QEMUError, "inválida"):
                QEMUManager(self.make_config(iso)).validate_media()

    def test_custom_adb_port_is_forwarded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            iso = Path(directory) / "android.iso"
            write_test_iso(iso)
            config = self.make_config(iso)
            config.adb.port = 4444
            command = QEMUManager(config).build_command()
            self.assertTrue(any("hostfwd=tcp:127.0.0.1:4444-:4444" in arg for arg in command))

    def test_installer_is_not_accepted_as_qemu(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            installer = Path(directory) / "qemu-w64-setup-20260729.exe"
            installer.write_bytes(b"installer")
            with patch("androidnova.qemu.manager.shutil.which", return_value=None):
                self.assertIsNone(resolve_qemu_executable(str(installer)))

    def test_qemu_system_executable_is_selected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "qemu-system-x86_64.exe"
            executable.write_bytes(b"fake")
            completed = subprocess.CompletedProcess([str(executable), "--version"], 0, "QEMU 11", "")
            with patch("androidnova.qemu.manager.subprocess.run", return_value=completed):
                self.assertEqual(resolve_qemu_executable(str(executable)), executable.resolve())


if __name__ == "__main__":
    unittest.main()
