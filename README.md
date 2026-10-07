# AndroidNova Emulator

AndroidNova is a new Windows-oriented Android emulator project built from scratch around QEMU and ADB. It is intentionally independent from the previous `AndroidPC-Emulator` project.

## Etapa 2 — ambiente real do emulador

The project now has the control path required for the first real integration test:

```text
AndroidNova -> QEMU -> Android x86_64 guest -> ADB
```

The repository does **not** contain, download, or redistribute an Android system image. The user must obtain a compatible image from its publisher and configure its local path.

## Windows test package

The repository now includes a Windows packaging path based on PyInstaller. The generated package is a desktop-interface test build; it does **not** bundle QEMU, ADB, or an Android system image.

On Windows, the packaging script is:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1
```

It installs the build-only PyInstaller dependency, creates a PyInstaller `onedir` build, writes it under `dist\AndroidNova-Emulator\`, and creates:

```text
dist\AndroidNova-Emulator-Test.zip
```

The GitHub Actions workflow `Windows test package` performs the same build on a Windows runner and smoke-tests that `AndroidNova-Emulator.exe` can start its Tkinter interface before uploading the ZIP as a workflow artifact.

The test package intentionally contains only the application and its example configuration. It does not contain proprietary/protected Android guest media or external QEMU/ADB binaries.

For a source checkout without building an EXE, Windows users can run:

```powershell
.\run_windows.bat
```

This source launcher requires Python 3.11+.

## Expected Android guest media

The simplest supported first test is a **bootable Android x86_64 ISO** (`.iso`). Android-x86 publishes x86_64 ISO releases and documents running the ISO with QEMU. See the official [Android-x86 download page](https://www.android-x86.org/download) and [QEMU How-To](https://www.android-x86.org/documentation/qemu.html).

The project can also boot a local disk image. For disk media, the configured QEMU format must match the actual file (`qcow2` by default, with `raw`, `vmdk`, `vdi`, and `vhdx` supported by configuration). AndroidNova does not convert or manufacture an Android disk image for the user.

For the first milestone, prefer an Android x86_64 ISO because it avoids pretending that an arbitrary `.qcow2` file is a valid Android guest. The Android-x86 documentation also describes QEMU/KVM execution of an ISO and ADB through TCP port 5555.

## Architecture

```text
Tkinter GUI
    |
    v
EmulatorCore ---- Configuration
    |
    +---- QEMU Manager ---- QEMU process + serial log
    |
    +---- ADB Manager ----- adb executable -> Android guest
    |
    +---- Runtime status -- QEMU / Android boot / ADB state
```

## Project layout

```text
src/androidnova/
├── adb/             # ADB discovery, connect and boot-readiness checks
├── config/          # JSON configuration model and validation
├── core/            # Emulator lifecycle and runtime state
├── qemu/            # QEMU media validation, command construction and process control
├── ui/              # Tkinter desktop interface
└── main.py          # Application entry point
config/example.json  # Example real-guest configuration
tests/               # Automated tests that do not require Android
scripts/run.py       # Source-tree launcher
packaging/           # Windows PyInstaller build files
run_windows.bat      # Windows source launcher
logs/                # Local QEMU serial/application logs (ignored by Git)
images/              # User-provided guest media (ignored by Git)
```

## Requirements on Windows

- Windows 10/11 x64.
- Python 3.11+ recommended for running from source.
- A QEMU build containing `qemu-system-x86_64.exe` for the real Android boot test.
- Android Debug Bridge (`adb.exe`), normally from the Android SDK Platform-Tools, for the real Android/ADB test.
- A user-provided Android x86_64 ISO or compatible disk image for the real guest test.
- For acceleration, Windows Hypervisor Platform must be installed/enabled. QEMU documents WHPX as its Windows hardware-acceleration backend.

The PyInstaller test package itself does **not** require Python to launch the packaged EXE. It still requires QEMU, ADB, and an Android guest image only when you press Start and attempt the real Android boot.

QEMU's current documentation recommends checking the capabilities of the installed binary itself (`-machine help`, `-device help`, etc.) instead of assuming that every build exposes identical devices. AndroidNova therefore keeps optional QEMU arguments configurable rather than inventing guest-specific boot flags.

## Installing QEMU and ADB

Install QEMU using a trusted Windows distribution or build it yourself. Put the QEMU `bin` directory on `PATH`, or set `paths.qemu` to the full path of `qemu-system-x86_64.exe`.

Install Android SDK Platform-Tools and put its directory on `PATH`, or set `paths.adb` to the full path of `adb.exe`.

Verify independently before starting AndroidNova:

```powershell
qemu-system-x86_64.exe --version
adb.exe version
```

If WHPX acceleration is enabled, also verify that the Windows Hypervisor Platform feature is installed. QEMU documents the Windows feature requirement and the `-accel whpx` invocation.

## Supplying the Android image

1. Obtain a compatible Android x86_64 image from its publisher.
2. Do **not** commit the image to this repository.
3. Place it somewhere local, for example:

```text
AndroidNova-Emulator/
└── images/
    └── android-x86_64.iso
```

4. Copy `config/example.json` to `config/local.json` if the launcher has not created it yet.
5. Set `paths.android_image` to the real local path.
6. Leave `qemu.media_type` as `auto` for an `.iso`, or explicitly use `iso`.

AndroidNova validates that the file exists, is readable, and is not empty before starting QEMU. It cannot prove that arbitrary bytes constitute a bootable Android system; that validation ultimately requires QEMU/guest boot testing.

## Run AndroidNova

From the repository root:

```powershell
python scripts/run.py
```

The GUI exposes RAM, CPU count, resolution, Android media path and ADB port. The runtime panel reports the actual lifecycle independently:

```text
QEMU: parado
Android: não iniciado
ADB: desconectado
```

then, during boot:

```text
QEMU: executando
Android: inicializando
ADB: conectando
```

and, only after an online ADB device reports `sys.boot_completed=1`:

```text
QEMU: executando
Android: pronto
ADB: conectado
```

## ADB flow

AndroidNova forwards the configured host ADB port to guest TCP port 5555 by default. The Android-x86 documentation describes the same general model: guest ADB on port 5555 plus QEMU user-network forwarding, followed by `adb connect` to the host-side forwarded port.

Manual verification after Android is ready:

```powershell
adb connect 127.0.0.1:5555
adb devices
```

The application also performs this connection itself and checks `adb devices` plus Android's `sys.boot_completed` property before declaring the guest ready.

## Boot arguments and firmware

AndroidNova deliberately does not hard-code a kernel/initrd/EFI combination that has not been verified against the supplied Android build. A bootable Android-x86 ISO normally contains the bootloader/kernel needed to start from CD-ROM, while custom disk/kernel layouts may require different firmware or boot arguments.

If a particular Android build requires extra QEMU options, place them in `qemu.extra_args` after validating them against the installed QEMU binary and that guest build. QEMU's documentation explicitly supports inspecting available machines/devices with `-machine help` and `-device help`.

## Display, audio and network

- Display uses the configured QEMU frontend (`sdl` by default). The `resolution` setting is retained as a VM preference; it is **not** falsely translated into a generic QEMU flag because Android guest resolution depends on the guest graphics stack.
- Audio uses QEMU's native Windows DirectSound backend on Windows and SDL elsewhere, with an AC97 guest device. QEMU documents DirectSound as a Windows-only audio backend and AC97 as a supported PC audio device.
- Network uses QEMU user-mode networking and `virtio-net-pci`, with the ADB TCP port forwarded from host to guest. QEMU documents `hostfwd` for this exact type of host-to-guest TCP forwarding.
- A serial log is written to `logs/qemu-serial.log`. This is diagnostic output; the Android image must expose useful serial output for it to contain guest boot messages.

## Tests

The automated tests do **not** claim that Android boots. They test only deterministic host-side behaviour such as:

- JSON configuration round trips and validation;
- ISO versus disk command construction;
- configured ADB port forwarding;
- serial log configuration;
- rejection of missing/empty guest media.

Run them with the Python standard library:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

The Windows packaging workflow additionally verifies the PyInstaller output and starts the packaged GUI for a short smoke test. A real Android boot still requires external QEMU, ADB and Android x86_64 guest media on the test computer.

## Current limitations

1. No Android image is included in the repository or test package.
2. No automatic image download is performed.
3. No QEMU or ADB binary is bundled in the test package.
4. The code cannot certify bootability of an arbitrary Android ISO/disk before actually launching it.
5. Android guest-specific resolution, GPU acceleration, sensors and gaming optimizations are not yet implemented.
6. Keyboard/mouse integration currently relies on QEMU's standard PC input devices and has not yet been tuned for Android gaming.
7. Persistent Android disk installation and snapshot management are not yet implemented.
8. Google Play/Google Games support requires a separately validated Android build and licensing/distribution review.

## Stage 2 acceptance criterion

The Stage 2 milestone is **not complete yet**. It is complete only after a real machine demonstrates:

```text
AndroidNova GUI
  -> QEMU process starts
  -> Android x86_64 reaches userspace
  -> guest ADB becomes available
  -> adb connect succeeds
  -> adb devices reports the Android guest
  -> sys.boot_completed == 1
```

Until that machine test is performed, the project is considered **prepared for the real-boot test**, not validated as successfully booting Android.

## Roadmap after the first real boot

1. Run and diagnose the first Android x86_64 ISO boot on Windows.
2. Fix only guest-specific QEMU arguments proven necessary by that image.
3. Make Android/ADB readiness asynchronous in the GUI so boot never blocks the interface.
4. Add persistent disk installation and VM profiles.
5. Improve display/input/audio/network integration.
6. Add APK management and richer diagnostics.
7. Investigate gaming-oriented performance after stable Android boot and ADB operation.
