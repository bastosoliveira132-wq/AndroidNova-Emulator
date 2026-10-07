"""Tkinter desktop interface for AndroidNova."""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

from androidnova.config.manager import AppConfig
from androidnova.core.emulator import EmulatorCore


class MainWindow:
    def __init__(self, root: tk.Tk, core: EmulatorCore) -> None:
        self.root = root
        self.core = core
        self.root.title("AndroidNova Emulator")
        self.root.geometry("560x420")
        self.root.minsize(520, 360)
        self.status = tk.StringVar(value="Stopped")
        self._build()

    def _build(self) -> None:
        frame = tk.Frame(self.root, padx=18, pady=18)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="AndroidNova Emulator", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        tk.Label(frame, text="QEMU + ADB control plane", font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 16))

        settings = tk.LabelFrame(frame, text="VM configuration", padx=12, pady=10)
        settings.pack(fill="x")
        self._field(settings, "RAM (MB)", str(self.core.config.vm.ram_mb), 0, self._set_ram)
        self._field(settings, "CPU cores", str(self.core.config.vm.cpu_count), 1, self._set_cpu)
        self._field(settings, "Resolution", self.core.config.vm.resolution, 2, self._set_resolution)

        controls = tk.Frame(frame, pady=16)
        controls.pack(fill="x")
        tk.Button(controls, text="Start", width=12, command=self._start).pack(side="left", padx=(0, 8))
        tk.Button(controls, text="Restart", width=12, command=self._restart).pack(side="left", padx=8)
        tk.Button(controls, text="Shutdown", width=12, command=self._stop).pack(side="left", padx=8)

        tk.Label(frame, text="Status:").pack(anchor="w")
        tk.Label(frame, textvariable=self.status, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(frame, text="Android image, QEMU and ADB are external prerequisites for a real boot.", wraplength=500).pack(anchor="w", pady=(12, 0))

    def _field(self, parent: tk.Widget, label: str, value: str, row: int, callback) -> None:
        tk.Label(parent, text=label, width=14, anchor="w").grid(row=row, column=0, sticky="w", pady=3)
        entry = tk.Entry(parent, width=24)
        entry.insert(0, value)
        entry.grid(row=row, column=1, sticky="w", pady=3)
        tk.Button(parent, text="Apply", command=lambda: callback(entry.get())).grid(row=row, column=2, padx=8)

    def _set_ram(self, value: str) -> None:
        try:
            self.core.config.vm.ram_mb = int(value)
            self.core.config.validate()
        except ValueError as exc:
            messagebox.showerror("Invalid RAM", str(exc))

    def _set_cpu(self, value: str) -> None:
        try:
            self.core.config.vm.cpu_count = int(value)
            self.core.config.validate()
        except ValueError as exc:
            messagebox.showerror("Invalid CPU", str(exc))

    def _set_resolution(self, value: str) -> None:
        self.core.config.vm.resolution = value
        try:
            self.core.config.validate()
        except ValueError as exc:
            messagebox.showerror("Invalid resolution", str(exc))

    def _start(self) -> None:
        try:
            self.core.start()
            self.status.set("Running")
        except Exception as exc:
            self.status.set("Error")
            messagebox.showerror("Unable to start", str(exc))

    def _restart(self) -> None:
        try:
            self.core.restart()
            self.status.set("Running")
        except Exception as exc:
            self.status.set("Error")
            messagebox.showerror("Unable to restart", str(exc))

    def _stop(self) -> None:
        self.core.stop()
        self.status.set("Stopped")


def create_window(config_path: Path) -> tk.Tk:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    core = EmulatorCore.from_file(config_path)
    root = tk.Tk()
    MainWindow(root, core)
    return root
