# PyInstaller onedir build for Windows.
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH).resolve().parent
hiddenimports = sorted(
    set(collect_submodules("androidnova"))
    | {
        "androidnova.main",
        "androidnova.ui.main_window",
        "androidnova.ui.setup_wizard",
        "androidnova.core.emulator",
        "androidnova.config.manager",
        "androidnova.qemu.manager",
        "androidnova.adb.manager",
        "androidnova.diagnostics",
    }
)

# The build script invokes this spec twice. The second invocation sets
# ANDROIDNOVA_DEBUG=1 so the diagnostic executable keeps its console visible.
debug_build = bool(__import__("os").environ.get("ANDROIDNOVA_DEBUG"))
exe_name = "AndroidNova-debug" if debug_build else "AndroidNova"
dist_name = exe_name

runtime_hook = str(ROOT / "packaging" / "runtime_logging.py")

a = Analysis(
    [str(ROOT / "scripts" / "run.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=[(str(ROOT / "config" / "example.json"), "config")],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[runtime_hook],
    excludes=["pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=exe_name,
    debug=debug_build,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=debug_build,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name=dist_name,
)
