#!/usr/bin/env python3
"""Устарело: актуальная сборка — scripts/build-logos-from-transparent-png.py
   (исходники в assets/logos/sources/). Старые копии — assets/archive/logos-originals/."""
import base64
import re
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1] / "assets" / "logos"
ORIG = Path(__file__).resolve().parents[1] / "assets" / "archive" / "logos-originals"


def sips_size(path: Path) -> tuple[int, int]:
    out = subprocess.check_output(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)], text=True
    )
    w = int(re.search(r"pixelWidth:\s*(\d+)", out).group(1))
    h = int(re.search(r"pixelHeight:\s*(\d+)", out).group(1))
    return w, h


def to_webp(src: Path, dst: Path) -> None:
    subprocess.run(
        ["magick", str(src), "-strip", "-quality", "88", str(dst)],
        check=True,
    )


def write_svg_from_webp(webp: Path, out_svg: Path, label: str) -> None:
    w, h = sips_size(webp)
    data = base64.b64encode(webp.read_bytes()).decode("ascii")
    safe_label = escape(label, {'"': "&quot;"})
    # xlink для совместимости с Safari
    body = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{safe_label}">
  <image width="{w}" height="{h}" xlink:href="data:image/webp;base64,{data}"/>
</svg>
"""
    out_svg.write_text(body, encoding="utf-8")


def main() -> None:
    if not ORIG.is_dir():
        print("Нет папки archive/logos-originals/", file=sys.stderr)
        sys.exit(1)

    mapping = [
        ("logo-hikrobot.png", "logo-hikrobot.svg", "HikRobot"),
        ("logo-echo.png", "logo-echo.svg", "Echo"),
        ("logo-mcdonalds.webp", "logo-mcdonalds.svg", "McDonald's"),
        ("logo-elepart.png", "logo-elepart.svg", "Элепарт"),
        ("logo-eco.webp", "logo-eco.svg", "Экологическая Альтернатива"),
        ("logo-shvedoff.webp", "logo-shvedoff.svg", "Шведофф"),
    ]

    tmp = ROOT / "._tmp_build.webp"
    try:
        for src_name, out_name, label in mapping:
            src = ORIG / src_name
            if not src.exists():
                print(f"Пропуск: нет {src}", file=sys.stderr)
                continue
            to_webp(src, tmp)
            write_svg_from_webp(tmp, ROOT / out_name, label)
            print(f"OK {out_name} <- {src_name}")
    finally:
        if tmp.exists():
            tmp.unlink()


if __name__ == "__main__":
    main()
