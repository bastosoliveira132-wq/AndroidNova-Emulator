"""QEMU process management and command construction."""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
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
        self._output_thread: threading.Thread | None = None

    def executable(self) -> str | None:
        configured = self.config.paths.qemu
        if Path(configured).is_file():
            return str(Path(configured).resolve())
        return shutil.which(configured)

    def _media_type(self) -> str:
        configured = self.config.qemu.media_type
        if configured != "auto":
            return configured
        suffix = Path(self.config.paths.android_image).suffix.lower()
        return "iso" if suffix in {".iso", ".imgiso"} else "disk"

    def validate_media(self) -> Path:
        image = Path(self.config.paths.android_image)
        if not image.is_file():
            raise QEMUError(f"Android guest media not found: {image}")
        if not os.access(image, os.R_OK):
            raise QEMUError(f"Android guest media is not readable: {image}")
        if image.stat().st_size == 0:
            raise QEMUError(f"Android guest media is empty: {image}")
        return image

    def build_command(self) -> list[str]:
        executable = self.executable() or self.config.paths.qemu
        image = Path(self.config.paths.android_image)
        media_type = self._media_type()
        command = [
            executable,
            "-machine", self.config.qemu.machine,
            "-m", str(self.config.vm.ram_mb),
            "-smp", str(self.config.vm.cpu_count),
            "-display", self.config.qemu.display_backend,
            "-serial", f"file={self.config.paths.serial_log}",
        ]

        if media_type == "iso":
            command.extend(["-cdrom", str(image)])
        else:
            command.extend(["-drive", f"file={image},format={self.config.qemu.disk_format},if=virtio"])

        if self.config.vm.network:
            command.extend([
                "-netdev",
                f"user,id=net0,hostfwd=tcp:{self.config.adb.host}:{self.config.adb.port}-:{self.config.adb.port}",
                "-device",
                "virtio-net-pci,netdev=net0",
            ])

        if self.config.qemu.acceleration:
            command.extend(["-accel", self.config.qemu.accelerator])

        if self.config.vm.audio:
            if os.name == "nt":
                command.extend(["-audiodev", "dsound,id=audio0", "-device", "AC97,audiodev=audio0"])
            else:
                command.extend(["-audiodev", "sdl,id=audio0", "-device", "AC97,audiodev=audio0"])
        else:
            command.extend(["-audiodev", "none,id=audio0"])

        command.extend(self.config.qemu.extra_args)
        return command

    def _read_output(self) -> None:
        if not self.process or not self.process.stdout:
            return
        for line in self.process.stdout:
            text = line.rstrip()
            if text:
                self.logger("QEMU: " + text)

    def start(self) -> None:
        if self.is_running():
            raise QEMUError("QEMU is already running")
        executable = self.executable()
        if executable is None:
            raise QEMUError("QEMU executable was not found. Configure paths.qemu or add QEMU to PATH.")
        self.validate_media()

        serial_log = Path(self.config.paths.serial_log)
        serial_log.parent.mkdir(parents=True, exist_ok=True)
        command = self.build_command()
        self.logger("Starting QEMU: " + " ".join(command))
        try:
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except OSError as exc:
            raise QEMUError(f"Unable to start QEMU: {exc}") from exc
        self._output_thread = threading.Thread(target=self._read_output, name="androidnova-qemu-log", daemon=True)
        self._output_thread.start()

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

    def exit_code(self) -> int | None:
        return None if self.process is None else self.process.poll()
