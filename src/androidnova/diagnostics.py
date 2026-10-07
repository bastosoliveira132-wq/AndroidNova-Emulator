"""Host dependency and Android guest media detection for Windows."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from androidnova.config.manager import AppConfig
from androidnova.qemu.manager import resolve_qemu_executable


@dataclass(frozen=True)
class DependencyStatus:
    name: str
    found: bool
    path: str | None
    version: str | None
    message: str


@dataclass(frozen=True)
class GuestMediaStatus:
    found: bool
    path: str | None
    kind: str | None
    message: str


@dataclass(frozen=True)
class EnvironmentStatus:
    qemu: DependencyStatus
    adb: DependencyStatus
    guest: GuestMediaStatus
    whpx: bool


def _candidate_paths(configured: str, names: tuple[str, ...]) -> list[Path]:
    candidates: list[Path] = []
    configured_path = Path(configured).expanduser()
    if configured_path.is_file():
        candidates.append(configured_path)
    resolved = shutil.which(configured)
    if resolved:
        candidates.append(Path(resolved))
    for name in names:
        resolved = shutil.which(name)
        if resolved:
            candidates.append(Path(resolved))
    if os.name == "nt":
        program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        local_app = Path(os.environ.get("LOCALAPPDATA", ""))
        user_profile = Path(os.environ.get("USERPROFILE", ""))
        if "adb.exe" in names:
            candidates.extend([
                local_app / "Android" / "Sdk" / "platform-tools" / "adb.exe",
                user_profile / "AppData" / "Local" / "Android" / "Sdk" / "platform-tools" / "adb.exe",
            ])
    unique: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        try:
            resolved_path = path.resolve()
        except OSError:
            continue
        if resolved_path.is_file():
            key = str(resolved_path).lower()
            if key not in seen:
                seen.add(key)
                unique.append(resolved_path)
    return unique


def _probe(executable: Path, args: tuple[str, ...]) -> str | None:
    try:
        result = subprocess.run([str(executable), *args], capture_output=True, text=True, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    output = (result.stdout or result.stderr).strip()
    return output.splitlines()[0] if output else None


def detect_qemu(config: AppConfig) -> DependencyStatus:
    path = resolve_qemu_executable(config.paths.qemu)
    if path is None:
        configured = Path(config.paths.qemu).name.lower()
        if configured.startswith("qemu-w64-setup-"):
            message = "Instalador do QEMU informado; selecione qemu-system-x86_64.exe"
        else:
            message = "qemu-system-x86_64.exe não encontrado"
        return DependencyStatus("QEMU", False, None, None, message)
    version = _probe(path, ("--version",))
    return DependencyStatus("QEMU", True, str(path), version, "QEMU x86_64 encontrado")


def detect_adb(config: AppConfig) -> DependencyStatus:
    candidates = _candidate_paths(config.paths.adb, ("adb.exe", "adb"))
    if not candidates:
        return DependencyStatus("ADB", False, None, None, "adb.exe não encontrado")
    path = candidates[0]
    version = _probe(path, ("version",))
    return DependencyStatus("ADB", True, str(path), version, "ADB encontrado")


def _looks_like_android_media(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        if path.stat().st_size == 0:
            return False
    except OSError:
        return False
    return path.suffix.lower() in {".iso", ".img", ".raw", ".qcow2", ".vmdk", ".vdi", ".vhd", ".vhdx"}


def detect_guest_media(config: AppConfig, root: Path) -> GuestMediaStatus:
    configured = Path(config.paths.android_image).expanduser()
    candidates = [configured if configured.is_absolute() else root / configured]
    images_dir = root / "images"
    if images_dir.is_dir():
        candidates.extend(sorted(images_dir.iterdir()))
    seen: set[str] = set()
    for candidate in candidates:
        if not _looks_like_android_media(candidate):
            continue
        resolved = candidate.resolve()
        key = str(resolved).lower()
        if key in seen:
            continue
        seen.add(key)
        kind = "ISO" if resolved.suffix.lower() == ".iso" else "disk image"
        return GuestMediaStatus(True, str(resolved), kind, "Mídia candidata encontrada")
    configured_display = str(configured if configured.is_absolute() else root / configured)
    if configured_display:
        return GuestMediaStatus(False, None, None, f"Mídia Android não encontrada, vazia ou inválida: {configured_display}")
    return GuestMediaStatus(False, None, None, "Nenhuma imagem Android configurada/encontrada")


def detect_whpx() -> bool:
    if os.name != "nt":
        return False
    dism = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "dism.exe"
    try:
        result = subprocess.run(
            [str(dism), "/online", "/Get-FeatureInfo", "/FeatureName:HypervisorPlatform"],
            capture_output=True, text=True, timeout=8, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    output = f"{result.stdout}\n{result.stderr}".lower()
    return "state : enabled" in output or "estado : habilitado" in output


def detect_environment(config: AppConfig, root: Path) -> EnvironmentStatus:
    return EnvironmentStatus(detect_qemu(config), detect_adb(config), detect_guest_media(config, root), detect_whpx())
