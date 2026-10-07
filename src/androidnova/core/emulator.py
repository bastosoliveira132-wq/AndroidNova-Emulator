"""High-level emulator lifecycle orchestration."""

from __future__ import annotations

import logging
from pathlib import Path

from androidnova.adb.manager import ADBManager
from androidnova.config.manager import AppConfig, load_config, save_config
from androidnova.qemu.manager import QEMUManager


class EmulatorCore:
    def __init__(self, config: AppConfig, logger: logging.Logger | None = None) -> None:
        self.config = config
        self.logger = logger or logging.getLogger("androidnova")
        self.qemu = QEMUManager(config, self.logger.info)
        self.adb = ADBManager(config)

    @classmethod
    def from_file(cls, path: Path) -> "EmulatorCore":
        return cls(load_config(path))

    def save(self, path: Path) -> None:
        save_config(self.config, path)

    def start(self) -> None:
        self.logger.info("Starting AndroidNova")
        self.qemu.start()

    def stop(self) -> None:
        self.qemu.stop()
        self.logger.info("AndroidNova stopped")

    def restart(self) -> None:
        self.logger.info("Restarting AndroidNova")
        self.qemu.restart()

    def is_running(self) -> bool:
        return self.qemu.is_running()
