"""Windows dependency and guest-media setup assistant."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from androidnova.config.manager import AppConfig, save_config
from androidnova.diagnostics import EnvironmentStatus, detect_environment


class SetupWizard:
    def __init__(self, parent: tk.Tk, config: AppConfig, config_path: Path, project_root: Path, on_saved) -> None:
        self.config = config
        self.config_path = config_path
        self.project_root = project_root
        self.on_saved = on_saved
        self.window = tk.Toplevel(parent)
        self.window.title("AndroidNova — Configuração do ambiente")
        self.window.geometry("760x620")
        self.window.minsize(700, 560)
        self._build()
        self.refresh()

    def _build(self) -> None:
        frame = tk.Frame(self.window, padx=18, pady=18)
        frame.pack(fill="both", expand=True)
        tk.Label(frame, text="Assistente de configuração", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        tk.Label(
            frame,
            text="O AndroidNova não baixa nem redistribui QEMU, ADB ou imagens Android. Indique os componentes instalados no seu computador.",
            wraplength=700,
            justify="left",
        ).pack(anchor="w", pady=(4, 16))

        self.rows: dict[str, tuple[tk.Label, tk.Entry]] = {}
        self._path_row(frame, "QEMU", "qemu", 0, "qemu-system-x86_64.exe")
        self._path_row(frame, "ADB", "adb", 1, "adb.exe")
        self._path_row(frame, "Imagem Android x86_64", "android_image", 2, "*.iso *.img *.qcow2")

        self.status_box = tk.LabelFrame(frame, text="Detecção automática", padx=12, pady=10)
        self.status_box.pack(fill="both", expand=True, pady=(18, 12))
        self.status_text = tk.StringVar(value="Verificando...")
        tk.Label(self.status_box, textvariable=self.status_text, justify="left", anchor="nw", wraplength=690).pack(fill="both", expand=True)

        buttons = tk.Frame(frame)
        buttons.pack(fill="x")
        tk.Button(buttons, text="Verificar novamente", command=self.refresh).pack(side="left")
        tk.Button(buttons, text="Salvar configuração", command=self.save).pack(side="right")

    def _path_row(self, parent: tk.Widget, label: str, key: str, row: int, filetypes: str) -> None:
        tk.Label(parent, text=label, width=24, anchor="w").pack(anchor="w")
        line = tk.Frame(parent)
        line.pack(fill="x", pady=(2, 10))
        current = getattr(self.config.paths, key)
        entry = tk.Entry(line)
        entry.insert(0, current)
        entry.pack(side="left", fill="x", expand=True)
        tk.Button(line, text="Procurar...", command=lambda k=key: self.browse(k)).pack(side="left", padx=(8, 0))
        self.rows[key] = (tk.Label(line, text="", width=12, anchor="e"), entry)
        self.rows[key][0].pack(side="right", padx=(8, 0))

    def browse(self, key: str) -> None:
        if key == "android_image":
            path = filedialog.askopenfilename(
                title="Selecione sua imagem Android x86_64",
                filetypes=[("Imagens Android/VM", "*.iso *.img *.raw *.qcow2 *.vmdk *.vdi *.vhd *.vhdx"), ("Todos os arquivos", "*.*")],
            )
        else:
            filename = "qemu-system-x86_64.exe" if key == "qemu" else "adb.exe"
            path = filedialog.askopenfilename(title=f"Selecione {filename}", filetypes=[("Executável", "*.exe"), ("Todos os arquivos", "*.*")])
        if path:
            self.rows[key][1].delete(0, tk.END)
            self.rows[key][1].insert(0, path)
            self.refresh()

    def _apply_paths(self) -> None:
        self.config.paths.qemu = self.rows["qemu"][1].get().strip() or "qemu-system-x86_64"
        self.config.paths.adb = self.rows["adb"][1].get().strip() or "adb"
        self.config.paths.android_image = self.rows["android_image"][1].get().strip() or "images/android-x86_64.iso"

    def refresh(self) -> None:
        self._apply_paths()
        status = detect_environment(self.config, self.project_root)
        self._render(status)

    def _render(self, status: EnvironmentStatus) -> None:
        def line(ok: bool, title: str, message: str, path: str | None, version: str | None = None) -> str:
            icon = "OK" if ok else "FALTA"
            detail = f" — {message}"
            if path:
                detail += f"\n    Caminho: {path}"
            if version:
                detail += f"\n    Versão: {version}"
            return f"[{icon}] {title}{detail}"

        text = "\n\n".join([
            line(status.qemu.found, "QEMU", status.qemu.message, status.qemu.path, status.qemu.version),
            line(status.adb.found, "ADB", status.adb.message, status.adb.path, status.adb.version),
            line(status.guest.found, "Imagem Android", status.guest.message, status.guest.path),
            f"[{'OK' if status.whpx else 'INFO'}] WHPX: {'detectado/consultado' if status.whpx else 'não confirmado; pode ser habilitado nas Recursos do Windows'}",
        ])
        if status.guest.found and status.guest.kind == "disk image":
            text += "\n\nAtenção: o arquivo foi reconhecido como imagem de disco, mas a inicialização Android x86_64 só será confirmada pelo teste real de boot."
        self.status_text.set(text)

    def save(self) -> None:
        self._apply_paths()
        try:
            self.config.validate()
            save_config(self.config, self.config_path)
        except (ValueError, OSError) as exc:
            messagebox.showerror("Configuração inválida", str(exc), parent=self.window)
            return
        self.on_saved()
        messagebox.showinfo("Configuração salva", "Os caminhos foram salvos. O AndroidNova está pronto para a próxima verificação.", parent=self.window)
