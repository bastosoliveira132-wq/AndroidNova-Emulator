# AndroidNova Emulator

AndroidNova is a new Windows-oriented Android emulator project built from scratch around QEMU and ADB. It is intentionally independent from the previous `AndroidPC-Emulator` project.

## Current status

This first milestone establishes the application architecture and a safe control layer. It does **not** ship an Android guest image. Booting a real Android guest will be enabled once a compatible Android x86_64 image, kernel/initrd or bootable disk is selected and supplied.

## Architecture

```text
Tkinter GUI
    |
    v
EmulatorCore ---- Configuration
    |
    +---- QEMU Manager ---- QEMU process
    |
    +---- ADB Manager ----- adb executable / Android guest
    |
    +---- Logging
```

## Project layout

```text
src/androidnova/
├── adb/             # ADB discovery and device commands
├── config/          # JSON configuration model and persistence
├── core/            # Emulator lifecycle orchestration
├── qemu/            # QEMU command construction and process control
├── ui/              # Tkinter desktop interface
└── main.py          # Application entry point
config/example.json  # Safe example configuration
scripts/run.py       # Source-tree launcher
runtime/             # Local runtime state (ignored by Git)
tests/               # Automated tests
```

## Requirements

- Windows 10/11 x64 is the first target.
- Python 3.11+ recommended.
- QEMU installed and available through `qemu-system-x86_64` or configured with an explicit path.
- Android guest image to be provided locally.
- Android Debug Bridge (`adb`) for guest communication.

Python dependencies are deliberately minimal in this milestone because Tkinter is part of the standard Python distribution on Windows.

## Run

From the repository root:

```powershell
python scripts/run.py
```

Or:

```powershell
python -m src.androidnova.main
```

Open **Settings** by editing `config/local.json` (created from `config/example.json` when needed), or use the GUI fields for the basic VM parameters.

## Configuration

The configuration is JSON and includes CPU count, RAM, display resolution, audio/network toggles, QEMU path, ADB path and the Android disk image path. Paths are intentionally user-supplied; the project does not download or redistribute Android system images.

## Important limitation

QEMU is only the virtualization/emulation engine. A real Android boot requires a compatible guest image and boot configuration. This repository currently creates the control plane first so that the guest integration can be tested without hard-coding an unverified Android image.

## Roadmap

1. Validate QEMU and ADB discovery on Windows.
2. Add a validated Android x86_64 guest and boot arguments.
3. Detect Android over ADB and expose install/restart/shutdown controls.
4. Add display, audio, network, keyboard/mouse and persistent VM profiles.
5. Add APK installation and richer diagnostics.
6. Investigate Google Play/Google Games compatibility separately, respecting licensing and distribution requirements.
7. Add performance and gaming-oriented tuning after stable Android boot and ADB operation.
