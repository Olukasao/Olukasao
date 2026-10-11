"""Gera assets/floating-tools.svg: ícones de ferramentas de design flutuando.

Cada ferramenta é um cartão escuro com borda roxa, brilho roxo atrás,
sombra no "chão" que encolhe quando o cartão sobe, e flutuação com leve
inclinação, defasada entre os cartões. Fundo transparente; o texto se
adapta ao tema claro/escuro.

Os ícones ficam em assets/icons/ (devicon e simple-icons, licenças MIT/CC0).

Uso: python3 scripts/build_floating_tools.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ICONS = ROOT / "assets" / "icons"
OUT = ROOT / "assets" / "floating-tools.svg"

# (arquivo do ícone, nome, cor de preenchimento para ícones monocromáticos)
TOOLS = [
    ("figma.svg", "Figma", None),
    ("photoshop.svg", "Photoshop", None),
    ("aftereffects.svg", "After Effects", None),
    ("blender.svg", "Blender", None),
    ("bambulab.svg", "Bambu Lab", "#00AE42"),
]

TILE, GAP, PAD = 96, 40, 30
ICON = 54
TOP = 34                      # espaço para a flutuação subir
W = PAD * 2 + len(TOOLS) * TILE + (len(TOOLS) - 1) * GAP
H = 206
ACCENT = "#A020F0"


def inline_icon(path, x, y, size, fill):
    src = path.read_text()
    view_box = re.search(r'viewBox="([^"]+)"', src).group(1)
    body = re.sub(r"^.*?<svg[^>]*>|</svg>\s*$", "", src, flags=re.S)
    body = re.sub(r"<title>.*?</title>", "", body)
    fill_attr = f' fill="{fill}"' if fill else ""
    return f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="{view_box}"{fill_attr}>{body}</svg>'


def main():
    tiles = []
    for i, (icon, name, fill) in enumerate(TOOLS):
        x = PAD + i * (TILE + GAP)
        cx = x + TILE / 2
        delay = f"{-i * 0.7:.1f}s"
        tiles.append(f'''  <g>
    <ellipse class="shadow" cx="{cx}" cy="{TOP + TILE + 34}" rx="{TILE * 0.42}" ry="7" style="animation-delay:{delay}"/>
    <g class="float" style="animation-delay:{delay}">
      <circle class="glow" cx="{cx}" cy="{TOP + TILE / 2}" r="{TILE * 0.5}" style="animation-delay:{delay}"/>
      <rect x="{x}" y="{TOP}" width="{TILE}" height="{TILE}" rx="24" fill="url(#tile)"/>
      <rect x="{x}" y="{TOP}" width="{TILE}" height="{TILE / 2}" rx="24" fill="url(#gloss)"/>
      <rect x="{x + 0.75}" y="{TOP + 0.75}" width="{TILE - 1.5}" height="{TILE - 1.5}" rx="23.25" fill="none" stroke="url(#edge)" stroke-width="1.5"/>
      {inline_icon(ICONS / icon, x + (TILE - ICON) / 2, TOP + (TILE - ICON) / 2, ICON, fill)}
    </g>
    <text class="label" x="{cx}" y="{H - 12}">{name}</text>
  </g>''')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Ferramentas de design: {', '.join(t[1] for t in TOOLS)}">
  <defs>
    <linearGradient id="tile" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#241b30"/>
      <stop offset="1" stop-color="#0e0b13"/>
    </linearGradient>
    <linearGradient id="gloss" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#fff" stop-opacity=".14"/>
      <stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#d9a8ff"/>
      <stop offset=".5" stop-color="{ACCENT}" stop-opacity=".5"/>
      <stop offset="1" stop-color="#5b1494"/>
    </linearGradient>
    <filter id="blur" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="14"/></filter>
    <filter id="soft" x="-50%" y="-200%" width="200%" height="500%"><feGaussianBlur stdDeviation="4"/></filter>
  </defs>
  <style>
    .float {{ transform-box: fill-box; transform-origin: center; animation: float 4.2s ease-in-out infinite; }}
    @keyframes float {{
      0%, 100% {{ transform: translateY(6px) rotate(-3deg); }}
      50% {{ transform: translateY(-10px) rotate(3deg); }}
    }}
    .shadow {{ fill: #000; opacity: .35; filter: url(#soft); transform-box: fill-box; transform-origin: center;
      animation: shadow 4.2s ease-in-out infinite; }}
    @keyframes shadow {{
      0%, 100% {{ transform: scaleX(1); opacity: .4; }}
      50% {{ transform: scaleX(.7); opacity: .18; }}
    }}
    .glow {{ fill: {ACCENT}; filter: url(#blur); animation: glow 4.2s ease-in-out infinite; }}
    @keyframes glow {{ 0%, 100% {{ opacity: .35; }} 50% {{ opacity: .75; }} }}
    .label {{ font: 600 13px 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; text-anchor: middle; fill: #59636e; }}
    @media (prefers-color-scheme: dark) {{ .label {{ fill: #9198a1; }} }}
  </style>
{chr(10).join(tiles)}
</svg>
'''
    OUT.write_text(svg)
    print(f"{OUT.relative_to(ROOT)}: {OUT.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
