"""Host-side tests for Windows dependency and guest-media detection."""

from pathlib import Path
import tempfile
import unittest

from androidnova.config.manager import AppConfig
from androidnova.diagnostics import detect_guest_media


class DiagnosticsTests(unittest.TestCase):
    def test_detects_configured_iso_relative_to_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            image = root / "images" / "android-x86_64.iso"
            image.parent.mkdir()
            image.write_bytes(b"android x86_64 test media")
            config = AppConfig()
            config.paths.android_image = "images/android-x86_64.iso"
            status = detect_guest_media(config, root)
            self.assertTrue(status.found)
            self.assertEqual(status.kind, "ISO")
            self.assertEqual(Path(status.path), image.resolve())

    def test_missing_guest_media_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            config = AppConfig()
            status = detect_guest_media(config, Path(temp))
            self.assertFalse(status.found)
            self.assertIsNone(status.path)


if __name__ == "__main__":
    unittest.main()
