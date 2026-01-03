# Demucs portable bundle build

This folder builds a standalone Demucs CLI bundle (CPU by default) that you can
ship with a C++ desktop app. The bundle includes:

- Demucs + dependencies (PyInstaller)
- Default model weights (htdemucs_6s)
- ffmpeg + ffprobe binaries for decoding mp3

The build is per-OS. Run the matching script on each OS you want to ship.

## Prereqs

- Python 3.8-3.11 (torch 2.0.1 CPU wheels do not support 3.12+)
- `uv` for creating a pinned Python 3.9.21 venv (unless you use an existing venv)
- A C/C++ toolchain suitable for PyInstaller on that OS

## Build (Linux)

```
./packaging/build_linux.sh
```

Use an existing project venv (e.g. `.venv`) instead of creating a new one:

```
USE_EXISTING_VENV=1 VENV_DIR=.venv ./packaging/build_linux.sh
```

## Build (macOS)

```
./packaging/build_macos.sh
```

Use an existing project venv (e.g. `.venv`) instead of creating a new one:

```
USE_EXISTING_VENV=1 VENV_DIR=.venv ./packaging/build_macos.sh
```

## Build (Windows PowerShell)

```
./packaging/build_windows.ps1
```

Use an existing project venv (e.g. `.venv`) instead of creating a new one:

```
$env:USE_EXISTING_VENV = "1"
$env:VENV_DIR = ".venv"
.\packaging\build_windows.ps1
```

## Controlling Python version

By default the scripts create a venv pinned to Python 3.9.21 via `uv`. You can
override that with:

```
PYTHON_VERSION=3.10.14 ./packaging/build_linux.sh
```

## Output

PyInstaller produces `dist/demucs_cli/` with an executable named `demucs_cli`
(or `demucs_cli.exe` on Windows). Ship that folder with your app.

## Usage (from C++)

```
demucs_cli "path/to/file.mp3"
```

Defaults:

- `--device cpu` is injected if you do not pass `--device`
- `--repo <models>` is injected if a bundled `models` folder exists
- `-n htdemucs_6s` is injected if you do not pass `-n/--name`

You can override either explicitly:

```
demucs_cli --device cpu --repo /path/to/models "input.mp3"
```

## Notes

- The scripts download ffmpeg/ffprobe from public URLs. Check the license terms
  for your distribution.
- The ffmpeg URL can be overridden with `--ffmpeg-url` in
  `packaging/fetch_assets.py`.
- The torch version is controlled by `TORCH_VERSION` and
  `TORCHAUDIO_VERSION` environment variables.
- This setup targets x86_64 by default. For arm64, update the torch versions
  and ffmpeg download URLs as needed.
