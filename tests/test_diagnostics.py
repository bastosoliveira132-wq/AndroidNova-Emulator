"""Host-side tests for Windows dependency and guest-media detection."""

from pathlib import Path
import tempfile
import unittest

from androidnova.config.manager import AppConfig
from androidnova.diagnostics import detect_guest_media


def write_test_iso(path: Path) -> None:
    data = bytearray(0x8001 + 5)
    data[0x8001:0x8006] = b"CD001"
    path.write_bytes(data)


class DiagnosticsTests(unittest.TestCase):
    def test_detects_configured_iso_relative_to_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            image = root / "images" / "android-x86_64.iso"
            image.parent.mkdir()
            write_test_iso(image)
            config = AppConfig()
            config.paths.android_image = "images/android-x86_64.iso"
            status = detect_guest_media(config, root)
            self.assertTrue(status.found)
            self.assertEqual(status.kind, "ISO")
            self.assertEqual(Path(status.path), image.resolve())

    def test_empty_iso_is_not_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            image = root / "android.iso"
            image.write_bytes(b"")
            config = AppConfig()
            config.paths.android_image = str(image)
            status = detect_guest_media(config, root)
            self.assertFalse(status.found)
            self.assertIn("vazia", status.message)

    def test_invalid_iso_is_not_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            image = root / "android.iso"
            image.write_bytes(b"not an ISO")
            config = AppConfig()
            config.paths.android_image = str(image)
            status = detect_guest_media(config, root)
            self.assertFalse(status.found)
            self.assertIn("inválida", status.message)

    def test_missing_guest_media_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            config = AppConfig()
            status = detect_guest_media(config, Path(temp))
            self.assertFalse(status.found)
            self.assertIsNone(status.path)


if __name__ == "__main__":
    unittest.main()
