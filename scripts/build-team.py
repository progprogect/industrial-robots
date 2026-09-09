#!/usr/bin/env python3
"""Сборка блока «Команда»: team-src/*.docx → partials/team-generated.html + assets/docs/team/*.pdf.

Резюме конвертируются pandoc'ом в HTML, размечаются классами и попадают:
  1) в партиал с карточками и <template> для просмотра на странице /komanda/;
  2) в автономные print-страницы, из которых headless Chrome печатает PDF.

Запуск из корня: python3 scripts/build-team.py [--no-pdf]
После изменения team-src/ или team.json перезапустить, затем scripts/build-pages.py.
"""
from __future__ import annotations

import html as html_mod
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEAM_SRC = ROOT / "team-src"
TEAM_JSON = ROOT / "scripts" / "team.json"
PARTIAL_OUT = ROOT / "partials" / "team-generated.html"
PDF_DIR = ROOT / "assets" / "docs" / "team"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

SECTION_HEADS = (
    "Проекты и работы",
    "Технологии",
    "Компетенции",
    "Оборудование и технологии",
    "Оборудование и компетенции",
    "Образование",
    "Образование и сертификаты",
    "Образование и повышение квалификации",
)

# Общий CSS документа-резюме: экран (модалка) и печать (PDF)
RESUME_CSS = """
.resume-doc{font-family:'Inter',-apple-system,'Segoe UI',Arial,sans-serif;color:#1e293b;background:#fff;padding:2rem 2.2rem;font-size:.92rem;line-height:1.55;}
.resume-doc p{margin:0 0 .6rem;}
.resume-doc .rz-org{font-weight:800;font-size:1rem;letter-spacing:.03em;color:#0f172a;margin:0 0 .15rem;}
.resume-doc .rz-addr{font-size:.76rem;color:#64748b;margin:0 0 1rem;}
.resume-doc .rz-note{border:1px solid #cbd5e1;background:#f8fafc;padding:.75rem 1rem;font-size:.73rem;line-height:1.5;color:#64748b;margin:0 0 1.4rem;}
.resume-doc .rz-note p{margin:0;}
.resume-doc .rz-name{font-size:1.3rem;font-weight:800;color:#0f172a;margin:0 0 .1rem;}
.resume-doc .rz-name strong{font-weight:800;}
.resume-doc .rz-role{font-size:1rem;font-weight:600;color:#00327d;margin:0 0 .4rem;}
.resume-doc .rz-exp{font-size:.85rem;color:#475569;margin:0 0 .9rem;}
.resume-doc .rz-intro{font-size:.88rem;color:#475569;margin:0 0 .9rem;}
.resume-doc .rz-sect{font-size:.78rem;font-weight:800;text-transform:uppercase;letter-spacing:.16em;color:#00327d;margin:1.5rem 0 .8rem;border-bottom:2px solid #00327d;padding-bottom:.3rem;}
.resume-doc .rz-sect strong{font-weight:800;}
.resume-doc .rz-row{display:flex;gap:1rem;border:1px solid #e2e8f0;border-left:3px solid #00327d;padding:.85rem 1rem;margin:0 0 .7rem;background:#fff;}
.resume-doc .rz-row-label{flex:0 0 5.6rem;font-size:.76rem;font-weight:600;color:#475569;line-height:1.4;}
.resume-doc .rz-row-label p{margin:0 0 .3rem;}
.resume-doc .rz-row-label strong{display:block;font-size:1rem;font-weight:800;color:#00327d;}
.resume-doc .rz-row-body{flex:1;min-width:0;}
.resume-doc .rz-row-body p{margin:0 0 .55rem;}
.resume-doc .rz-row-body p:last-child{margin-bottom:0;}
.resume-doc .rz-row-body > p:first-child > strong{color:#0f172a;}
@media (max-width:640px){
.resume-doc{padding:1.3rem 1.1rem;font-size:.88rem;}
.resume-doc .rz-row{flex-direction:column;gap:.35rem;}
.resume-doc .rz-row-label{flex:none;display:flex;flex-wrap:wrap;gap:.5rem;align-items:baseline;}
.resume-doc .rz-row-label strong{display:inline;}
}
"""

PRINT_CSS = """
@page{size:A4;margin:14mm 13mm;}
html,body{margin:0;padding:0;background:#fff;}
.resume-doc{padding:0;font-size:10pt;line-height:1.5;}
.resume-doc .rz-row{break-inside:avoid;}
.resume-doc .rz-note{break-inside:avoid;}
"""

STRONG_ONLY_RE = re.compile(r"^<p><strong>(.*?)</strong></p>$", re.DOTALL)
BLOCK_RE = re.compile(r"<table.*?</table>|<p>.*?</p>", re.DOTALL)
TD_RE = re.compile(r"<td>(.*?)</td>", re.DOTALL)


def pandoc_html(docx: Path) -> str:
    res = subprocess.run(
        ["pandoc", "-t", "html", "--wrap=none", str(docx)],
        capture_output=True, text=True, check=True,
    )
    return res.stdout


def classify(raw_html: str) -> str:
    """Плоский поток <p>/<table> от pandoc → размеченный фрагмент .resume-doc."""
    text = re.sub(r"<colgroup>.*?</colgroup>\s*", "", raw_html, flags=re.DOTALL)
    text = re.sub(r'\s*style="[^"]*"', "", text)

    out: list[str] = []
    seen_name = False
    seen_role = False
    seen_exp = False
    seen_sect = False

    for m in BLOCK_RE.finditer(text):
        block = m.group(0).strip()

        if block.startswith("<table"):
            tds = TD_RE.findall(block)
            if len(tds) == 1:
                out.append(f'<div class="rz-note">{tds[0].strip()}</div>')
            elif len(tds) == 2:
                out.append(
                    '<div class="rz-row">'
                    f'<div class="rz-row-label">{tds[0].strip()}</div>'
                    f'<div class="rz-row-body">{tds[1].strip()}</div>'
                    "</div>"
                )
            else:
                out.append(block)
            continue

        strong = STRONG_ONLY_RE.match(block)
        if strong:
            inner = strong.group(1).strip()
            plain = re.sub(r"<[^>]+>", "", inner)
            if "ПРИЛОЖЕНИЕ" in plain:
                continue  # нумерация приложений — из контекста КП, на сайте не нужна
            if plain.startswith("ООО"):
                out.append(f'<p class="rz-org">{inner}</p>')
            elif not seen_name:
                out.append(f'<p class="rz-name">{inner}</p>')
                seen_name = True
            else:
                out.append(f'<p class="rz-sect">{inner}</p>')
                seen_sect = True
            continue

        inner = block[len("<p>"):-len("</p>")].strip()
        plain = re.sub(r"<[^>]+>", "", inner)
        if plain.startswith("г. Гродно"):
            out.append(f'<p class="rz-addr">{inner}</p>')
        elif seen_name and not seen_role:
            out.append(f'<p class="rz-role">{inner}</p>')
            seen_role = True
        elif seen_role and not seen_exp and plain.startswith("Опыт"):
            out.append(f'<p class="rz-exp">{inner}</p>')
            seen_exp = True
        elif seen_exp and not seen_sect:
            out.append(f'<p class="rz-intro">{inner}</p>')
        else:
            out.append(block)

    return '<article class="resume-doc">\n' + "\n".join(out) + "\n</article>"


def esc(s: str) -> str:
    return html_mod.escape(s, quote=True)


def card_html(sp: dict) -> str:
    tags = "".join(
        f'<span class="border border-outline-variant/60 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">{esc(t)}</span>'
        for t in sp["tags"]
    )
    pdf_href = "{{SITE_ROOT_PREFIX}}/assets/docs/team/" + sp["pdf"]
    return f"""<div class="flex flex-col border border-outline-variant/50 bg-white cyber-border transition-colors hover:border-primary">
<div class="flex items-center justify-between gap-3 border-b border-outline-variant/40 bg-surface-container-low px-5 py-2.5">
<span class="inline-flex shrink-0 items-center gap-1.5 text-[10px] font-black uppercase tracking-[0.18em] text-primary"><span class="material-symbols-outlined text-base" aria-hidden="true">description</span>Резюме · {esc(sp["area"])}</span>
<span class="min-w-0 truncate text-[10px] font-bold uppercase tracking-widest text-on-surface-variant/50">{esc(sp["name"])}</span>
</div>
<div class="flex flex-1 flex-col p-6">
<h3 class="mb-1.5 text-lg font-bold leading-snug">{esc(sp["role"])}</h3>
<p class="mb-3 text-xs font-bold uppercase tracking-widest text-on-surface-variant/70">{esc(sp["experience"])}</p>
<p class="flex-1 text-sm leading-relaxed text-on-surface-variant">{esc(sp["hook"])}</p>
<div class="mt-4 flex flex-wrap gap-1.5">{tags}</div>
<div class="mt-5 flex items-stretch gap-2.5">
<button type="button" data-resume="{sp["slug"]}" class="machined-gradient inline-flex min-h-11 flex-1 items-center justify-center gap-2 px-4 text-[10px] font-black uppercase tracking-[0.16em] text-white shadow-lg transition-all hover:shadow-[#00327d]/20 touch-manipulation">Открыть резюме<span class="material-symbols-outlined text-base" aria-hidden="true">open_in_full</span></button>
<a class="inline-flex min-h-11 items-center justify-center gap-1 border border-outline-variant/60 px-3.5 text-[10px] font-black uppercase tracking-widest text-on-surface-variant transition-colors hover:border-primary hover:text-primary" href="{pdf_href}" download title="Скачать резюме в PDF"><span class="material-symbols-outlined text-base" aria-hidden="true">download</span>PDF</a>
</div>
</div>
</div>"""


def print_page_html(fragment: str, title: str) -> str:
    return (
        "<!DOCTYPE html>\n<html lang=\"ru\">\n<head>\n<meta charset=\"utf-8\"/>\n"
        f"<title>{esc(title)}</title>\n<style>{RESUME_CSS}\n{PRINT_CSS}</style>\n</head>\n"
        f"<body>\n{fragment}\n</body>\n</html>\n"
    )


def make_pdf(page_html: str, out_pdf: Path, tmp_dir: Path) -> None:
    src = tmp_dir / (out_pdf.stem + ".html")
    src.write_text(page_html, encoding="utf-8")
    subprocess.run(
        [
            CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
            f"--print-to-pdf={out_pdf}", src.as_uri(),
        ],
        capture_output=True, text=True, check=True,
    )


def main() -> None:
    no_pdf = "--no-pdf" in sys.argv
    data = json.loads(TEAM_JSON.read_text(encoding="utf-8"))
    specialists = data["specialists"]

    cards: list[str] = []
    templates: list[str] = []
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        tmp_dir = Path(td)
        for sp in specialists:
            docx = TEAM_SRC / sp["file"]
            if not docx.is_file():
                print(f"Пропуск {sp['slug']}: нет {docx}", file=sys.stderr)
                continue
            fragment = classify(pandoc_html(docx))
            cards.append(card_html(sp))
            pdf_href = "{{SITE_ROOT_PREFIX}}/assets/docs/team/" + sp["pdf"]
            templates.append(
                f'<template id="rz-tpl-{sp["slug"]}" data-role="{esc(sp["role"])}" data-name="{esc(sp["name"])}" data-pdf="{pdf_href}">\n{fragment}\n</template>'
            )
            if not no_pdf:
                title = f'Резюме — {sp["name"]} — {sp["role"]} · ООО «Промышленные роботы»'
                make_pdf(print_page_html(fragment, title), PDF_DIR / sp["pdf"], tmp_dir)
                print(f"OK PDF {PDF_DIR.relative_to(ROOT) / sp['pdf']}")

    partial = (
        "<!-- Автогенерировано scripts/build-team.py из team-src/ и scripts/team.json — не редактировать вручную -->\n"
        f"<style>{RESUME_CSS}</style>\n"
        '<div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 md:gap-7" id="team-cards">\n'
        + "\n".join(cards)
        + "\n</div>\n"
        + "\n".join(templates)
        + "\n"
    )
    PARTIAL_OUT.write_text(partial, encoding="utf-8")
    print(f"OK {PARTIAL_OUT.relative_to(ROOT)} ({len(cards)} карточек)")


if __name__ == "__main__":
    main()
