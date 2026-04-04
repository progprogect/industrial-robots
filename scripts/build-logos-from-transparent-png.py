#!/usr/bin/env python3
"""Собирает assets/logos/logo-*.svg с встроенным растром (один файл на логотип).
   PNG: logo new/transparent/*.png
   «Экологическая альтернатива»: оригинал из logo-eco.webp (корень репозитория).
   Yango не собирается — на сайте текст «Yango Tech»."""
import base64
import re
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "logo new" / "transparent"
OUT = ROOT / "assets" / "logos"
ECO_WEBP = ROOT / "logo-eco.webp"


def sips_size(path: Path) -> tuple[int, int]:
    out = subprocess.check_output(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)], text=True
    )
    w = int(re.search(r"pixelWidth:\s*(\d+)", out).group(1))
    h = int(re.search(r"pixelHeight:\s*(\d+)", out).group(1))
    return w, h


def write_svg_from_raster(src: Path, out_svg: Path, label: str, mime: str) -> None:
    w, h = sips_size(src)
    data = base64.b64encode(src.read_bytes()).decode("ascii")
    safe_label = escape(label, {'"': "&quot;"})
    body = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{safe_label}">
  <image width="{w}" height="{h}" xlink:href="data:{mime};base64,{data}"/>
</svg>
"""
    out_svg.write_text(body, encoding="utf-8")


def write_svg_from_png(png: Path, out_svg: Path, label: str) -> None:
    write_svg_from_raster(png, out_svg, label, "image/png")


def main() -> None:
    if not SRC.is_dir():
        print(f"Нет папки {SRC}", file=sys.stderr)
        sys.exit(1)
    OUT.mkdir(parents=True, exist_ok=True)

    mapping = [
        ("hikrobot.png", "logo-hikrobot.svg", "HikRobot"),
        ("echo.png", "logo-echo.svg", "Echo"),
        ("mcdonalds.png", "logo-mcdonalds.svg", "McDonald's"),
        ("elepart.png", "logo-elepart.svg", "Элепарт"),
        ("shvedoff.png", "logo-shvedoff.svg", "Шведофф"),
        ("huawei.png", "logo-huawei.svg", "Huawei"),
    ]

    for src_name, out_name, label in mapping:
        src = SRC / src_name
        if not src.exists():
            print(f"Пропуск: нет {src}", file=sys.stderr)
            continue
        write_svg_from_png(src, OUT / out_name, label)
        print(f"OK {out_name} <- {src_name}")

    if ECO_WEBP.is_file():
        write_svg_from_raster(
            ECO_WEBP, OUT / "logo-eco.svg", "Экологическая Альтернатива", "image/webp"
        )
        print(f"OK logo-eco.svg <- {ECO_WEBP.name}")
    else:
        print(f"Пропуск logo-eco: нет {ECO_WEBP}", file=sys.stderr)


if __name__ == "__main__":
    main()
