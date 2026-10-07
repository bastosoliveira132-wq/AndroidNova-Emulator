"""ADB discovery and Android guest communication."""

from __future__ import annotations

import shutil
import subprocess
import time
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

    def start_server(self) -> str:
        return self._run("start-server").stdout.strip()

    def devices_with_state(self) -> dict[str, str]:
        result = self._run("devices")
        devices: dict[str, str] = {}
        for line in result.stdout.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2:
                devices[parts[0]] = parts[1]
        return devices

    def devices(self) -> list[str]:
        return [serial for serial, state in self.devices_with_state().items() if state == "device"]

    def connect(self) -> str:
        target = f"{self.config.adb.host}:{self.config.adb.port}"
        return self._run("connect", target).stdout.strip()

    def boot_completed(self, serial: str) -> bool:
        result = self._run("-s", serial, "shell", "getprop", "sys.boot_completed")
        return result.stdout.strip() == "1"

    def wait_for_ready(self) -> str:
        """Connect and wait until an online Android device reports boot completed."""
        self.start_server()
        deadline = time.monotonic() + self.config.adb.connect_timeout_seconds
        last_error = "ADB device not available"
        while time.monotonic() < deadline:
            try:
                self.connect()
                devices = self.devices_with_state()
                target = f"{self.config.adb.host}:{self.config.adb.port}"
                state = devices.get(target)
                if state == "device" and self.boot_completed(target):
                    return target
                if state:
                    last_error = f"ADB device state: {state}"
            except (ADBError, subprocess.TimeoutExpired) as exc:
                last_error = str(exc)
            time.sleep(self.config.adb.poll_interval_seconds)
        raise ADBError(last_error)

    def install_apk(self, apk_path: str) -> str:
        path = Path(apk_path)
        if not path.is_file():
            raise ADBError(f"APK not found: {path}")
        devices = self.devices()
        if not devices:
            raise ADBError("No online ADB device is connected")
        return self._run("-s", devices[0], "install", "-r", str(path), timeout=120).stdout.strip()
