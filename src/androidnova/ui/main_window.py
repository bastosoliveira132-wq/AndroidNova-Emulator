"""Tkinter desktop interface for AndroidNova."""

from __future__ import annotations

import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from androidnova.core.emulator import EmulatorCore
from androidnova.diagnostics import detect_environment
from androidnova.qemu.manager import QEMUError
from androidnova.ui.setup_wizard import SetupWizard


class MainWindow:
    def __init__(self, root: tk.Tk, core: EmulatorCore, config_path: Path, project_root: Path) -> None:
        self.root = root
        self.core = core
        self.config_path = config_path
        self.project_root = project_root
        self.root.title("AndroidNova Emulator")
        self.root.geometry("760x680")
        self.root.minsize(700, 620)
        self.status = tk.StringVar()
        self.environment = tk.StringVar(value="Verificando ambiente...")
        self._build()
        self._refresh_status()
        self.root.after(50, self._refresh_environment)

    def _build(self) -> None:
        frame = tk.Frame(self.root, padx=18, pady=18)
        frame.pack(fill="both", expand=True)
        tk.Label(frame, text="AndroidNova Emulator", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        tk.Label(frame, text="QEMU + Android x86_64 + ADB", font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 10))

        env = tk.LabelFrame(frame, text="Ambiente Windows", padx=12, pady=10)
        env.pack(fill="x")
        tk.Label(env, textvariable=self.environment, justify="left", anchor="w", wraplength=700).pack(fill="x")
        env_buttons = tk.Frame(env)
        env_buttons.pack(fill="x", pady=(8, 0))
        tk.Button(env_buttons, text="Configurar / procurar componentes", command=self._open_setup).pack(side="left")
        tk.Button(env_buttons, text="Verificar", command=self._refresh_environment).pack(side="left", padx=8)

        settings = tk.LabelFrame(frame, text="VM configuration", padx=12, pady=10)
        settings.pack(fill="x", pady=(12, 0))
        self._field(settings, "RAM (MB)", str(self.core.config.vm.ram_mb), 0, self._set_ram)
        self._field(settings, "CPU cores", str(self.core.config.vm.cpu_count), 1, self._set_cpu)
        self._field(settings, "Resolution", self.core.config.vm.resolution, 2, self._set_resolution)
        self._field(settings, "Android media", self.core.config.paths.android_image, 3, self._set_image)
        self._field(settings, "ADB port", str(self.core.config.adb.port), 4, self._set_adb_port)

        controls = tk.Frame(frame, pady=14)
        controls.pack(fill="x")
        tk.Button(controls, text="Start", width=12, command=self._start).pack(side="left", padx=(0, 6))
        tk.Button(controls, text="Restart", width=12, command=self._restart).pack(side="left", padx=6)
        tk.Button(controls, text="Shutdown", width=12, command=self._stop).pack(side="left", padx=6)
        tk.Button(controls, text="Connect ADB", width=12, command=self._connect_adb).pack(side="left", padx=6)
        tk.Button(controls, text="Install APK", width=12, command=self._install_apk).pack(side="left", padx=6)

        status_box = tk.LabelFrame(frame, text="Runtime status", padx=12, pady=10)
        status_box.pack(fill="x")
        tk.Label(status_box, textvariable=self.status, justify="left", font=("Segoe UI", 11, "bold"), anchor="w").pack(fill="x")
        tk.Label(
            frame,
            text="O primeiro boot real exige uma imagem Android x86_64 fornecida pelo usuário e QEMU/ADB instalados. O AndroidNova não baixa nem redistribui a imagem.",
            wraplength=700, justify="left",
        ).pack(anchor="w", pady=(12, 0))

    def _field(self, parent: tk.Widget, label: str, value: str, row: int, callback) -> None:
        tk.Label(parent, text=label, width=16, anchor="w").grid(row=row, column=0, sticky="w", pady=3)
        entry = tk.Entry(parent, width=54)
        entry.insert(0, value)
        entry.grid(row=row, column=1, sticky="ew", pady=3)
        tk.Button(parent, text="Apply", command=lambda: callback(entry.get())).grid(row=row, column=2, padx=8)
        parent.grid_columnconfigure(1, weight=1)

    def _persist(self) -> None:
        try:
            self.core.save(self.config_path)
        except (ValueError, OSError) as exc:
            raise RuntimeError(f"Não foi possível salvar a configuração: {exc}") from exc

    def _apply(self, setter, value: str, title: str) -> None:
        try:
            setter(value)
            self.core.config.validate()
            self._persist()
            self._refresh_environment()
        except (ValueError, TypeError, RuntimeError) as exc:
            messagebox.showerror(title, str(exc))

    def _set_ram(self, value: str) -> None:
        self._apply(lambda v: setattr(self.core.config.vm, "ram_mb", int(v)), value, "Invalid RAM")

    def _set_cpu(self, value: str) -> None:
        self._apply(lambda v: setattr(self.core.config.vm, "cpu_count", int(v)), value, "Invalid CPU")

    def _set_resolution(self, value: str) -> None:
        self._apply(lambda v: setattr(self.core.config.vm, "resolution", v), value, "Invalid resolution")

    def _set_image(self, value: str) -> None:
        self._apply(lambda v: setattr(self.core.config.paths, "android_image", v.strip()), value, "Invalid Android image")

    def _set_adb_port(self, value: str) -> None:
        self._apply(lambda v: setattr(self.core.config.adb, "port", int(v)), value, "Invalid ADB port")

    def _open_setup(self) -> None:
        SetupWizard(self.root, self.core.config, self.config_path, self.project_root, self._refresh_environment)

    def _refresh_environment(self) -> None:
        try:
            status = detect_environment(self.core.config, self.project_root)
            qemu = (
                f"[OK] QEMU — {status.qemu.message}\n    Caminho: {status.qemu.path}"
                if status.qemu.found else f"[FALTA] QEMU — {status.qemu.message}"
            )
            adb = (
                f"[OK] ADB — {status.adb.message}\n    Caminho: {status.adb.path}"
                if status.adb.found else f"[FALTA] ADB — {status.adb.message}"
            )
            guest = (
                f"[OK] Imagem Android — {status.guest.message}\n    Caminho: {status.guest.path}"
                if status.guest.found else f"[FALTA] Imagem Android — {status.guest.message}"
            )
            self.environment.set(f"{qemu}\n\n{adb}\n\n{guest}\n\n[{'OK' if status.whpx else 'INFO'}] WHPX: {'detectado' if status.whpx else 'não confirmado'}")
        except Exception as exc:
            self.environment.set(f"Não foi possível verificar o ambiente: {exc}")

    def _start(self) -> None:
        try:
            self._persist()
            self._refresh_environment()
            self.core.start()
        except (QEMUError, OSError, ValueError, RuntimeError) as exc:
            messagebox.showerror("Falha ao iniciar AndroidNova", str(exc))
        except Exception as exc:
            messagebox.showerror("Falha inesperada ao iniciar", str(exc))

    def _restart(self) -> None:
        try:
            self._persist()
            self.core.restart()
        except Exception as exc:
            messagebox.showerror("Unable to restart", str(exc))

    def _stop(self) -> None:
        self.core.stop()

    def _connect_adb(self) -> None:
        try:
            result = self.core.connect_adb()
            messagebox.showinfo("ADB", result or "ADB connect command completed")
        except Exception as exc:
            messagebox.showerror("ADB connection", str(exc))

    def _install_apk(self) -> None:
        apk = filedialog.askopenfilename(filetypes=[("Android package", "*.apk"), ("All files", "*.*")])
        if not apk:
            return
        try:
            result = self.core.install_apk(apk)
            messagebox.showinfo("APK installation", result or "APK installed")
        except Exception as exc:
            messagebox.showerror("APK installation", str(exc))

    def _refresh_status(self) -> None:
        status = self.core.status()
        self.status.set(f"QEMU: {status.qemu}\nAndroid: {status.android}\nADB: {status.adb}")
        self.root.after(1000, self._refresh_status)


def create_window(config_path: Path, project_root: Path) -> tk.Tk:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    core = EmulatorCore.from_file(config_path)
    root = tk.Tk()
    MainWindow(root, core, config_path, project_root)
    return root
