#!/usr/bin/env python3
"""Download and stage model weights and ffmpeg for packaging."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import sys
import tarfile
import urllib.request
import zipfile

MODEL_NAME = "htdemucs_6s"
MODEL_SIG = "5c90dfd2"
MODEL_CHECKSUM = "34c22ccb"
MODEL_FILENAME = f"{MODEL_SIG}-{MODEL_CHECKSUM}.th"
MODEL_URL = (
    "https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/" + MODEL_FILENAME
)

FFMPEG_URLS = {
    "linux": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
    "macos": "https://evermeet.cx/ffmpeg/getrelease/zip",
    "windows": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
}


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as resp, open(dest, "wb") as fh:
        shutil.copyfileobj(resp, fh)


def _sha256_prefix(path: Path, length: int) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(2**20), b""):
            sha.update(chunk)
    return sha.hexdigest()[:length]


def _stage_models(root: Path, force: bool) -> None:
    repo_root = root.parent
    models_dir = root / "assets" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    yaml_src = repo_root / "demucs" / "remote" / f"{MODEL_NAME}.yaml"
    yaml_dest = models_dir / f"{MODEL_NAME}.yaml"
    if yaml_src.exists():
        shutil.copy2(yaml_src, yaml_dest)
    else:
        raise FileNotFoundError(f"Missing {yaml_src}")

    model_path = models_dir / MODEL_FILENAME
    if model_path.exists() and not force:
        return

    tmp_path = models_dir / (MODEL_FILENAME + ".download")
    _download(MODEL_URL, tmp_path)
    actual = _sha256_prefix(tmp_path, len(MODEL_CHECKSUM))
    if actual != MODEL_CHECKSUM:
        tmp_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"Checksum mismatch for {MODEL_FILENAME}: expected {MODEL_CHECKSUM}, got {actual}"
        )
    tmp_path.rename(model_path)


def _extract_from_tar(archive: Path, dest_dir: Path, suffix: str) -> Path:
    with tarfile.open(archive, "r:*") as tf:
        member = next((m for m in tf.getmembers() if m.name.endswith(suffix)), None)
        if member is None:
            raise RuntimeError(f"{suffix} binary not found in tar archive")
        tf.extract(member, path=dest_dir)
        extracted = dest_dir / member.name
    return extracted


def _extract_from_zip(archive: Path, dest_dir: Path, suffix: str) -> Path:
    with zipfile.ZipFile(archive) as zf:
        member = next(
            (n for n in zf.namelist() if n.endswith(suffix)), None
        )
        if member is None:
            raise RuntimeError(f"{suffix} binary not found in zip archive")
        zf.extract(member, path=dest_dir)
        extracted = dest_dir / member
    return extracted


def _stage_ffmpeg(root: Path, platform: str, force: bool, url: str | None) -> None:
    ffmpeg_dir = root / "assets" / "ffmpeg"
    ffmpeg_dir.mkdir(parents=True, exist_ok=True)

    exe_suffix = ".exe" if platform == "windows" else ""
    targets = {
        f"ffmpeg{exe_suffix}": ffmpeg_dir / f"ffmpeg{exe_suffix}",
        f"ffprobe{exe_suffix}": ffmpeg_dir / f"ffprobe{exe_suffix}",
    }
    if all(target.exists() for target in targets.values()) and not force:
        return

    download_url = url or FFMPEG_URLS[platform]
    tmp = ffmpeg_dir / "ffmpeg_download"
    _download(download_url, tmp)

    work_dir = ffmpeg_dir / "ffmpeg_extract"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    extracted = {}
    if platform == "linux":
        extracted["ffmpeg"] = _extract_from_tar(tmp, work_dir, "/ffmpeg")
        extracted["ffprobe"] = _extract_from_tar(tmp, work_dir, "/ffprobe")
    elif platform == "macos":
        extracted["ffmpeg"] = _extract_from_zip(tmp, work_dir, "/ffmpeg")
        extracted["ffprobe"] = _extract_from_zip(tmp, work_dir, "/ffprobe")
    elif platform == "windows":
        extracted["ffmpeg.exe"] = _extract_from_zip(tmp, work_dir, "/ffmpeg.exe")
        extracted["ffprobe.exe"] = _extract_from_zip(tmp, work_dir, "/ffprobe.exe")
    else:
        raise ValueError(f"Unsupported platform: {platform}")

    for name, src in extracted.items():
        dest = targets[name]
        shutil.copy2(src, dest)
        if platform != "windows":
            dest.chmod(dest.stat().st_mode | 0o111)

    shutil.rmtree(work_dir)
    tmp.unlink(missing_ok=True)


def _detect_platform() -> str:
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform == "darwin":
        return "macos"
    if sys.platform in ("win32", "cygwin"):
        return "windows"
    raise RuntimeError(f"Unsupported platform: {sys.platform}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--os", dest="platform", choices=["linux", "macos", "windows"])
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--skip-ffmpeg", action="store_true")
    parser.add_argument("--skip-models", action="store_true")
    parser.add_argument("--ffmpeg-url", default=None)
    args = parser.parse_args()

    platform = args.platform or _detect_platform()
    root = Path(__file__).resolve().parent

    if not args.skip_models:
        _stage_models(root, args.force)

    if not args.skip_ffmpeg:
        _stage_ffmpeg(root, platform, args.force, args.ffmpeg_url)

    print("Assets ready in packaging/assets")


if __name__ == "__main__":
    main()
