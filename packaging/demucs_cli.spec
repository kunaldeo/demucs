# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import os

from PyInstaller.utils.hooks import collect_all

block_cipher = None

project_root = Path(os.environ.get("DEMUCS_PROJECT_ROOT", os.getcwd())).resolve()
assets_root = Path(os.environ.get("DEMUCS_ASSETS_ROOT", project_root / "packaging" / "assets")).resolve()

hiddenimports = []
_datas = []
_binaries = []

for pkg in [
    "demucs",
    "torch",
    "torchaudio",
    "einops",
    "julius",
    "openunmix",
    "numpy",
    "dora",
    "yaml",
    "lameenc",
    "soundfile",
]:
    datas, binaries, imports = collect_all(pkg)
    _datas += datas
    _binaries += binaries
    hiddenimports += imports

_datas += [
    (str(assets_root / "models"), "models"),
    (str(assets_root / "ffmpeg"), "ffmpeg"),
]

entry_script = project_root / "packaging" / "demucs_cli.py"

analysis = Analysis(
    [str(entry_script)],
    pathex=[str(project_root)],
    binaries=_binaries,
    datas=_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(analysis.pure, analysis.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    [],
    name="demucs_cli",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
