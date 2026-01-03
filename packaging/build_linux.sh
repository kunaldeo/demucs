#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

PYTHON=${PYTHON:-python3}
if [[ -z "${VENV_DIR:-}" ]]; then
  if [[ -d ".venv" ]]; then
    VENV_DIR=".venv"
  else
    VENV_DIR=".venv-build"
  fi
fi
USE_EXISTING_VENV=${USE_EXISTING_VENV:-0}
PYTHON_VERSION=${PYTHON_VERSION:-3.9.21}
TORCH_VERSION=${TORCH_VERSION:-2.0.1}
TORCHAUDIO_VERSION=${TORCHAUDIO_VERSION:-2.0.2}
PYINSTALLER_OPTS=${PYINSTALLER_OPTS:-"--clean --noconfirm"}

if [[ "$USE_EXISTING_VENV" == "1" ]]; then
  if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    echo "Venv not found at $VENV_DIR. Set VENV_DIR or create it first."
    exit 1
  fi
else
  if ! command -v uv >/dev/null 2>&1; then
    echo "uv is required to create a pinned Python ${PYTHON_VERSION} venv."
    echo "Install uv, or set USE_EXISTING_VENV=1 to use an existing venv."
    exit 1
  fi
  uv venv --clear --python "${PYTHON_VERSION}" "$VENV_DIR"
fi

PYTHON="$VENV_DIR/bin/python"
PY_VER=$("$PYTHON" - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
)
case "$PY_VER" in
  3.8|3.9|3.10|3.11) ;;
  *)
    echo "Python $PY_VER is not compatible with torch ${TORCH_VERSION}+cpu."
    echo "Set PYTHON_VERSION to 3.8-3.11 (e.g. PYTHON_VERSION=3.9.21)."
    exit 1
    ;;
esac
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

if ! python -m pip --version >/dev/null 2>&1; then
  python -m ensurepip --upgrade
fi

python -m pip install --upgrade pip
python -m pip install \
  "torch==${TORCH_VERSION}+cpu" \
  "torchaudio==${TORCHAUDIO_VERSION}+cpu" \
  --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r "$ROOT_DIR/packaging/requirements_packaging.txt"
python -m pip install "$ROOT_DIR" --no-deps

python "$ROOT_DIR/packaging/fetch_assets.py" --os linux

export DEMUCS_PROJECT_ROOT="$ROOT_DIR"
export DEMUCS_ASSETS_ROOT="$ROOT_DIR/packaging/assets"
pyinstaller "$ROOT_DIR/packaging/demucs_cli.spec" ${PYINSTALLER_OPTS}

printf '\nBuilt CLI at dist/demucs_cli\n'
