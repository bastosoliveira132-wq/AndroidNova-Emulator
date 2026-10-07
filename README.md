# AndroidNova Emulator

AndroidNova is a new Windows-oriented Android emulator project built from scratch around QEMU and ADB. It is intentionally independent from the previous `AndroidPC-Emulator` project.

## Etapa 2 — ambiente real do emulador

The project now has the control path required for the first real integration test:

```text
AndroidNova -> QEMU -> Android x86_64 guest -> ADB
```

The repository does **not** contain, download, or redistribute an Android system image. The user must obtain a compatible image from its publisher and configure its local path.

## Windows readiness and setup assistant

The desktop application now performs a Windows environment check at startup and shows, separately:

- **QEMU** — detects only the real `qemu-system-x86_64.exe` from the configured path, `PATH`, and common Windows installation locations, and probes its version. A `qemu-w64-setup-*.exe` installer is explicitly rejected.
- **ADB** — detects `adb.exe` from the configured path, `PATH`, and the common Android SDK `platform-tools` location, and probes its version.
- **Android guest media** — checks the configured image path and the repository `images/` directory for a non-empty supported image. ISO files are additionally checked for an ISO9660 `CD001` volume signature before being accepted.
- **WHPX** — checks whether the Windows Hypervisor Platform optional feature is enabled.

The GUI includes **Configurar / procurar componentes**, which opens a setup assistant. It lets the user browse for `qemu-system-x86_64.exe`, `adb.exe`, and the user-provided Android x86_64 image, then saves those paths to `config/local.json`.

The media detector is deliberately strict enough to reject an empty or obviously invalid ISO before QEMU starts. It still cannot prove that arbitrary bytes contain a bootable Android x86_64 system; the final proof remains the real QEMU boot test. AndroidNova never downloads or bundles the guest image.

The detector does not recursively scan the whole Windows filesystem. Automatic detection is limited to `PATH`, configured paths, common QEMU/Android SDK locations, and the project's `images/` directory. This keeps startup predictable and avoids unexpectedly scanning unrelated user data.

## Windows test package and diagnostics

The repository includes a Windows packaging path based on PyInstaller. The generated package is a desktop-interface test build; it does **not** bundle QEMU, ADB, or an Android system image.

On Windows, the packaging script is:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1
```

It writes a complete `build_windows.log`, creates two PyInstaller `onedir` builds, and stages a diagnostic ZIP under `dist\`:

```text
dist\AndroidNova\AndroidNova.exe
dist\AndroidNova-debug\AndroidNova-debug.exe
dist\AndroidNova-Emulator-Test.zip
```

`AndroidNova.exe` is the normal GUI build with no console window. `AndroidNova-debug.exe` is the diagnostic build with its console enabled, so Python/PyInstaller startup errors remain visible. Both builds also initialize `androidnova.log` beside the executable; uncaught application exceptions are written there.

For a machine where the normal EXE appears to open and immediately close, run `debug_windows.bat` from the repository root. It verifies Python and PyInstaller, runs the build, checks both EXEs, launches `AndroidNova-debug.exe`, prints its exit code, and always ends with `pause` so the CMD window remains available for inspection. The build transcript is saved as `build_windows.log`.

The GitHub Actions workflow `Windows test package` performs source/import checks, builds both executables on a real Windows runner, verifies the bundled configuration, starts the normal GUI EXE, confirms that it stays alive during the startup smoke test, verifies the startup log, and uploads the ZIP as a workflow artifact.

The test package intentionally contains only the application and its example configuration. It does not contain proprietary/protected Android guest media or external QEMU/ADB binaries.

For a source checkout without building an EXE, Windows users can run:

```powershell
.\run_windows.bat
```

This source launcher requires Python 3.11+.

## Expected Android guest media

The simplest supported first test is a **bootable Android x86_64 ISO** (`.iso`). Android-x86 publishes x86_64 ISO releases and documents running the ISO with QEMU. See the official [Android-x86 download page](https://www.android-x86.org/download) and [QEMU How-To](https://www.android-x86.org/documentation/qemu.html).

The project can also boot a local disk image. For disk media, the configured QEMU format must match the actual file (`qcow2` by default, with `raw`, `vmdk`, `vdi`, and `vhdx` supported by configuration). AndroidNova does not convert or manufacture an Android disk image for the user.

## Architecture

```text
Tkinter GUI
    |
    v
EmulatorCore ---- Configuration
    |
    +---- Environment Detector -- QEMU / ADB / guest media / WHPX
    |
    +---- Setup Wizard ---------- user-selected local paths
    |
    +---- QEMU Manager ---------- QEMU process + serial log
    |
    +---- ADB Manager ----------- adb executable -> Android guest
    |
    +---- Runtime status -------- QEMU / Android boot / ADB state
```

The new environment detector and setup wizard are additive. The existing `EmulatorCore`, QEMU manager, ADB manager, configuration model, and Tkinter application remain the control architecture for the emulator.

## Project layout

```text
src/androidnova/
├── adb/             # ADB discovery, connect and boot-readiness checks
├── config/          # JSON configuration model and validation
├── core/            # Emulator lifecycle and runtime state
├── qemu/            # QEMU media validation, command construction and process control
├── ui/              # Tkinter desktop interface and setup assistant
├── diagnostics.py   # Windows QEMU/ADB/media/WHPX detection
└── main.py          # Application entry point
config/example.json  # Example real-guest configuration
tests/               # Automated tests that do not require Android
scripts/run.py       # Source-tree launcher
packaging/           # Windows PyInstaller build files
run_windows.bat      # Windows source launcher
debug_windows.bat    # Windows diagnostic build/startup launcher
logs/                # Local QEMU serial/application logs (ignored by Git)
images/              # User-provided guest media (ignored by Git)
```

## Requirements on Windows

- Windows 10/11 x64.
- Python 3.11+ recommended for running from source and building; the packaged EXE itself does not require Python.
- A QEMU build containing `qemu-system-x86_64.exe` for the real Android boot test.
- Android Debug Bridge (`adb.exe`), normally from the Android SDK Platform-Tools, for the real Android/ADB test.
- A user-provided Android x86_64 ISO or compatible disk image for the real guest test.
- For acceleration, Windows Hypervisor Platform must be installed/enabled. QEMU documents WHPX as its Windows hardware-acceleration backend.

The PyInstaller test package itself does **not** require Python to launch the packaged EXE. It still requires QEMU, ADB, and an Android guest image only when you press Start and attempt the real Android boot.

## Installing QEMU and ADB

Install QEMU using a trusted Windows distribution or build it yourself. Put the QEMU `bin` directory on `PATH`, or set `paths.qemu` to the full path of `qemu-system-x86_64.exe`. **Do not set this field to the QEMU installer** (`qemu-w64-setup-*.exe`); the installer is not the emulator process.

Official QEMU downloads and Windows installation guidance are available at [QEMU Download](https://www.qemu.org/download/).

Install the current Android SDK Platform-Tools package for Windows. It contains `adb.exe`. The official download is available from [Android Developers — SDK Platform-Tools](https://developer.android.com/tools/releases/platform-tools).

Verify independently before starting AndroidNova:

```powershell
qemu-system-x86_64.exe --version
adb.exe version
```

If WHPX acceleration is enabled, also verify that the Windows Hypervisor Platform feature is installed. QEMU documents the Windows feature requirement and the `-accel whpx` invocation.

## Supplying the Android image

1. Obtain a compatible Android x86_64 image from its publisher.
2. Do **not** commit the image to this repository.
3. You can place it in the local `images/` directory or keep it anywhere else on the Windows machine.
4. Open **Configurar / procurar componentes** in AndroidNova.
5. Select the QEMU executable, ADB executable, and Android x86_64 image when they are not detected automatically.
6. Click **Salvar configuração**.

The saved local paths go into `config/local.json`, which is local configuration and must not contain credentials or protected guest media. VM RAM, CPU count, resolution preference, audio, network, and ADB port are persisted there as well.

AndroidNova validates that the selected guest file exists, is readable, is not empty, and, for ISO files, has the expected ISO9660 volume signature before starting QEMU.

## Run AndroidNova

From the repository root:

```powershell
python scripts/run.py
```

The GUI first reports the host readiness state. A typical clean machine will show QEMU, ADB, and the Android image as **FALTA**. After installation/configuration they should show **OK**. The runtime panel separately reports the actual emulator lifecycle.

## ADB flow
