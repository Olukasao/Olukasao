"""Gera assets/behance-carousel.svg a partir das imagens em assets/behance/.

O README do GitHub não roda JavaScript, então o carrossel é um SVG animado
(só CSS) com as imagens embutidas em base64 (SVG carregado via <img> não
busca arquivos externos).

Layout estilo coverflow: card central em destaque, vizinhos menores,
esmaecidos e desfocados, fundo transparente (os cards flutuam sobre o
fundo do GitHub, com sombra), legenda que se adapta ao tema claro/escuro
e barra de progresso.

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
    ("kollectbr-logo.webp", "KollectBR", "Identidade Visual"),
    ("elfbar.webp", "Elfbar", "Manipulação de Imagem"),
    ("pod-point-1.webp", "Pod Point", "Social Media"),
    ("pod-point-2.webp", "Pod Point", "Social Media"),
    ("hookah-like-caixa.webp", "Hookah Like", "Embalagem Personalizada"),
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
    "L1": (W / 2 - 245, 0.76, 0.85, 1.2, 0.6),
    "R1": (W / 2 + 245, 0.76, 0.85, 1.2, 0.6),
    "L2": (W / 2 - 400, 0.56, 0.75, 2.5, 0.3),
    "R2": (W / 2 + 400, 0.56, 0.75, 2.5, 0.3),
    # Fora da tela (cards além dos 5 visíveis esperam aqui, invisíveis).
    "OUT_L": (-150, 0.45, 0.3, 3, 0),
    "OUT_R": (W + 150, 0.45, 0.3, 3, 0),
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

    defs, captions = [], []
    layers = {"far": [], "mid": [], "front": []}
    for i, (name, title, kind) in enumerate(SLIDES):
        img = Image.open(SRC / name).convert("RGB")

        # Card: fundo desfocado da própria arte + arte inteira (contain) em 2x.
        fg = img.copy()
        fg.thumbnail((2 * CARD_W, 2 * CARD_H), Image.LANCZOS)
        fw, fh = fg.width / 2, fg.height / 2
        card_bg = blurred(img, CARD_W // 3, CARD_H // 3, 4, 0.6)
        defs.append(f'''    <image id="bg{i}" href="{data_uri(card_bg, 70)}" width="{CARD_W}" height="{CARD_H}" preserveAspectRatio="none"/>
    <g id="card{i}" filter="url(#float)">
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
        for layer in layers:
            layers[layer].append(f'    <g class="move" {style}><g class="{layer}" {style}><g class="bob"><use href="#card{i}"/></g></g></g>')
        captions.append(f'''    <g class="cap" {style}>
      <text class="num" x="{W / 2}" y="{H - 92}">{i + 1:02d} / {n:02d}</text>
      <text class="title" x="{W / 2}" y="{H - 66}">{title}</text>
      <text class="kind" x="{W / 2}" y="{H - 46}">{kind}</text>
    </g>''')

    # Posição do card em cada passo; ele chega nela durante os primeiros m%.
    # Com mais de 5 artes, as excedentes esperam fora da tela à esquerda.
    seq = ["C", "L1", "L2"] + ["OUT_L"] * (n - 5) + ["R2", "R1"]
    frames = [f"0% {{ {pose('R1')} }}"]
    for k in range(n - 1):
        a, prev, cur = k * step, seq[k - 1] if k else "R1", seq[k]
        if cur == "R2" and prev == "L2":
            # Sem espera fora da tela: sai pela esquerda e volta pela direita no meio do movimento.
            frames += [f"{a + m / 2:.3f}% {{ {pose('OUT_L')} }}", f"{a + m / 2 + eps:.3f}% {{ {pose('OUT_R')} }}"]
        elif cur == "R2":
            frames += [f"{a:.3f}% {{ {pose('OUT_R')} }}"]
        elif k:
            frames += [f"{a:.3f}% {{ {pose(prev)} }}"]
        frames += [f"{a + m:.3f}% {{ {pose(cur)} }}"]
    frames += [f"{(n - 1) * step:.3f}% {{ {pose('R2')} }}", f"{(n - 1) * step + m:.3f}% {{ {pose('R1')} }}",
               f"100% {{ {pose('R1')} }}"]
    move_kf = "\n      " + "\n      ".join(frames)

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
    mid = visible((step + m, 2 * step + m), ((n - 1) * step, 100))
    far = visible((2 * step + m, (n - 1) * step))

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Carrossel de projetos de design no Behance">
  <defs>
    <clipPath id="cardclip"><rect x="{-CARD_W / 2}" y="{-CARD_H / 2}" width="{CARD_W}" height="{CARD_H}" rx="18"/></clipPath>
    <filter id="float" x="-30%" y="-30%" width="160%" height="170%">
      <feDropShadow dx="0" dy="18" stdDeviation="16" flood-color="#000" flood-opacity=".45"/>
    </filter>
    <!-- Esmaece os cards nas bordas laterais, sem pintar fundo. -->
    <linearGradient id="edgefade" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/>
      <stop offset=".1" stop-color="#fff" stop-opacity="1"/>
      <stop offset=".9" stop-color="#fff" stop-opacity="1"/>
      <stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <mask id="edges" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">
      <rect width="{W}" height="{H}" fill="url(#edgefade)"/>
    </mask>
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
    .bob {{ animation: bob 4s ease-in-out infinite; }}
    @keyframes bob {{ 0%, 100% {{ transform: translateY(-4px); }} 50% {{ transform: translateY(4px); }} }}
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
    .num {{ font-size: 11px; font-weight: 700; letter-spacing: 3px; fill: {ACCENT}; }}
    .title {{ font-size: 21px; font-weight: 700; fill: #1f2328; }}
    .kind {{ font-size: 13px; fill: #59636e; letter-spacing: .5px; }}
    .track {{ fill: #8b949e; fill-opacity: .25; }}
    @media (prefers-color-scheme: dark) {{
      .num {{ fill: #c27bff; }}
      .title {{ fill: #f0f6fc; }}
      .kind {{ fill: #9198a1; }}
    }}
  </style>
  <g mask="url(#edges)">
{chr(10).join(layers["far"])}
{chr(10).join(layers["mid"])}
{chr(10).join(layers["front"])}
  </g>
{chr(10).join(captions)}
  <rect class="track" x="{W / 2 - 80}" y="{H - 26}" width="160" height="3" rx="1.5"/>
  <rect class="bar" x="{W / 2 - 80}" y="{H - 26}" width="160" height="3" rx="1.5" fill="{ACCENT}"/>
</svg>
'''
    OUT.write_text(svg)
    print(f"{OUT.relative_to(ROOT)}: {OUT.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
