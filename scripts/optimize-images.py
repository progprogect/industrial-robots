#!/usr/bin/env python3
"""Генерация WebP из манифеста scripts/image-manifest.json через ImageMagick (magick).

Запуск из корня репозитория: python3 scripts/optimize-images.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "scripts" / "image-manifest.json"


def identify_size(path: Path) -> tuple[int, int]:
    out = subprocess.check_output(
        ["magick", "identify", "-format", "%wx%h", str(path)],
        text=True,
    ).strip()
    w, h = out.split("x", 1)
    return int(w), int(h)


def run_one(entry: dict) -> dict:
    src = ROOT / entry["src"]
    dst = ROOT / entry["dst"]
    max_side = int(entry["max"])
    quality = int(entry["quality"])
    inplace = entry.get("inplace", False)

    if not src.is_file():
        raise FileNotFoundError(src)

    dst.parent.mkdir(parents=True, exist_ok=True)

    if inplace and src.resolve() == dst.resolve():
        tmp = dst.with_suffix(dst.suffix + ".tmp.webp")
        out_path = tmp
    else:
        out_path = dst

    # Resize only if larger than max_side on either dimension; strip metadata
    geo = f"{max_side}x{max_side}>"
    cmd = [
        "magick",
        str(src),
        "-auto-orient",
        "-strip",
        "-resize",
        geo,
        "-quality",
        str(quality),
        str(out_path),
    ]
    subprocess.check_call(cmd, cwd=str(ROOT))

    if inplace and src.resolve() == dst.resolve():
        out_path.replace(dst)

    w, h = identify_size(dst)
    return {"dst": str(dst.relative_to(ROOT)), "width": w, "height": h, "bytes": dst.stat().st_size}


def main() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = data["entries"]
    report = []
    for entry in entries:
        print(f"… {entry['src']} -> {entry['dst']}", flush=True)
        info = run_one(entry)
        report.append(info)
        print(f"  OK {info['width']}x{info['height']} ({info['bytes'] // 1024} KB)", flush=True)

    out_json = ROOT / "scripts" / "image-output-sizes.json"
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Размеры записаны в {out_json.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(e, file=sys.stderr)
        sys.exit(e.returncode)
