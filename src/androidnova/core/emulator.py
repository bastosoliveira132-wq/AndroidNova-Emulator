"""High-level emulator lifecycle orchestration and state reporting."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from androidnova.adb.manager import ADBError, ADBManager
from androidnova.config.manager import AppConfig, load_config, save_config
from androidnova.qemu.manager import QEMUManager


@dataclass(frozen=True)
class EmulatorStatus:
    qemu: str
    android: str
    adb: str


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
        self.logger.info("QEMU started; Android is now initializing")

    def stop(self) -> None:
        self.qemu.stop()
        self.logger.info("AndroidNova stopped")

    def restart(self) -> None:
        self.logger.info("Restarting AndroidNova")
        self.qemu.restart()
        self.logger.info("QEMU restarted; Android is now initializing")

    def is_running(self) -> bool:
        return self.qemu.is_running()

    def status(self) -> EmulatorStatus:
        if not self.qemu.is_running():
            return EmulatorStatus("parado", "não iniciado", "desconectado")
        try:
            devices = self.adb.devices_with_state()
        except ADBError:
            return EmulatorStatus("executando", "inicializando", "indisponível")

        target = f"{self.config.adb.host}:{self.config.adb.port}"
        state = devices.get(target)
        if state == "device":
            try:
                ready = self.adb.boot_completed(target)
            except ADBError:
                ready = False
            if ready:
                return EmulatorStatus("executando", "pronto", "conectado")
            return EmulatorStatus("executando", "inicializando", "conectando")
        if state:
            return EmulatorStatus("executando", "inicializando", f"{state}")
        return EmulatorStatus("executando", "inicializando", "desconectado")

    def connect_adb(self) -> str:
        self.adb.start_server()
        return self.adb.connect()

    def wait_for_android(self) -> str:
        return self.adb.wait_for_ready()

    def install_apk(self, apk_path: str) -> str:
        return self.adb.install_apk(apk_path)
