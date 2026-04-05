#!/usr/bin/env python3
"""Формирует pages-src/photoseparator.src.html из Separator-LP/index.html.

HEAD (DOCTYPE, тема, header, открытие <main>) берётся из текущего
pages-src/photoseparator.src.html до маркера <!-- Hero Section --> — так
сохраняется единая дизайн-система с остальным сайтом. Перед первым запуском
файл-шаблон должен уже существовать в репозитории.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Рядом с папкой «Industrial Robots» лежит «PhotoSeparator»
LP = ROOT.parent.parent / "PhotoSeparator" / "Separator-LP" / "index.html"
ASSET = "assets/images/products/photoseparator"

text = LP.read_text(encoding="utf-8")
# main: от hero до конца секции contacts (до старого footer LP)
start = text.index("<!-- Hero Section -->")
end = text.index("<!-- Footer -->")
main = text[start:end]

replacements = [
    ('src="apple-detection-2.jpg"', f'src="{ASSET}/apple-detection-2.jpg"'),
    ('poster="separator-poster.jpg"', f'poster="{ASSET}/separator-poster.jpg"'),
    ('src="separator-example.mp4"', f'src="{ASSET}/separator-example.mp4"'),
    ('src="plate.jpeg"', f'src="{ASSET}/plate.jpeg"'),
    ('src="SmartCameraX86.jpg"', f'src="{ASSET}/SmartCameraX86.jpg"'),
    (
        'src="680a070c3b99253410dd3dcf-69a86629d3773d2ea3e50090_Manufacturing_poster.0000000.jpg"',
        f'src="{ASSET}/680a070c3b99253410dd3dcf-69a86629d3773d2ea3e50090_Manufacturing_poster.0000000.jpg"',
    ),
    ('src="Bones.png.webp"', f'src="{ASSET}/Bones.png.webp"'),
    ('src="horticulturae-07-00276-g008.png"', f'src="{ASSET}/horticulturae-07-00276-g008.png"'),
    ('src="brXmVCZQ-2.jpeg"', f'src="{ASSET}/brXmVCZQ-2.jpeg"'),
    ('src="XWnxVjDr.jpeg"', f'src="{ASSET}/XWnxVjDr.jpeg"'),
    ('src="RQH6Glbg.jpeg"', f'src="{ASSET}/RQH6Glbg.jpeg"'),
    ("Сравнение с эталоном через AI-алгоритмы «Базтит».", "Сравнение с эталоном через наши AI-алгоритмы."),
    ("Месяцев — ориентировочный срок окупаемости оборудования БАЗТИТ.", "Месяцев — ориентировочный срок окупаемости оборудования."),
    ("<th class=\"p-6 font-headline font-extrabold text-primary border-b-2 border-primary\">BAZTIT (РБ)</th>", "<th class=\"p-6 font-headline font-extrabold text-primary border-b-2 border-primary\">Промышленные роботы (РБ)</th>"),
]

for a, b in replacements:
    main = main.replace(a, b)

HEAD_MARKER = "<!-- Hero Section -->"
OUT_SRC = ROOT / "pages-src" / "photoseparator.src.html"
if not OUT_SRC.is_file():
    raise FileNotFoundError(
        f"Ожидается существующий шаблон {OUT_SRC} (HEAD до {HEAD_MARKER!r})."
    )
_existing = OUT_SRC.read_text(encoding="utf-8")
if HEAD_MARKER not in _existing:
    raise ValueError(f"В {OUT_SRC} нет маркера {HEAD_MARKER!r}")
HEAD = _existing.split(HEAD_MARKER, 1)[0]

TAIL = """</main>

<!-- @include partials/footer.html -->
</body>
</html>
"""

out = OUT_SRC
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(HEAD + main + TAIL, encoding="utf-8")
print("Wrote", out)
