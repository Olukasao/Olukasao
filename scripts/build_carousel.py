"""Gera assets/behance-carousel.svg a partir das imagens em assets/behance/.

O README do GitHub não roda JavaScript, então o carrossel é um SVG animado
com as imagens embutidas em base64 (SVG carregado via <img> não busca
arquivos externos).

Uso: python3 scripts/build_carousel.py
"""
import base64
import io
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "behance"
OUT = ROOT / "assets" / "behance-carousel.svg"

SLIDES = [
    ("elfbar.webp", "Elfbar", "Manipulação de Imagem"),
    ("demon-slayer-1.webp", "Demon Slayer × KollectBR", "Manipulação de Imagem"),
    ("demon-slayer-2.webp", "Demon Slayer × KollectBR", "Manipulação de Imagem"),
    ("pod-point-1.webp", "Pod Point", "Social Media"),
    ("pod-point-2.webp", "Pod Point", "Social Media"),
]

W, H = 800, 460
FG_H = 400          # altura máxima da arte em primeiro plano
SLIDE_SECONDS = 3.5
FADE = 0.7
ACCENT = "#A020F0"


def data_uri(img, quality):
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def background(img):
    """Fundo: a própria arte em modo cover, desfocada e escurecida."""
    small = img.copy()
    small.thumbnail((W // 4, H // 4))
    scale = max(W / small.width, H / small.height)
    small = small.resize((round(small.width * scale), round(small.height * scale)))
    left, top = (small.width - W) // 2, (small.height - H) // 2
    small = small.crop((left, top, left + W, top + H)).resize((W // 4, H // 4))
    small = small.filter(ImageFilter.GaussianBlur(6))
    return ImageEnhance.Brightness(small).enhance(0.45)


def foreground(img):
    """Arte em 2x para ficar nítida em telas de alta densidade."""
    fg = img.copy()
    fg.thumbnail((2 * (W - 80), 2 * FG_H), Image.LANCZOS)
    return fg


def main():
    n = len(SLIDES)
    total = n * SLIDE_SECONDS
    step = 100 / n
    fade = FADE / total * 100

    slides, dots = [], []
    for i, (name, title, kind) in enumerate(SLIDES):
        img = Image.open(SRC / name)
        fg = foreground(img)
        fw, fh = fg.width / 2, fg.height / 2
        fx, fy = (W - fw) / 2, (H - fh) / 2 - 12
        slides.append(f'''  <g class="slide" style="animation-delay:{i * SLIDE_SECONDS:.2f}s">
    <image href="{data_uri(background(img), 70)}" width="{W}" height="{H}" preserveAspectRatio="none"/>
    <g class="art" filter="url(#shadow)">
      <image href="{data_uri(fg, 78)}" x="{fx:.0f}" y="{fy:.0f}" width="{fw:.0f}" height="{fh:.0f}" clip-path="inset(0 round 14px)"/>
    </g>
    <rect width="{W}" height="{H}" fill="url(#fade)"/>
    <text class="title" x="28" y="{H - 34}">{title}</text>
    <text class="kind" x="28" y="{H - 16}">{kind} · Behance</text>
  </g>''')
        cx = W - 28 - (n - 1 - i) * 16
        dots.append(f'  <circle class="dot" cx="{cx}" cy="{H - 24}" r="4" style="animation-delay:{i * SLIDE_SECONDS:.2f}s"/>')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Carrossel de projetos de design no Behance">
  <defs>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="18"/></clipPath>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="130%">
      <feDropShadow dx="0" dy="10" stdDeviation="12" flood-color="#000" flood-opacity="0.55"/>
    </filter>
    <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0.65" stop-color="#000" stop-opacity="0"/>
      <stop offset="1" stop-color="#000" stop-opacity="0.75"/>
    </linearGradient>
  </defs>
  <style>
    .slide {{ opacity: 0; animation: show {total:.1f}s infinite; }}
    .art {{ transform-box: fill-box; transform-origin: center; animation: zoom {total:.1f}s infinite; animation-delay: inherit; }}
    @keyframes show {{
      0% {{ opacity: 0; }}
      {fade:.2f}% {{ opacity: 1; }}
      {step:.2f}% {{ opacity: 1; }}
      {step + fade:.2f}% {{ opacity: 0; }}
      100% {{ opacity: 0; }}
    }}
    @keyframes zoom {{
      0% {{ transform: scale(1.06); filter: blur(6px); }}
      {fade * 1.5:.2f}% {{ filter: blur(0); }}
      {step + fade:.2f}% {{ transform: scale(1); }}
      100% {{ transform: scale(1); }}
    }}
    .dot {{ fill: #fff; opacity: .35; animation: dot {total:.1f}s infinite; }}
    @keyframes dot {{
      0% {{ fill: {ACCENT}; opacity: 1; }}
      {step:.2f}% {{ fill: {ACCENT}; opacity: 1; }}
      {step + 0.01:.2f}% {{ fill: #fff; opacity: .35; }}
      100% {{ fill: #fff; opacity: .35; }}
    }}
    text {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; fill: #fff; }}
    .title {{ font-size: 18px; font-weight: 700; }}
    .kind {{ font-size: 12px; fill: #d9b3ff; }}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="#0d0d0d"/>
{chr(10).join(slides)}
{chr(10).join(dots)}
  </g>
</svg>
'''
    OUT.write_text(svg)
    print(f"{OUT.relative_to(ROOT)}: {OUT.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
