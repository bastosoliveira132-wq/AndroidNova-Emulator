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
    android_image: str = "images/android.qcow2"


@dataclass
class QEMUConfig:
    machine: str = "q35"
    acceleration: bool = True
    display_backend: str = "sdl"
    extra_args: list[str] = field(default_factory=list)


@dataclass
class ADBConfig:
    host: str = "127.0.0.1"
    port: int = 5555


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
        if self.adb.port < 1 or self.adb.port > 65535:
            raise ValueError("ADB port must be between 1 and 65535")
        if "x" not in self.vm.resolution.lower():
            raise ValueError("resolution must use WIDTHxHEIGHT format")


def load_config(path: Path) -> AppConfig:
    with path.open("r", encoding="utf-8") as handle:
        return AppConfig.from_dict(json.load(handle))


def save_config(config: AppConfig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(config.to_dict(), handle, indent=2)
        handle.write("\n")
