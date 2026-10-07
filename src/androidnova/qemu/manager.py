"""QEMU process management and command construction."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Callable

from androidnova.config.manager import AppConfig


class QEMUError(RuntimeError):
    """Raised when QEMU cannot be started or controlled."""


class QEMUManager:
    def __init__(self, config: AppConfig, logger: Callable[[str], None] | None = None) -> None:
        self.config = config
        self.logger = logger or (lambda message: None)
        self.process: subprocess.Popen[str] | None = None

    def executable(self) -> str | None:
        configured = self.config.paths.qemu
        if Path(configured).is_file():
            return str(Path(configured).resolve())
        return shutil.which(configured)

    def build_command(self) -> list[str]:
        executable = self.executable() or self.config.paths.qemu
        command = [
            executable,
            "-machine", self.config.qemu.machine,
            "-m", str(self.config.vm.ram_mb),
            "-smp", str(self.config.vm.cpu_count),
            "-drive", f"file={self.config.paths.android_image},format=qcow2,if=virtio",
            "-display", self.config.qemu.display_backend,
            "-netdev", "user,id=net0,hostfwd=tcp:127.0.0.1:5555-:5555",
            "-device", "virtio-net-pci,netdev=net0",
        ]
        if self.config.qemu.acceleration:
            command.extend(["-accel", "whpx"])
        if not self.config.vm.audio:
            command.append("-audiodev")
            command.append("none,id=audio0")
        command.extend(self.config.qemu.extra_args)
        return command

    def start(self) -> None:
        if self.is_running():
            raise QEMUError("QEMU is already running")
        executable = self.executable()
        if executable is None:
            raise QEMUError("QEMU executable was not found. Configure paths.qemu or add QEMU to PATH.")
        image = Path(self.config.paths.android_image)
        if not image.is_file():
            raise QEMUError(f"Android guest image not found: {image}")

        command = self.build_command()
        self.logger("Starting QEMU: " + " ".join(command))
        try:
            self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        except OSError as exc:
            raise QEMUError(f"Unable to start QEMU: {exc}") from exc

    def stop(self) -> None:
        if not self.process:
            return
        if self.process.poll() is None:
            self.logger("Stopping QEMU")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
        self.process = None

    def restart(self) -> None:
        self.stop()
        self.start()

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None
