# Transcriptor

Local voice-to-text transcription for Linux. Similar to [SuperWhisper](https://superwhisper.com/) for macOS.

Press **F12**, speak, press **F12** again and the text is typed into the active application. No external servers — everything runs locally with [faster-whisper](https://github.com/SYSTRAN/faster-whisper).

![Idle](transcriptor/assets/icon_idle.png) Idle &nbsp;&nbsp; ![Recording](transcriptor/assets/icon_recording.png) Recording &nbsp;&nbsp; ![Processing](transcriptor/assets/icon_processing.png) Processing

## Features

- **Local transcription** with faster-whisper (based on OpenAI Whisper)
- **No GPU required** — optimized for CPU with int8 quantization
- **Text injection** directly into any active application (xdotool)
- **System tray icon** with visual states (green/red/yellow)
- **GUI settings** with GTK 3 (model, language, hotkey, etc.)
- **Native desktop notifications**
- **X11** and **Wayland** support
- Available models: tiny, base, small, medium, large-v3

## Compatibility

| Component | Supported | Notes |
|---|---|---|
| **Distros** | Ubuntu 22.04+, Debian 12+, Fedora 38+, Arch Linux | Any distro with GTK 3 and Python 3.10+ |
| **Desktops** | GNOME, KDE Plasma, XFCE, Cinnamon, MATE, Budgie | Requires system tray support (AppIndicator) |
| **Display server** | X11, Wayland | X11: xdotool + xclip / Wayland: wtype + wl-copy |
| **Audio** | PipeWire, PulseAudio, ALSA | Any PortAudio-compatible backend |
| **CPU** | x86_64 (Intel/AMD) | ARM64 possible but untested |
| **GPU** | Not required | Optional: NVIDIA with CUDA for acceleration |
| **Python** | 3.10, 3.11, 3.12, 3.13 | |
| **Minimum RAM** | 2 GB (small model) | 4 GB+ recommended |

> **Tested on:** Ubuntu 24.04 LTS, X11, PipeWire, Python 3.12, AMD Ryzen + 32 GB RAM (CPU-only).

## Installation

```bash
git clone https://github.com/Aivanaso/transcriptor.git
cd transcriptor
chmod +x install.sh
./install.sh
```

The installer does everything automatically:

1. Installs system dependencies (apt)
2. Creates a Python virtual environment
3. Installs Transcriptor and its dependencies
4. Adds the app to the application menu

### Run

From the **application menu** (search "Transcriptor") or from terminal:

```bash
./venv/bin/transcriptor
```

The first run will download the Whisper model (`small` is ~461 MB).

### Uninstall

```bash
./uninstall.sh
```

Your configuration (`~/.config/transcriptor/`) and downloaded models (`~/.cache/huggingface/`) are preserved. The script shows how to remove them too.

## Usage

1. Launch `transcriptor` — a green icon appears in the system tray
2. Press **F12** to start recording (icon turns red)
3. Speak
4. Press **F12** to stop and transcribe (icon turns yellow)
5. The text is automatically typed into the active application

### Tray menu

Right-click the tray icon:

- **Configuración** — Opens the settings dialog
- **Salir** — Quits the application

### Settings

From the settings dialog you can change:

| Option | Description | Default |
|---|---|---|
| Model | Whisper model size | `small` |
| Language | Transcription language | Spanish (`es`) |
| Hotkey | Record/stop key | `F12` |
| Auto-paste | Type text into active app | Enabled |
| Notifications | Show desktop notifications | Enabled |

Configuration is stored in `~/.config/transcriptor/config.json`.

## Available models

| Model | Size | RAM (approx.) | Speed | Accuracy |
|---|---|---|---|---|
| tiny | ~75 MB | ~1 GB | Very fast | Low |
| base | ~142 MB | ~1 GB | Fast | Medium |
| **small** | ~461 MB | ~2 GB | Medium | **Good** |
| medium | ~1.5 GB | ~5 GB | Slow | Very good |
| large-v3 | ~3 GB | ~10 GB | Very slow | Excellent |

`small` is recommended for CPU as the best speed/quality trade-off.

## Project structure

```
transcriptor/
├── main.py                  # Root entry point
├── pyproject.toml           # Packaging
├── install.sh               # Full installer
├── uninstall.sh             # Uninstaller
├── transcriptor/
│   ├── main.py              # Package entry point
│   ├── app.py               # Coordinator (state machine)
│   ├── audio.py             # Recording (sounddevice)
│   ├── transcriber.py       # Transcription (faster-whisper)
│   ├── text_input.py        # Text injection (xdotool/wtype)
│   ├── hotkey.py            # Global hotkey (pynput)
│   ├── tray.py              # System tray (pystray)
│   ├── settings_dialog.py   # Settings dialog (GTK 3)
│   ├── config.py            # JSON config management
│   └── assets/              # Tray icons
└── transcriptor.desktop     # Desktop launcher
```

## Tech stack

| Component | Technology |
|---|---|
| Transcription | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2) |
| Audio | [sounddevice](https://python-sounddevice.readthedocs.io/) (PortAudio) |
| Hotkey | [pynput](https://pynput.readthedocs.io/) |
| System tray | [pystray](https://github.com/moses-palmer/pystray) + Pillow |
| Settings GUI | GTK 3 (PyGObject) |
| Notifications | notify-send |

## License

MIT
