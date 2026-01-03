#!/usr/bin/env python3
"""Thin wrapper to make the Demucs CLI self-contained in a bundle."""
from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import List

from demucs.separate import main as demucs_main


def _bundle_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent


def _has_flag(argv: List[str], flag: str) -> bool:
    if flag in argv:
        return True
    prefix = flag + "="
    return any(arg.startswith(prefix) for arg in argv)


def _inject_defaults(argv: List[str]) -> List[str]:
    args = list(argv)
    root = _bundle_root()

    ffmpeg_dir = root / "ffmpeg"
    if ffmpeg_dir.exists():
        os.environ["PATH"] = str(ffmpeg_dir) + os.pathsep + os.environ.get("PATH", "")

    models_dir = root / "models"
    if not _has_flag(args, "--repo") and models_dir.exists():
        args.extend(["--repo", str(models_dir)])

    if not _has_flag(args, "--name") and not _has_flag(args, "-n"):
        args.extend(["-n", "htdemucs_6s"])

    if not _has_flag(args, "--device"):
        args.extend(["--device", "cpu"])

    return args


def main() -> None:
    argv = _inject_defaults(sys.argv[1:])
    demucs_main(argv)


if __name__ == "__main__":
    main()
