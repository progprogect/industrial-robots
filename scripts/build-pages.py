#!/usr/bin/env python3
"""Сборка HTML из pages-src/*.src.html с подстановкой partials и плейсхолдеров.
   Запуск из корня репозитория: python3 scripts/build-pages.py"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "pages-src"

INCLUDE_RE = re.compile(r"^\s*<!--\s*@include\s+(.+?)\s*-->\s*$", re.MULTILINE)

# INDEX_PREFIX: "" для главной (якоря #…), "index.html" для подстраниц
PAGE_VARS: dict[str, dict[str, str]] = {
    "index.src.html": {
        "INDEX_PREFIX": "",
        "HOME_HREF": "index.html",
        "PHOTO_PRODUCT_HREF": "photoseparator.html",
        "CTA_CONTACTS_HREF": "#contacts",
    },
    "photoseparator.src.html": {
        "INDEX_PREFIX": "index.html",
        "HOME_HREF": "index.html",
        "PHOTO_PRODUCT_HREF": "photoseparator.html",
        "CTA_CONTACTS_HREF": "#contacts",
    },
    "privacy.src.html": {
        "INDEX_PREFIX": "index.html",
        "HOME_HREF": "index.html",
        "PHOTO_PRODUCT_HREF": "photoseparator.html",
        "CTA_CONTACTS_HREF": "index.html#contacts",
    },
}

OUT_NAMES = {
    "index.src.html": "index.html",
    "photoseparator.src.html": "photoseparator.html",
    "privacy.src.html": "privacy.html",
}


def read_partial(rel_path: str) -> str:
    path = ROOT / rel_path.strip()
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8")


def expand_includes(text: str) -> str:
    def repl(m: re.Match[str]) -> str:
        return read_partial(m.group(1).strip())

    prev = None
    while prev != text:
        prev = text
        text = INCLUDE_RE.sub(repl, text)
    return text


def apply_vars(text: str, vars_map: dict[str, str]) -> str:
    for key, val in vars_map.items():
        text = text.replace("{{" + key + "}}", val)
    if "{{" in text and "}}" in text:
        remaining = set(re.findall(r"\{\{(\w+)\}\}", text))
        if remaining:
            print(f"Предупреждение: не подставлены плейсхолдеры: {remaining}", file=sys.stderr)
    return text


def build_one(src_name: str) -> None:
    src_path = SRC / src_name
    if not src_path.is_file():
        print(f"Пропуск: нет {src_path}", file=sys.stderr)
        return
    vars_map = PAGE_VARS.get(src_name)
    if not vars_map:
        print(f"Нет конфигурации для {src_name}", file=sys.stderr)
        return
    text = src_path.read_text(encoding="utf-8")
    text = expand_includes(text)
    text = apply_vars(text, vars_map)
    out_name = OUT_NAMES.get(src_name, src_name.replace(".src.html", ".html"))
    out_path = ROOT / out_name
    out_path.write_text(text, encoding="utf-8")
    print(f"OK {out_path.relative_to(ROOT)}")


def main() -> None:
    if not SRC.is_dir():
        print(f"Создайте каталог {SRC}", file=sys.stderr)
        sys.exit(1)
    for src_name in PAGE_VARS:
        build_one(src_name)


if __name__ == "__main__":
    main()
