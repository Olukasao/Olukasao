"""Gera as capas clicáveis da seção Motion Design (assets/motion/cover-*.svg).

Cada capa é um SVG com um quadro do vídeo embutido, cantos arredondados,
botão de play pulsando, contador e título. No README cada capa é um link
para o vídeo enviado ao GitHub.

Uso: python3 scripts/build_motion_covers.py
"""
import base64
import io
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "assets" / "motion"

# (quadro do vídeo, arquivo de saída, título, descrição)
MOTIONS = [
    ("kollect-your-world-frame.jpg", "cover-kollect-your-world.svg", "Kollect Your World", "Animação de logo · KollectBR"),
    ("chat-interno-frame.jpg", "cover-chat-interno.svg", "Chat Interno", "Motion · Acessanet"),
]

W, H = 640, 360
PX, PY, PR = 640 - 58, 360 - 52, 26   # centro e raio do botão de play
ACCENT = "#A020F0"


def data_uri(path):
    img = Image.open(path).convert("RGB")
    scale = max(2 * W / img.width, 2 * H / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    left, top = (img.width - 2 * W) // 2, (img.height - 2 * H) // 2
    img = img.crop((left, top, left + 2 * W, top + 2 * H))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=82, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def cover(frame, title, desc, index, total):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{title}: assistir ao vídeo">
  <defs>
    <clipPath id="r"><rect width="{W}" height="{H}" rx="20"/></clipPath>
    <linearGradient id="shade" x1="0" y1="0" x2="0" y2="1">
      <stop offset=".45" stop-color="#000" stop-opacity="0"/>
      <stop offset="1" stop-color="#000" stop-opacity=".85"/>
    </linearGradient>
    <filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="14"/></filter>
  </defs>
  <style>
    text {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; fill: #fff; }}
    .num {{ font-size: 12px; font-weight: 700; letter-spacing: 3px; fill: #d9a8ff; }}
    .title {{ font-size: 24px; font-weight: 700; }}
    .desc {{ font-size: 14px; fill: #d0c8da; }}
    .ring {{ transform-box: fill-box; transform-origin: center; animation: ring 2.4s ease-out infinite; }}
    @keyframes ring {{ 0% {{ transform: scale(1); opacity: .7; }} 100% {{ transform: scale(1.7); opacity: 0; }} }}
    .glow {{ animation: glow 2.4s ease-in-out infinite; }}
    @keyframes glow {{ 0%, 100% {{ opacity: .45; }} 50% {{ opacity: .85; }} }}
  </style>
  <g clip-path="url(#r)">
    <image href="{data_uri(frame)}" width="{W}" height="{H}" preserveAspectRatio="xMidYMid slice"/>
    <rect width="{W}" height="{H}" fill="#000" fill-opacity=".18"/>
    <rect width="{W}" height="{H}" fill="url(#shade)"/>
    <circle class="glow" cx="{PX}" cy="{PY}" r="{PR + 8}" fill="{ACCENT}" filter="url(#blur)"/>
    <circle class="ring" cx="{PX}" cy="{PY}" r="{PR}" fill="none" stroke="#fff" stroke-width="2"/>
    <circle cx="{PX}" cy="{PY}" r="{PR}" fill="{ACCENT}"/>
    <circle cx="{PX}" cy="{PY}" r="{PR}" fill="none" stroke="#fff" stroke-opacity=".35" stroke-width="1.5"/>
    <path d="M{PX - 7} {PY - 11} L{PX + 12} {PY} L{PX - 7} {PY + 11} Z" fill="#fff" stroke="#fff" stroke-width="3" stroke-linejoin="round"/>
    <text class="num" x="24" y="{H - 66}">{index:02d} / {total:02d}</text>
    <text class="title" x="24" y="{H - 40}">{title}</text>
    <text class="desc" x="24" y="{H - 18}">{desc}</text>
    <rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="19.5" fill="none" stroke="#fff" stroke-opacity=".12" stroke-width="1.5"/>
  </g>
</svg>
'''


def main():
    for i, (frame, out, title, desc) in enumerate(MOTIONS, 1):
        src = DIR / frame
        if not src.exists():
            print(f"pulando {out}: falta {src.relative_to(ROOT)}")
            continue
        (DIR / out).write_text(cover(src, title, desc, i, len(MOTIONS)))
        print(f"{(DIR / out).relative_to(ROOT)}: {(DIR / out).stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
