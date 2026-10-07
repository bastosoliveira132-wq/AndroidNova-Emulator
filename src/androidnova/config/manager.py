"""JSON configuration loading and validation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class VMConfig:
    ram_mb: int = 4096
    cpu_count: int = 4
    resolution: str = "1280x720"
    audio: bool = True
    network: bool = True


@dataclass
class PathConfig:
    qemu: str = "qemu-system-x86_64"
    adb: str = "adb"
    android_image: str = "images/android-x86_64.iso"
    serial_log: str = "logs/qemu-serial.log"


@dataclass
class QEMUConfig:
    machine: str = "q35"
    acceleration: bool = True
    accelerator: str = "whpx"
    display_backend: str = "sdl"
    media_type: str = "auto"
    extra_args: list[str] = field(default_factory=list)


@dataclass
class ADBConfig:
    host: str = "127.0.0.1"
    port: int = 5555
    connect_timeout_seconds: int = 90
    poll_interval_seconds: float = 2.0


@dataclass
class AppConfig:
    vm: VMConfig = field(default_factory=VMConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    qemu: QEMUConfig = field(default_factory=QEMUConfig)
    adb: ADBConfig = field(default_factory=ADBConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        config = cls(
            vm=VMConfig(**data.get("vm", {})),
            paths=PathConfig(**data.get("paths", {})),
            qemu=QEMUConfig(**data.get("qemu", {})),
            adb=ADBConfig(**data.get("adb", {})),
        )
        config.validate()
        return config

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def validate(self) -> None:
        if self.vm.ram_mb < 512:
            raise ValueError("ram_mb must be at least 512")
        if self.vm.cpu_count < 1:
            raise ValueError("cpu_count must be at least 1")
        width, height = self.resolution_size()
        if width < 320 or height < 240:
            raise ValueError("resolution must be at least 320x240")
        if self.adb.port < 1 or self.adb.port > 65535:
            raise ValueError("ADB port must be between 1 and 65535")
        if self.adb.connect_timeout_seconds < 1:
            raise ValueError("ADB connect timeout must be at least 1 second")
        if self.adb.poll_interval_seconds <= 0:
            raise ValueError("ADB poll interval must be greater than zero")
        if self.qemu.media_type not in {"auto", "iso", "disk"}:
            raise ValueError("qemu.media_type must be auto, iso, or disk")

    def resolution_size(self) -> tuple[int, int]:
        value = self.vm.resolution.lower().replace(" ", "")
        parts = value.split("x")
        if len(parts) != 2:
            raise ValueError("resolution must use WIDTHxHEIGHT format")
        try:
            return int(parts[0]), int(parts[1])
        except ValueError as exc:
            raise ValueError("resolution must use numeric WIDTHxHEIGHT format") from exc


def load_config(path: Path) -> AppConfig:
    with path.open("r", encoding="utf-8") as handle:
        return AppConfig.from_dict(json.load(handle))


def save_config(config: AppConfig, path: Path) -> None:
    config.validate()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(config.to_dict(), handle, indent=2)
        handle.write("\n")
