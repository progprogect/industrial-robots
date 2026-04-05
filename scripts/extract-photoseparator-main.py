#!/usr/bin/env python3
"""Одноразово формирует pages-src/photoseparator.src.html из Separator-LP/index.html."""
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

HEAD = '''<!DOCTYPE html>
<html class="dark" lang="ru">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>ООО «Промышленные роботы» | Фотосепаратор и оптическая сортировка</title>
<meta name="description" content="Проектирование и производство оптических фотосепараторов, сортировка по компьютерному зрению. ООО «Промышленные роботы», Республика Беларусь."/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&amp;family=Inter:wght@400;500&amp;family=JetBrains+Mono:wght@400;700&amp;family=Space+Grotesk:wght@500&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<style>
        html { scroll-padding-top: 5.625rem; }
        .material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }
        .glass-panel { background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.3); }
        .tech-grid {
            background-image: radial-gradient(circle at 2px 2px, rgba(0, 200, 255, 0.05) 1px, transparent 0);
            background-size: 40px 40px;
        }
        .corner-accent { position: relative; }
        .corner-accent::before {
            content: ''; position: absolute; top: 0; left: 0; width: 10px; height: 10px;
            border-top: 2px solid #00C8FF; border-left: 2px solid #00C8FF;
        }
        .machined-gradient { background: linear-gradient(135deg, #00327d 0%, #0047ab 100%); }
    </style>
<script id="tailwind-config">
        tailwind.config = {
          darkMode: "class",
          theme: {
            extend: {
              colors: {
                "on-surface-variant": "#bcc8d0",
                "on-secondary-fixed-variant": "#723600",
                "on-error": "#690005",
                "error": "#ffb4ab",
                "on-secondary-fixed": "#311300",
                "surface-container-highest": "#2a3548",
                "on-background": "#d7e3fc",
                "surface-container-low": "#101c2e",
                "background": "#0A1628",
                "surface-tint": "#00C8FF",
                "primary": "#00C8FF",
                "surface-container-lowest": "#030e20",
                "secondary-fixed-dim": "#ffb787",
                "on-surface": "#d7e3fc",
                "surface-container": "#142032",
                "secondary": "#ffb787",
                "on-tertiary-container": "#0043a5",
                "on-primary": "#003546",
                "outline-variant": "#3c484f",
                "surface-container-high": "#1f2a3d",
                "on-secondary-container": "#461f00",
                "primary-fixed": "#bee9ff",
                "on-primary-container": "#001f2a",
                "error-container": "#93000a",
                "surface-bright": "#2e394d",
                "secondary-fixed": "#ffdcc7",
                "tertiary-fixed": "#dae2ff",
                "inverse-surface": "#d7e3fc",
                "tertiary-container": "#9eb8ff",
                "on-error-container": "#ffdad6",
                "secondary-container": "#e1720e",
                "outline": "#86939a",
                "tertiary": "#c7d4ff",
                "on-secondary": "#502400",
                "on-tertiary": "#002c71",
                "primary-fixed-dim": "#68d3ff",
                "on-primary-fixed": "#001f2a",
                "surface-variant": "#2a3548",
                "inverse-primary": "#006684",
                "inverse-on-surface": "#253144",
                "on-tertiary-fixed": "#001947",
                "primary-container": "#00C8FF",
                "on-tertiary-fixed-variant": "#00419f",
                "surface-dim": "#0A1628",
                "surface": "#0A1628",
                "on-primary-fixed-variant": "#004d64",
                "tertiary-fixed-dim": "#b1c5ff"
              },
              fontFamily: {
                "headline": ["Manrope"],
                "body": ["Inter"],
                "label": ["JetBrains Mono"]
              },
              borderRadius: {"DEFAULT": "0.125rem", "lg": "0.25rem", "xl": "0.5rem", "full": "0.75rem"},
            },
          },
        }
    </script>
</head>
<body class="bg-background text-on-background font-body tech-grid selection:bg-primary-container selection:text-on-primary-container pt-20 sm:pt-24">
<!-- @include partials/header.html -->
'''

TAIL = '''
<!-- @include partials/footer.html -->
</body>
</html>
'''

out = ROOT / "pages-src" / "photoseparator.src.html"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(HEAD + main + TAIL, encoding="utf-8")
print("Wrote", out)
