"""Gera assets/behance-carousel.svg a partir das imagens em assets/behance/.

O README do GitHub não roda JavaScript, então o carrossel é um SVG animado
(só CSS) com as imagens embutidas em base64 (SVG carregado via <img> não
busca arquivos externos).

Layout estilo coverflow: card central em destaque, vizinhos menores,
escurecidos e desfocados, fundo ambiente com a arte atual, legenda
editorial e barra de progresso.

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
    ("demon-slayer-1.webp", "Demon Slayer × KollectBR", "Manipulação de Imagem"),
    ("demon-slayer-2.webp", "Demon Slayer × KollectBR", "Manipulação de Imagem"),
    ("elfbar.webp", "Elfbar", "Manipulação de Imagem"),
    ("pod-point-1.webp", "Pod Point", "Social Media"),
    ("pod-point-2.webp", "Pod Point", "Social Media"),
]

W, H = 900, 540
CARD_W, CARD_H = 290, 362      # tamanho do card central
CY = 222                       # centro vertical dos cards
STEP_SECONDS = 3.2
MOVE_SECONDS = 0.9
ACCENT = "#A020F0"

# Posições do coverflow: (x do centro, escala, brilho, blur, opacidade)
POS = {
    "C": (W / 2, 1.0, 1.0, 0, 1),
    "L1": (W / 2 - 245, 0.76, 0.5, 1.2, 1),
    "R1": (W / 2 + 245, 0.76, 0.5, 1.2, 1),
    "L2": (W / 2 - 400, 0.56, 0.3, 2.5, 0.85),
    "R2": (W / 2 + 400, 0.56, 0.3, 2.5, 0.85),
}


def data_uri(img, quality):
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def cover(img, w, h):
    scale = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    left, top = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((left, top, left + w, top + h))


def blurred(img, w, h, radius, brightness):
    small = cover(img, w, h)
    return ImageEnhance.Brightness(small.filter(ImageFilter.GaussianBlur(radius))).enhance(brightness)


def pose(name):
    x, s, b, blur, o = POS[name]
    return (f"transform: translate({x:.1f}px, {CY}px) scale({s}); "
            f"filter: brightness({b}) blur({blur}px); opacity: {o};")


def main():
    n = len(SLIDES)
    total = n * STEP_SECONDS
    step = 100 / n
    m = MOVE_SECONDS / total * 100
    eps = 0.01

    defs, ambient, captions = [], [], []
    layers = {"far": [], "mid": [], "front": []}
    for i, (name, title, kind) in enumerate(SLIDES):
        img = Image.open(SRC / name).convert("RGB")

        # Card: fundo desfocado da própria arte + arte inteira (contain) em 2x.
        fg = img.copy()
        fg.thumbnail((2 * CARD_W, 2 * CARD_H), Image.LANCZOS)
        fw, fh = fg.width / 2, fg.height / 2
        card_bg = blurred(img, CARD_W // 3, CARD_H // 3, 4, 0.6)
        defs.append(f'''    <image id="bg{i}" href="{data_uri(card_bg, 70)}" width="{CARD_W}" height="{CARD_H}" preserveAspectRatio="none"/>
    <g id="card{i}">
      <g clip-path="url(#cardclip)">
        <use href="#bg{i}" x="{-CARD_W / 2}" y="{-CARD_H / 2}"/>
        <image href="{data_uri(fg, 80)}" x="{-fw / 2:.1f}" y="{-fh / 2:.1f}" width="{fw:.1f}" height="{fh:.1f}"/>
      </g>
      <rect x="{-CARD_W / 2}" y="{-CARD_H / 2}" width="{CARD_W}" height="{CARD_H}" rx="18" fill="none" stroke="#fff" stroke-opacity=".14"/>
    </g>''')

        # Ordem no tempo: R1 -> C -> L1 -> L2 -> (volta por trás) -> R2 -> R1.
        # O card i começa adiantado (n - i) passos, então o card 0 abre no centro.
        delay = -((n - i) % n) * STEP_SECONDS
        style = f'style="animation-delay:{delay:.2f}s"'
        ambient.append(f'    <use class="amb" href="#bg{i}" transform="translate(-60 -60) scale({(W + 120) / CARD_W:.4f} {(H + 120) / CARD_H:.4f})" {style}/>')
        for layer in layers:
            layers[layer].append(f'    <g class="move" {style}><g class="{layer}" {style}><use href="#card{i}"/></g></g>')
        captions.append(f'''    <g class="cap" {style}>
      <text class="num" x="{W / 2}" y="{H - 92}">{i + 1:02d} / {n:02d}</text>
      <text class="title" x="{W / 2}" y="{H - 66}">{title}</text>
      <text class="kind" x="{W / 2}" y="{H - 46}">{kind}</text>
    </g>''')

    hidden = "filter: brightness(0.3) blur(3px); opacity: 0;"
    move_kf = f"""
      0% {{ {pose("R1")} }}
      {m:.2f}% {{ {pose("C")} }}
      {step:.2f}% {{ {pose("C")} }}
      {step + m:.2f}% {{ {pose("L1")} }}
      {2 * step:.2f}% {{ {pose("L1")} }}
      {2 * step + m:.2f}% {{ {pose("L2")} }}
      {3 * step:.2f}% {{ {pose("L2")} }}
      {3 * step + m / 2:.2f}% {{ transform: translate(-150px, {CY}px) scale(0.45); {hidden} }}
      {3 * step + m / 2 + eps:.2f}% {{ transform: translate({W + 150}px, {CY}px) scale(0.45); {hidden} }}
      {3 * step + m:.2f}% {{ {pose("R2")} }}
      {4 * step:.2f}% {{ {pose("R2")} }}
      {4 * step + m:.2f}% {{ {pose("R1")} }}
      100% {{ {pose("R1")} }}"""

    def visible(*ranges):
        """Opacidade 1 só nos intervalos dados (troca de camada instantânea)."""
        frames = [] if ranges[0][0] == 0 else ["0% { opacity: 0; }"]
        for a, b in ranges:
            if a > 0:
                frames.append(f"{a - eps:.3f}% {{ opacity: 0; }}")
            frames.append(f"{a:.3f}% {{ opacity: 1; }}")
            if b < 100:
                frames += [f"{b - eps:.3f}% {{ opacity: 1; }}", f"{b:.3f}% {{ opacity: 0; }}"]
        frames.append(f"100% {{ opacity: {1 if ranges[-1][1] >= 100 else 0}; }}")
        return " ".join(frames)

    # Camadas de profundidade: o card do centro sempre por cima dos vizinhos.
    front = visible((0, step + m))
    mid = visible((step + m, 2 * step + m), (4 * step, 100))
    far = visible((2 * step + m, 4 * step))

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Carrossel de projetos de design no Behance">
  <defs>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="22"/></clipPath>
    <clipPath id="cardclip"><rect x="{-CARD_W / 2}" y="{-CARD_H / 2}" width="{CARD_W}" height="{CARD_H}" rx="18"/></clipPath>
    <radialGradient id="glow" cx="50%" cy="42%" r="45%">
      <stop offset="0" stop-color="{ACCENT}" stop-opacity=".45"/>
      <stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="shade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#07030c" stop-opacity=".35"/>
      <stop offset=".6" stop-color="#07030c" stop-opacity=".55"/>
      <stop offset="1" stop-color="#07030c" stop-opacity=".95"/>
    </linearGradient>
    <linearGradient id="edges" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#07030c" stop-opacity=".9"/>
      <stop offset=".12" stop-color="#07030c" stop-opacity="0"/>
      <stop offset=".88" stop-color="#07030c" stop-opacity="0"/>
      <stop offset="1" stop-color="#07030c" stop-opacity=".9"/>
    </linearGradient>
{chr(10).join(defs)}
  </defs>
  <style>
    .move {{ animation: move {total:.1f}s cubic-bezier(.65,0,.35,1) infinite; }}
    @keyframes move {{{move_kf}
    }}
    .front {{ animation: front {total:.1f}s linear infinite; }}
    .mid {{ animation: mid {total:.1f}s linear infinite; }}
    .far {{ animation: far {total:.1f}s linear infinite; }}
    @keyframes front {{ {front} }}
    @keyframes mid {{ {mid} }}
    @keyframes far {{ {far} }}
    .amb {{ opacity: 0; animation: amb {total:.1f}s ease-in-out infinite; }}
    @keyframes amb {{ 0% {{ opacity: 0; }} {m:.3f}% {{ opacity: 1; }} {step:.3f}% {{ opacity: 1; }} {step + m:.3f}% {{ opacity: 0; }} 100% {{ opacity: 0; }} }}
    .cap {{ opacity: 0; animation: cap {total:.1f}s ease-out infinite; }}
    @keyframes cap {{
      0% {{ opacity: 0; transform: translateY(10px); filter: blur(4px); }}
      {m * 0.6:.3f}% {{ opacity: 0; transform: translateY(10px); filter: blur(4px); }}
      {m * 1.4:.3f}% {{ opacity: 1; transform: translateY(0); filter: blur(0); }}
      {step - 1:.3f}% {{ opacity: 1; transform: translateY(0); filter: blur(0); }}
      {step + 1:.3f}% {{ opacity: 0; transform: translateY(-6px); filter: blur(4px); }}
      100% {{ opacity: 0; }}
    }}
    .bar {{ transform-box: fill-box; transform-origin: left; animation: bar {STEP_SECONDS}s linear infinite; }}
    @keyframes bar {{ 0% {{ transform: scaleX(0); }} 100% {{ transform: scaleX(1); }} }}
    text {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; text-anchor: middle; }}
    .num {{ font-size: 11px; font-weight: 700; letter-spacing: 3px; fill: #c27bff; }}
    .title {{ font-size: 21px; font-weight: 700; fill: #fff; }}
    .kind {{ font-size: 13px; fill: #b9a7c9; letter-spacing: .5px; }}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="#07030c"/>
{chr(10).join(ambient)}
    <rect width="{W}" height="{H}" fill="url(#shade)"/>
    <rect width="{W}" height="{H}" fill="url(#glow)"/>
{chr(10).join(layers["far"])}
{chr(10).join(layers["mid"])}
{chr(10).join(layers["front"])}
    <rect width="{W}" height="{H}" fill="url(#edges)"/>
{chr(10).join(captions)}
    <rect x="{W / 2 - 80}" y="{H - 26}" width="160" height="3" rx="1.5" fill="#fff" fill-opacity=".15"/>
    <rect class="bar" x="{W / 2 - 80}" y="{H - 26}" width="160" height="3" rx="1.5" fill="{ACCENT}"/>
    <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="22" fill="none" stroke="#fff" stroke-opacity=".08"/>
  </g>
</svg>
'''
    OUT.write_text(svg)
    print(f"{OUT.relative_to(ROOT)}: {OUT.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
