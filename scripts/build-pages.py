#!/usr/bin/env python3
"""Сборка HTML из pages-src/*.src.html с подстановкой partials и плейсхолдеров.
   Запуск из корня репозитория: python3 scripts/build-pages.py"""
from __future__ import annotations

import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "pages-src"
SITE_SEO_PATH = ROOT / "scripts" / "site-seo.json"

INCLUDE_RE = re.compile(r"^\s*<!--\s*@include\s+(.+?)\s*-->\s*$", re.MULTILINE)

# INDEX_PREFIX: "" для главной (якоря #…), "index.html" для подстраниц
PAGE_VARS: dict[str, dict[str, str]] = {
    "index.src.html": {
        "INDEX_PREFIX": "",
        "HOME_HREF": "index.html",
        "PHOTO_PRODUCT_HREF": "photoseparator.html",
        "AGV_PRODUCT_HREF": "agv.html",
        "MANIPULATOR_PRODUCT_HREF": "manipulator.html",
        "REPAIR_SERVICE_HREF": "repair.html",
        "CONTACTS_PAGE_HREF": "contacts.html",
        "CTA_CONTACTS_HREF": "contacts.html#contacts",
        "PHONE_TEL_HREF": "tel:+375255092206",
    },
    "photoseparator.src.html": {
        "INDEX_PREFIX": "index.html",
        "HOME_HREF": "index.html",
        "PHOTO_PRODUCT_HREF": "photoseparator.html",
        "AGV_PRODUCT_HREF": "agv.html",
        "MANIPULATOR_PRODUCT_HREF": "manipulator.html",
        "REPAIR_SERVICE_HREF": "repair.html",
        "CONTACTS_PAGE_HREF": "contacts.html",
        "CTA_CONTACTS_HREF": "#contacts",
        "PHONE_TEL_HREF": "tel:+375255092206",
    },
    "privacy.src.html": {
        "INDEX_PREFIX": "index.html",
        "HOME_HREF": "index.html",
        "PHOTO_PRODUCT_HREF": "photoseparator.html",
        "AGV_PRODUCT_HREF": "agv.html",
        "MANIPULATOR_PRODUCT_HREF": "manipulator.html",
        "REPAIR_SERVICE_HREF": "repair.html",
        "CONTACTS_PAGE_HREF": "contacts.html",
        "CTA_CONTACTS_HREF": "contacts.html#contacts",
        "PHONE_TEL_HREF": "tel:+375255092206",
    },
    "agv.src.html": {
        "INDEX_PREFIX": "index.html",
        "HOME_HREF": "index.html",
        "PHOTO_PRODUCT_HREF": "photoseparator.html",
        "AGV_PRODUCT_HREF": "agv.html",
        "MANIPULATOR_PRODUCT_HREF": "manipulator.html",
        "REPAIR_SERVICE_HREF": "repair.html",
        "CONTACTS_PAGE_HREF": "contacts.html",
        "CTA_CONTACTS_HREF": "#contacts",
        "PHONE_TEL_HREF": "tel:+375255092206",
    },
    "manipulator.src.html": {
        "INDEX_PREFIX": "index.html",
        "HOME_HREF": "index.html",
        "PHOTO_PRODUCT_HREF": "photoseparator.html",
        "AGV_PRODUCT_HREF": "agv.html",
        "MANIPULATOR_PRODUCT_HREF": "manipulator.html",
        "REPAIR_SERVICE_HREF": "repair.html",
        "CONTACTS_PAGE_HREF": "contacts.html",
        "CTA_CONTACTS_HREF": "#contacts",
        "PHONE_TEL_HREF": "tel:+375255092206",
    },
    "contacts.src.html": {
        "INDEX_PREFIX": "index.html",
        "HOME_HREF": "index.html",
        "PHOTO_PRODUCT_HREF": "photoseparator.html",
        "AGV_PRODUCT_HREF": "agv.html",
        "MANIPULATOR_PRODUCT_HREF": "manipulator.html",
        "REPAIR_SERVICE_HREF": "repair.html",
        "CONTACTS_PAGE_HREF": "contacts.html",
        "CTA_CONTACTS_HREF": "#contacts",
        "PHONE_TEL_HREF": "tel:+375255092206",
    },
    "repair.src.html": {
        "INDEX_PREFIX": "index.html",
        "HOME_HREF": "index.html",
        "PHOTO_PRODUCT_HREF": "photoseparator.html",
        "AGV_PRODUCT_HREF": "agv.html",
        "MANIPULATOR_PRODUCT_HREF": "manipulator.html",
        "REPAIR_SERVICE_HREF": "repair.html",
        "CONTACTS_PAGE_HREF": "contacts.html",
        "CTA_CONTACTS_HREF": "#contacts",
        "PHONE_TEL_HREF": "tel:+375255092206",
    },
}

OUT_NAMES = {
    "index.src.html": "index.html",
    "photoseparator.src.html": "photoseparator.html",
    "privacy.src.html": "privacy.html",
    "agv.src.html": "agv.html",
    "manipulator.src.html": "manipulator.html",
    "contacts.src.html": "contacts.html",
    "repair.src.html": "repair.html",
}

# SEO: заголовок, описание, относительный путь к og:image (от корня сайта)
SEO_PAGE: dict[str, dict[str, str]] = {
    "index.src.html": {
        "SEO_TITLE": "ООО «Промышленные роботы» | Индустриальная автоматизация",
        "SEO_DESCRIPTION": (
            "Индустриальная автоматизация и робототехника в Беларуси. ООО «Промышленные роботы», Гродно: "
            "фотосепараторы, роботы-манипуляторы, AGV, ремонт промышленного оборудования, компьютерное зрение."
        ),
        "OG_IMAGE": "assets/images/lab-hero.webp",
    },
    "photoseparator.src.html": {
        "SEO_TITLE": "ООО «Промышленные роботы» | Фотосепаратор и оптическая сортировка",
        "SEO_DESCRIPTION": (
            "Проектирование и производство оптических фотосепараторов, сортировка по компьютерному зрению. "
            "ООО «Промышленные роботы», Республика Беларусь."
        ),
        "OG_IMAGE": "assets/images/products/photoseparator/hero-apple-detection.webp",
    },
    "privacy.src.html": {
        "SEO_TITLE": "Политика конфиденциальности — ООО «Промышленные роботы»",
        "SEO_DESCRIPTION": (
            "Порядок обработки персональных данных посетителей сайта ООО «Промышленные роботы». УНП 591043841, г. Гродно."
        ),
        "OG_IMAGE": "assets/images/lab-hero.webp",
    },
    "agv.src.html": {
        "SEO_TITLE": "Автономная рохля (AGV) | ООО «Промышленные роботы»",
        "SEO_DESCRIPTION": (
            "Автономная рохля (AGV) для паллетных перевозок внутри склада и производства. Параметры подбираются под объект; "
            "внедрение, гарантия и ориентир стоимости — на странице."
        ),
        "OG_IMAGE": "assets/images/agv-rohly.webp",
    },
    "manipulator.src.html": {
        "SEO_TITLE": "Робот-манипулятор | ООО «Промышленные роботы»",
        "SEO_DESCRIPTION": (
            "Промышленный робот-манипулятор: грузоподъёмность до 30 кг, интеграция с ПЛК и учётом, компьютерное зрение, "
            "сервис в Гродно. Ориентир стоимости и комплектация — на странице."
        ),
        "OG_IMAGE": "assets/images/manipulator.webp",
    },
    "contacts.src.html": {
        "SEO_TITLE": "Контакты — ООО «Промышленные роботы»",
        "SEO_DESCRIPTION": (
            "Контакты ООО «Промышленные роботы»: адрес в Гродно, реквизиты, телефон, email, мессенджеры и форма обратной связи."
        ),
        "OG_IMAGE": "assets/images/lab-hero.webp",
    },
    "repair.src.html": {
        "SEO_TITLE": "Ремонт промышленного оборудования — Гродно | ООО «Промышленные роботы»",
        "SEO_DESCRIPTION": (
            "Ремонт станков, электроники, выезд по области. Выезд и диагностика — 90 BYN, остальное по смете после осмотра. "
            "Звоните — обсудим."
        ),
        "OG_IMAGE": "assets/images/repair/repair-welding.webp",
    },
}


def load_site_seo() -> dict:
    if not SITE_SEO_PATH.is_file():
        return {
            "site_origin": "https://www.example.com",
            "og_locale": "ru_BY",
            "site_name": "ООО «Промышленные роботы»",
            "default_og_image": "assets/images/lab-hero.webp",
            "theme_color": "#00327d",
        }
    return json.loads(SITE_SEO_PATH.read_text(encoding="utf-8"))


def absolute_url(origin: str, rel_path: str) -> str:
    origin = origin.rstrip("/")
    rel = rel_path.strip().lstrip("/")
    return f"{origin}/{rel}"


def json_ld_organization(origin: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "ООО «Промышленные роботы»",
        "url": origin,
        "logo": absolute_url(origin, "apple-touch-icon.png"),
        "telephone": "+375255092206",
        "email": "progprogect@gmail.com",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "ул. Академическая, 17",
            "addressLocality": "Гродно",
            "addressCountry": "BY",
        },
    }
    return json.dumps(data, ensure_ascii=False)


def json_ld_local_business(origin: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": "ООО «Промышленные роботы»",
        "image": absolute_url(origin, "assets/images/lab-hero.webp"),
        "telephone": "+375255092206",
        "email": "progprogect@gmail.com",
        "url": absolute_url(origin, "contacts.html"),
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "ул. Академическая, 17",
            "addressLocality": "Гродно",
            "addressCountry": "BY",
        },
    }
    return json.dumps(data, ensure_ascii=False)


def merge_seo_vars(src_name: str, base: dict[str, str]) -> dict[str, str]:
    cfg = load_site_seo()
    origin = str(cfg.get("site_origin", "https://www.example.com")).rstrip("/")
    out_file = OUT_NAMES[src_name]
    canonical_url = absolute_url(origin, out_file)

    seo = SEO_PAGE[src_name]
    og_rel = seo.get("OG_IMAGE") or cfg.get("default_og_image", "assets/images/lab-hero.webp")
    og_full = absolute_url(origin, og_rel)

    merged = dict(base)
    merged["SITE_ORIGIN"] = origin
    merged["CANONICAL_URL"] = canonical_url
    merged["SEO_SITE_NAME"] = html.escape(str(cfg.get("site_name", "ООО «Промышленные роботы»")), quote=True)
    raw_title = seo["SEO_TITLE"]
    raw_desc = seo["SEO_DESCRIPTION"]
    merged["SEO_TITLE"] = html.escape(raw_title, quote=False)
    merged["SEO_TITLE_META"] = html.escape(raw_title, quote=True)
    merged["SEO_DESCRIPTION"] = html.escape(raw_desc, quote=True)
    merged["OG_IMAGE_FULL_URL"] = og_full
    merged["OG_LOCALE"] = str(cfg.get("og_locale", "ru_BY"))
    merged["THEME_COLOR"] = str(cfg.get("theme_color", "#00327d"))

    if src_name == "index.src.html":
        merged["JSON_LD_ORG"] = json_ld_organization(origin)
    else:
        merged["JSON_LD_ORG"] = ""

    if src_name == "contacts.src.html":
        merged["JSON_LD_LOCAL"] = json_ld_local_business(origin)
    else:
        merged["JSON_LD_LOCAL"] = ""

    return merged


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


def write_robots_and_sitemap(origin: str) -> None:
    origin = origin.rstrip("/")
    robots = (
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {origin}/sitemap.xml\n"
    )
    (ROOT / "robots.txt").write_text(robots, encoding="utf-8")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for out_name in OUT_NAMES.values():
        lines.append("  <url>")
        lines.append(f"    <loc>{origin}/{out_name}</loc>")
        lines.append(f"    <lastmod>{today}</lastmod>")
        lines.append("  </url>")
    lines.append("</urlset>")
    lines.append("")
    (ROOT / "sitemap.xml").write_text("\n".join(lines), encoding="utf-8")
    print(f"OK {ROOT / 'robots.txt'}")
    print(f"OK {ROOT / 'sitemap.xml'}")


def build_one(src_name: str) -> None:
    src_path = SRC / src_name
    if not src_path.is_file():
        print(f"Пропуск: нет {src_path}", file=sys.stderr)
        return
    vars_map = PAGE_VARS.get(src_name)
    if not vars_map:
        print(f"Нет конфигурации для {src_name}", file=sys.stderr)
        return
    merged = merge_seo_vars(src_name, vars_map)
    text = src_path.read_text(encoding="utf-8")
    text = expand_includes(text)
    text = apply_vars(text, merged)
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
    cfg = load_site_seo()
    origin = str(cfg.get("site_origin", "https://www.example.com")).rstrip("/")
    write_robots_and_sitemap(origin)


if __name__ == "__main__":
    main()
