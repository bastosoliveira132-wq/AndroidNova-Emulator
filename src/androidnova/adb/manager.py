"""ADB discovery and guest communication."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from androidnova.config.manager import AppConfig


class ADBError(RuntimeError):
    """Raised when an ADB operation fails."""


class ADBManager:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def executable(self) -> str | None:
        configured = self.config.paths.adb
        if Path(configured).is_file():
            return str(Path(configured).resolve())
        return shutil.which(configured)

    def _run(self, *args: str, timeout: int = 10) -> subprocess.CompletedProcess[str]:
        executable = self.executable()
        if executable is None:
            raise ADBError("ADB executable was not found. Configure paths.adb or add adb to PATH.")
        result = subprocess.run(
            [executable, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode != 0:
            raise ADBError(result.stderr.strip() or result.stdout.strip() or "ADB command failed")
        return result

    def version(self) -> str:
        return self._run("version").stdout.strip()

    def devices(self) -> list[str]:
        result = self._run("devices")
        devices: list[str] = []
        for line in result.stdout.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                devices.append(parts[0])
        return devices

    def connect(self) -> str:
        target = f"{self.config.adb.host}:{self.config.adb.port}"
        return self._run("connect", target).stdout.strip()

    def install_apk(self, apk_path: str) -> str:
        path = Path(apk_path)
        if not path.is_file():
            raise ADBError(f"APK not found: {path}")
        return self._run("install", "-r", str(path), timeout=60).stdout.strip()
