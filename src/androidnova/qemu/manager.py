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


def _qemu_candidates(configured: str) -> list[Path]:
    """Return only real QEMU system executables, never installer packages."""
    candidates: list[Path] = []
    configured_path = Path(configured).expanduser()
    if configured_path.is_file():
        candidates.append(configured_path)
    resolved = shutil.which(configured)
    if resolved:
        candidates.append(Path(resolved))
    for name in ("qemu-system-x86_64.exe", "qemu-system-x86_64"):
        resolved = shutil.which(name)
        if resolved:
            candidates.append(Path(resolved))
    if os.name == "nt":
        program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        candidates.extend([
            program_files / "qemu" / "qemu-system-x86_64.exe",
            program_files / "QEMU" / "qemu-system-x86_64.exe",
        ])
    result: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        try:
            resolved_candidate = candidate.resolve()
        except OSError:
            continue
        if resolved_candidate.name.lower() not in {"qemu-system-x86_64.exe", "qemu-system-x86_64"}:
            continue
        key = str(resolved_candidate).lower()
        if key not in seen and resolved_candidate.is_file():
            seen.add(key)
            result.append(resolved_candidate)
    return result


def resolve_qemu_executable(configured: str) -> Path | None:
    """Find a usable qemu-system-x86_64 executable from config/PATH/defaults."""
    for candidate in _qemu_candidates(configured):
        try:
            result = subprocess.run(
                [str(candidate), "--version"], capture_output=True, text=True, timeout=5, check=False
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if result.returncode == 0 or result.stdout or result.stderr:
            return candidate
    return None


class QEMUManager:
    def __init__(self, config: AppConfig, logger: Callable[[str], None] | None = None, base_dir: Path | None = None) -> None:
        self.config = config
        self.logger = logger or (lambda message: None)
        self.base_dir = (base_dir or Path.cwd()).resolve()
        self.process: subprocess.Popen[str] | None = None
        self._output_thread: threading.Thread | None = None

    def _resolve_config_path(self, value: str) -> Path:
        path = Path(value).expanduser()
        return path if path.is_absolute() else self.base_dir / path

    def executable(self) -> str | None:
        resolved = resolve_qemu_executable(self.config.paths.qemu)
        return str(resolved) if resolved else None

    def media_path(self) -> Path:
        return self._resolve_config_path(self.config.paths.android_image).resolve()

    def serial_log_path(self) -> Path:
        return self._resolve_config_path(self.config.paths.serial_log).resolve()

    def _media_type(self) -> str:
        configured = self.config.qemu.media_type
        if configured != "auto":
            return configured
        return "iso" if self.media_path().suffix.lower() == ".iso" else "disk"

    def validate_media(self) -> Path:
        image = self.media_path()
        if not image.is_file():
            raise QEMUError(f"Imagem Android não encontrada: {image}")
        if not os.access(image, os.R_OK):
            raise QEMUError(f"Imagem Android não pode ser lida: {image}")
        try:
            size = image.stat().st_size
        except OSError as exc:
            raise QEMUError(f"Não foi possível acessar a imagem Android: {image} ({exc})") from exc
        if size == 0:
            raise QEMUError(f"Imagem Android está vazia: {image}")
        if image.suffix.lower() == ".iso":
            try:
                with image.open("rb") as handle:
                    handle.seek(0x8001)
                    signature = handle.read(5)
            except OSError as exc:
                raise QEMUError(f"Não foi possível validar a ISO Android: {image} ({exc})") from exc
            if signature != b"CD001":
                raise QEMUError(f"ISO Android inválida ou não reconhecida (assinatura ISO9660 ausente): {image}")
        return image

    def build_command(self) -> list[str]:
        # Command construction can be inspected before QEMU is installed. Actual
        # process start performs the strict executable check below.
        executable = self.executable() or self.config.paths.qemu
        image = self.validate_media()
        media_type = self._media_type()
        command = [
            executable,
            "-machine", self.config.qemu.machine,
            "-m", str(self.config.vm.ram_mb),
            "-smp", str(self.config.vm.cpu_count),
            "-display", self.config.qemu.display_backend,
            "-serial", f"file={self.serial_log_path()}",
        ]
        if media_type == "iso":
            command.extend(["-cdrom", str(image), "-boot", "order=d"])
        else:
            command.extend(["-drive", f"file={image},format={self.config.qemu.disk_format},if=virtio"])
        if self.config.vm.network:
            command.extend([
                "-netdev",
                f"user,id=net0,hostfwd=tcp:{self.config.adb.host}:{self.config.adb.port}-:{self.config.adb.port}",
                "-device", "virtio-net-pci,netdev=net0",
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
            raise QEMUError(
                "QEMU não encontrado. Configure qemu-system-x86_64.exe; "
                "o instalador qemu-w64-setup-*.exe não pode iniciar a VM."
            )
        self.validate_media()
        serial_log = self.serial_log_path()
        serial_log.parent.mkdir(parents=True, exist_ok=True)
        command = self.build_command()
        self.logger("Starting QEMU: " + " ".join(command))
        try:
            self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        except OSError as exc:
            raise QEMUError(f"Falha ao iniciar o QEMU: {exc}") from exc
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
