#!/usr/bin/env python3
"""Сборка HTML из pages-src/*.src.html с подстановкой partials и плейсхолдеров.
   ЧПУ: вложенные каталоги slug/index.html (GitHub Pages). Запуск из корня: python3 scripts/build-pages.py"""
from __future__ import annotations

import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "pages-src"
SITE_SEO_PATH = ROOT / "scripts" / "site-seo.json"

INCLUDE_RE = re.compile(r"^\s*<!--\s*@include\s+(.+?)\s*-->\s*$", re.MULTILINE)

# Исходник → сегмент пути (пусто = главная index.html в корне)
PAGE_SLUGS: dict[str, str] = {
    "index.src.html": "",
    "photoseparator.src.html": "fotoseparator",
    "privacy.src.html": "politika-konfidencialnosti",
    "agv.src.html": "agv",
    "manipulator.src.html": "robot-manipulyator",
    "contacts.src.html": "kontakty",
    "repair.src.html": "remont",
}

# Старые плоские имена → слаг (редирект-заглушки в корне)
REDIRECT_STUBS: dict[str, str] = {
    "photoseparator.html": "fotoseparator",
    "privacy.html": "politika-konfidencialnosti",
    "agv.html": "agv",
    "manipulator.html": "robot-manipulyator",
    "contacts.html": "kontakty",
    "repair.html": "remont",
}

PAGE_ORDER: list[str] = [
    "index.src.html",
    "photoseparator.src.html",
    "privacy.src.html",
    "agv.src.html",
    "manipulator.src.html",
    "contacts.src.html",
    "repair.src.html",
]

# priority, changefreq (sitemap)
SITEMAP_META: dict[str, tuple[str, str]] = {
    "index.src.html": ("1.0", "weekly"),
    "photoseparator.src.html": ("0.9", "monthly"),
    "agv.src.html": ("0.9", "monthly"),
    "manipulator.src.html": ("0.9", "monthly"),
    "repair.src.html": ("0.85", "monthly"),
    "contacts.src.html": ("0.8", "monthly"),
    "privacy.src.html": ("0.3", "yearly"),
}

PRODUCT_SRC: frozenset[str] = frozenset(
    {"photoseparator.src.html", "agv.src.html", "manipulator.src.html"}
)

# SEO: заголовок, описание, относительный путь к og:image (от корня сайта)
SEO_PAGE: dict[str, dict[str, str]] = {
    "index.src.html": {
        "SEO_TITLE": "ООО «Промышленные роботы» | Индустриальная автоматизация",
        "SEO_DESCRIPTION": (
            "Индустриальная автоматизация и робототехника в Беларуси. ООО «Промышленные роботы», Гродно: "
            "фотосепараторы, роботы-манипуляторы, AGV, ремонт промышленного оборудования, компьютерное зрение."
        ),
        "OG_IMAGE": "assets/images/lab-hero.webp",
        "BREADCRUMB_NAME": "Главная",
    },
    "photoseparator.src.html": {
        "SEO_TITLE": "ООО «Промышленные роботы» | Фотосепаратор и оптическая сортировка",
        "SEO_DESCRIPTION": (
            "Проектирование и производство оптических фотосепараторов, сортировка по компьютерному зрению. "
            "ООО «Промышленные роботы», Республика Беларусь."
        ),
        "OG_IMAGE": "assets/images/products/photoseparator/hero-apple-detection.webp",
        "BREADCRUMB_NAME": "Фотосепаратор",
    },
    "privacy.src.html": {
        "SEO_TITLE": "Политика конфиденциальности — ООО «Промышленные роботы»",
        "SEO_DESCRIPTION": (
            "Порядок обработки персональных данных посетителей сайта ООО «Промышленные роботы». УНП 591043841, г. Гродно."
        ),
        "OG_IMAGE": "assets/images/lab-hero.webp",
        "BREADCRUMB_NAME": "Политика конфиденциальности",
    },
    "agv.src.html": {
        "SEO_TITLE": "Автономная рохля (AGV) | ООО «Промышленные роботы»",
        "SEO_DESCRIPTION": (
            "Автономная рохля (AGV) для паллетных перевозок внутри склада и производства. Параметры подбираются под объект; "
            "внедрение, гарантия и ориентир стоимости — на странице."
        ),
        "OG_IMAGE": "assets/images/agv-rohly.webp",
        "BREADCRUMB_NAME": "Автономная рохля (AGV)",
    },
    "manipulator.src.html": {
        "SEO_TITLE": "Робот-манипулятор | ООО «Промышленные роботы»",
        "SEO_DESCRIPTION": (
            "Промышленный робот-манипулятор: грузоподъёмность до 30 кг, интеграция с ПЛК и учётом, компьютерное зрение, "
            "сервис в Гродно. Ориентир стоимости и комплектация — на странице."
        ),
        "OG_IMAGE": "assets/images/manipulator.webp",
        "BREADCRUMB_NAME": "Робот-манипулятор",
    },
    "contacts.src.html": {
        "SEO_TITLE": "Контакты — ООО «Промышленные роботы»",
        "SEO_DESCRIPTION": (
            "Контакты ООО «Промышленные роботы»: адрес в Гродно, реквизиты, телефон, email, мессенджеры и форма обратной связи."
        ),
        "OG_IMAGE": "assets/images/lab-hero.webp",
        "BREADCRUMB_NAME": "Контакты",
    },
    "repair.src.html": {
        "SEO_TITLE": "Ремонт промышленного оборудования — Гродно | ООО «Промышленные роботы»",
        "SEO_DESCRIPTION": (
            "Ремонт станков, электроники, выезд по области. Выезд и диагностика — 90 BYN, остальное по смете после осмотра. "
            "Звоните — обсудим."
        ),
        "OG_IMAGE": "assets/images/repair/repair-welding.webp",
        "BREADCRUMB_NAME": "Ремонт оборудования",
    },
}


def load_site_seo() -> dict[str, Any]:
    if not SITE_SEO_PATH.is_file():
        return {
            "site_origin": "https://promroboty.by",
            "base_path": "",
            "og_locale": "ru_BY",
            "site_name": "ООО «Промышленные роботы»",
            "default_og_image": "assets/images/lab-hero.webp",
            "theme_color": "#00327d",
        }
    return json.loads(SITE_SEO_PATH.read_text(encoding="utf-8"))


def normalize_base_path(raw: str | None) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    s = s.strip("/")
    return "/" + s if s else ""


def page_path(base_path: str, slug: str) -> str:
    """Путь от корня сайта: /, /repo/, /fotoseparator/, /repo/fotoseparator/."""
    bp = normalize_base_path(base_path)
    slug = (slug or "").strip().strip("/")
    if not slug:
        return f"{bp}/" if bp else "/"
    if not bp:
        return f"/{slug}/"
    return f"{bp}/{slug}/"


def canonical_url(site_origin: str, base_path: str, slug: str) -> str:
    """Абсолютный canonical для страницы."""
    origin = site_origin.rstrip("/")
    bp = normalize_base_path(base_path)
    slug = (slug or "").strip().strip("/")
    if not slug:
        return f"{origin}{bp}/" if bp else f"{origin}/"
    if not bp:
        return f"{origin}/{slug}/"
    return f"{origin}{bp}/{slug}/"


def absolute_asset_url(site_origin: str, base_path: str, rel: str) -> str:
    rel = rel.strip().lstrip("/")
    origin = site_origin.rstrip("/")
    bp = normalize_base_path(base_path)
    if not bp:
        return f"{origin}/{rel}"
    return f"{origin}{bp}/{rel}"


def out_relative_path(src_name: str) -> Path:
    slug = PAGE_SLUGS[src_name]
    if not slug:
        return Path("index.html")
    return Path(slug) / "index.html"


def site_root_prefix(base_path: str) -> str:
    """Префикс для шаблонов: '' или '/industrial-robots' → {{SITE_ROOT_PREFIX}}/assets/..."""
    return normalize_base_path(base_path)


def json_ld_script(data: dict[str, Any]) -> str:
    return '<script type="application/ld+json">\n' + json.dumps(data, ensure_ascii=False) + "\n</script>"


def json_ld_organization(site_origin: str, base_path: str) -> str:
    home = canonical_url(site_origin, base_path, "")
    data = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "ООО «Промышленные роботы»",
        "url": home,
        "logo": absolute_asset_url(site_origin, base_path, "apple-touch-icon.png"),
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


def json_ld_local_business(site_origin: str, base_path: str) -> str:
    home_img = absolute_asset_url(site_origin, base_path, "assets/images/lab-hero.webp")
    contacts = canonical_url(site_origin, base_path, "kontakty")
    data = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": "ООО «Промышленные роботы»",
        "image": home_img,
        "telephone": "+375255092206",
        "email": "progprogect@gmail.com",
        "url": contacts,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "ул. Академическая, 17",
            "addressLocality": "Гродно",
            "addressCountry": "BY",
        },
    }
    return json.dumps(data, ensure_ascii=False)


def build_breadcrumb_ld(site_origin: str, base_path: str, src_name: str) -> dict[str, Any]:
    seo = SEO_PAGE[src_name]
    name = seo.get("BREADCRUMB_NAME", seo["SEO_TITLE"].split("|")[0].strip())
    home = canonical_url(site_origin, base_path, "")
    products_url = f"{home}#solutions"
    items: list[dict[str, Any]] = [
        {"@type": "ListItem", "position": 1, "name": "Главная", "item": home},
    ]
    if src_name in PRODUCT_SRC:
        items.append({"@type": "ListItem", "position": 2, "name": "Продукты", "item": products_url})
        items.append(
            {
                "@type": "ListItem",
                "position": 3,
                "name": name,
                "item": canonical_url(site_origin, base_path, PAGE_SLUGS[src_name]),
            }
        )
    else:
        items.append(
            {
                "@type": "ListItem",
                "position": 2,
                "name": name,
                "item": canonical_url(site_origin, base_path, PAGE_SLUGS[src_name]),
            }
        )
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}


def build_webpage_ld(site_origin: str, base_path: str, src_name: str, site_name: str) -> dict[str, Any]:
    seo = SEO_PAGE[src_name]
    cid = canonical_url(site_origin, base_path, PAGE_SLUGS[src_name])
    home = canonical_url(site_origin, base_path, "")
    return {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": seo["SEO_TITLE"].split("|")[0].strip(),
        "description": seo["SEO_DESCRIPTION"],
        "url": cid,
        "isPartOf": {"@type": "WebSite", "name": site_name, "url": home},
    }


def build_product_or_service_ld(site_origin: str, base_path: str, src_name: str, site_name: str) -> dict[str, Any] | None:
    if src_name == "repair.src.html":
        seo = SEO_PAGE[src_name]
        cid = canonical_url(site_origin, base_path, PAGE_SLUGS[src_name])
        home = canonical_url(site_origin, base_path, "")
        return {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": seo.get("BREADCRUMB_NAME", "Ремонт оборудования"),
            "description": seo["SEO_DESCRIPTION"],
            "url": cid,
            "provider": {"@type": "Organization", "name": site_name, "url": home},
        }
    if src_name in PRODUCT_SRC:
        seo = SEO_PAGE[src_name]
        cid = canonical_url(site_origin, base_path, PAGE_SLUGS[src_name])
        home = canonical_url(site_origin, base_path, "")
        return {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": seo.get("BREADCRUMB_NAME", seo["SEO_TITLE"].split("|")[0].strip()),
            "description": seo["SEO_DESCRIPTION"],
            "url": cid,
            "brand": {"@type": "Brand", "name": site_name},
            "manufacturer": {"@type": "Organization", "name": site_name, "url": home},
        }
    return None


def build_json_ld_extra_html(site_origin: str, base_path: str, src_name: str, site_name: str) -> str:
    if src_name == "index.src.html":
        return ""
    parts: list[str] = []
    parts.append(json_ld_script(build_breadcrumb_ld(site_origin, base_path, src_name)))
    parts.append(json_ld_script(build_webpage_ld(site_origin, base_path, src_name, site_name)))
    ps = build_product_or_service_ld(site_origin, base_path, src_name, site_name)
    if ps:
        parts.append(json_ld_script(ps))
    return "\n".join(parts)


def build_page_vars(src_name: str) -> dict[str, str]:
    cfg = load_site_seo()
    base_path = normalize_base_path(str(cfg.get("base_path", "")))
    bp = base_path

    def po(slug: str) -> str:
        return page_path(bp, slug)

    home_path = po("")
    contacts_path = po("kontakty")

    if src_name == "contacts.src.html":
        cta_contacts = "#contacts"
    else:
        cta_contacts = f"{contacts_path}#contacts"

    return {
        "SITE_ROOT_PREFIX": site_root_prefix(bp),
        "HOME_PATH": home_path,
        "HOME_HREF": home_path,
        "PHOTO_PRODUCT_HREF": po("fotoseparator"),
        "AGV_PRODUCT_HREF": po("agv"),
        "MANIPULATOR_PRODUCT_HREF": po("robot-manipulyator"),
        "REPAIR_SERVICE_HREF": po("remont"),
        "CONTACTS_PAGE_HREF": contacts_path,
        "PRIVACY_PAGE_HREF": po("politika-konfidencialnosti"),
        "CTA_CONTACTS_HREF": cta_contacts,
        "PHONE_TEL_HREF": "tel:+375255092206",
    }


def merge_seo_vars(src_name: str, base: dict[str, str]) -> dict[str, str]:
    cfg = load_site_seo()
    site_origin = str(cfg.get("site_origin", "https://promroboty.by")).rstrip("/")
    base_path = normalize_base_path(str(cfg.get("base_path", "")))
    site_name = str(cfg.get("site_name", "ООО «Промышленные роботы»"))

    canonical = canonical_url(site_origin, base_path, PAGE_SLUGS[src_name])
    seo = SEO_PAGE[src_name]
    og_rel = seo.get("OG_IMAGE") or str(cfg.get("default_og_image", "assets/images/lab-hero.webp"))
    og_full = absolute_asset_url(site_origin, base_path, og_rel)

    merged = dict(base)
    merged["SITE_ORIGIN"] = site_origin
    merged["CANONICAL_URL"] = canonical
    merged["SEO_SITE_NAME"] = html.escape(site_name, quote=True)
    raw_title = seo["SEO_TITLE"]
    raw_desc = seo["SEO_DESCRIPTION"]
    merged["SEO_TITLE"] = html.escape(raw_title, quote=False)
    merged["SEO_TITLE_META"] = html.escape(raw_title, quote=True)
    merged["SEO_DESCRIPTION"] = html.escape(raw_desc, quote=True)
    merged["OG_IMAGE_FULL_URL"] = og_full
    merged["OG_LOCALE"] = str(cfg.get("og_locale", "ru_BY"))
    merged["THEME_COLOR"] = str(cfg.get("theme_color", "#00327d"))

    if src_name == "index.src.html":
        merged["JSON_LD_ORG"] = json_ld_organization(site_origin, base_path)
    else:
        merged["JSON_LD_ORG"] = ""

    if src_name == "contacts.src.html":
        merged["JSON_LD_LOCAL"] = json_ld_local_business(site_origin, base_path)
    else:
        merged["JSON_LD_LOCAL"] = ""

    merged["JSON_LD_EXTRA_HTML"] = build_json_ld_extra_html(site_origin, base_path, src_name, site_name)

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


def write_robots_and_sitemap(site_origin: str, base_path: str) -> None:
    bp = normalize_base_path(base_path)
    origin = site_origin.rstrip("/")
    sitemap_loc = f"{origin}{bp}/sitemap.xml" if bp else f"{origin}/sitemap.xml"
    robots = (
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {sitemap_loc}\n"
    )
    (ROOT / "robots.txt").write_text(robots, encoding="utf-8")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for src_name in PAGE_ORDER:
        loc = canonical_url(site_origin, base_path, PAGE_SLUGS[src_name])
        pr, ch = SITEMAP_META.get(src_name, ("0.5", "monthly"))
        lines.append("  <url>")
        lines.append(f"    <loc>{xml_escape(loc)}</loc>")
        lines.append(f"    <lastmod>{today}</lastmod>")
        lines.append(f"    <changefreq>{ch}</changefreq>")
        lines.append(f"    <priority>{pr}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    lines.append("")
    (ROOT / "sitemap.xml").write_text("\n".join(lines), encoding="utf-8")
    print(f"OK {ROOT / 'robots.txt'}")
    print(f"OK {ROOT / 'sitemap.xml'}")


def redirect_stub_html(site_origin: str, base_path: str, slug: str) -> str:
    target = canonical_url(site_origin, base_path, slug)
    rel = page_path(base_path, slug)
    rel_js = json.dumps(rel, ensure_ascii=False)
    gtag = read_partial("partials/gtag.html")
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8"/>
{gtag}<link rel="canonical" href="{html.escape(target, quote=True)}"/>
<meta http-equiv="refresh" content="0;url={html.escape(rel, quote=True)}"/>
<title>Перенаправление</title>
<script>location.replace({rel_js});</script>
</head>
<body><p><a href="{html.escape(rel, quote=True)}">Перейти на новый адрес</a></p></body>
</html>
"""


def write_redirect_stubs(site_origin: str, base_path: str) -> None:
    for fname, slug in REDIRECT_STUBS.items():
        out = ROOT / fname
        out.write_text(redirect_stub_html(site_origin, base_path, slug), encoding="utf-8")
        print(f"OK redirect {out.relative_to(ROOT)}")


def build_one(src_name: str) -> None:
    src_path = SRC / src_name
    if not src_path.is_file():
        print(f"Пропуск: нет {src_path}", file=sys.stderr)
        return
    vars_map = build_page_vars(src_name)
    merged = merge_seo_vars(src_name, vars_map)
    text = src_path.read_text(encoding="utf-8")
    text = expand_includes(text)
    text = apply_vars(text, merged)
    rel = out_relative_path(src_name)
    out_path = ROOT / rel
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    print(f"OK {out_path.relative_to(ROOT)}")


def main() -> None:
    if not SRC.is_dir():
        print(f"Создайте каталог {SRC}", file=sys.stderr)
        sys.exit(1)
    cfg = load_site_seo()
    site_origin = str(cfg.get("site_origin", "https://promroboty.by"))
    base_path = normalize_base_path(str(cfg.get("base_path", "")))
    for src_name in PAGE_ORDER:
        build_one(src_name)
    write_redirect_stubs(site_origin, base_path)
    write_robots_and_sitemap(site_origin, base_path)


if __name__ == "__main__":
    main()
