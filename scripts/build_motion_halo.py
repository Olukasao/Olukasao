"""Gera assets/motion/halo-carousel.webp: carrossel de vídeos estilo "Halo".

Card central grande tocando um trecho do motion, com halo roxo atrás;
vizinhos menores, esmaecidos e desfocados. Troca sozinho a cada passo.
Fundo transparente para flutuar sobre o GitHub (claro ou escuro).

Os MP4 originais não ficam no repositório (são grandes). Passe a pasta
onde eles estão:

    python3 scripts/build_motion_halo.py /caminho/para/os/videos
"""
import subprocess
from functools import lru_cache
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "motion" / "halo-carousel.webp"

# (arquivo do vídeo, início do trecho em s, título, descrição)
MOTIONS = [
    ("kollect-your-world.mp4", 2.0, "Kollect Your World", "Animação de logo · KollectBR"),
    ("chat-interno.mp4", 3.5, "Chat Interno", "Motion de interface · Acessanet"),
    ("central-assinante.mp4", 7.5, "Central do Assinante", "Motion de produto · Acessanet"),
    ("agenda-tecnicos.mp4", 3.0, "Agenda de Técnicos", "Motion de produto · Acessanet"),
]

W, H = 960, 440
FPS = 20
STEP = 3.5            # segundos que cada motion fica no centro
MOVE = 0.6            # duração da troca
CARD_W, CARD_H = 520, 293
CY = 165
ACCENT = (160, 32, 240)

FONT_BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FONT_REG = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"

# Posições: (deslocamento x a partir do centro, escala, opacidade, esmaecimento 0..1)
SLOTS = {
    0: (0, 1.0, 1.0, 0.0),        # centro
    1: (300, 0.58, 0.6, 1.0),     # direita
    2: (0, 0.42, 0.0, 1.0),       # atrás (invisível)
    3: (-300, 0.58, 0.6, 1.0),    # esquerda
}


def ease(p):
    return p * p * (3 - 2 * p)


def lerp(a, b, p):
    return a + (b - a) * p


def extract(video, start, tmp):
    """Quadros do trecho em 2x do tamanho do card, para reduzir com qualidade."""
    pattern = tmp / f"{video.stem}-%03d.png"
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", str(STEP), "-i", str(video),
        "-vf", f"fps={FPS},scale={CARD_W * 2}:{CARD_H * 2}:flags=lanczos", str(pattern),
    ], check=True)
    return [Image.open(p).convert("RGB") for p in sorted(tmp.glob(f"{video.stem}-*.png"))]


@lru_cache(maxsize=None)
def rounded_mask(w, h, r):
    m = Image.new("L", (w * 4, h * 4), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w * 4 - 1, h * 4 - 1), r * 4, fill=255)
    return m.resize((w, h), Image.LANCZOS)


def side_version(img):
    """Versão esmaecida/desfocada usada nos cards laterais."""
    small = img.resize((CARD_W // 2, CARD_H // 2), Image.LANCZOS).filter(ImageFilter.GaussianBlur(2))
    return ImageEnhance.Brightness(small.resize(img.size, Image.LANCZOS)).enhance(0.7)


def halo():
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse((W / 2 - 300, CY - 150, W / 2 + 300, CY + 150), fill=ACCENT + (110,))
    return g.filter(ImageFilter.GaussianBlur(60))


def main(src_dir):
    src_dir = Path(src_dir)
    n = len(MOTIONS)
    total = int(n * STEP * FPS)
    move_frames = int(MOVE * FPS)
    step_frames = int(STEP * FPS)

    with tempfile.TemporaryDirectory() as t:
        clips = [extract(src_dir / f, s, Path(t)) for f, s, *_ in MOTIONS]
    posters = [c[0] for c in clips]
    sides = [side_version(p) for p in posters]
    glow = halo()
    f_num, f_title, f_desc = (ImageFont.truetype(FONT_BOLD, 13), ImageFont.truetype(FONT_BOLD, 22),
                              ImageFont.truetype(FONT_REG, 14))

    frames = []
    for f in range(total):
        k, u = divmod(f, step_frames)
        p = ease(min(u / move_frames, 1.0))
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        # Halo pulsa de leve e some durante a troca.
        pulse = 0.85 + 0.15 * abs(((u / step_frames) * 2) % 2 - 1)
        canvas.alpha_composite(Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 0)), glow, pulse * p))

        cards = []
        for i in range(n):
            cur, prev = (i - k) % n, (i - k + 1) % n
            a, b = SLOTS[prev], SLOTS[cur]
            dx, s, op, dim = (lerp(a[j], b[j], p) for j in range(4))
            if cur == 0 and p >= 1:
                img = clips[i][min(u - move_frames, len(clips[i]) - 1)] if u >= move_frames else posters[i]
            else:
                img = Image.blend(posters[i], sides[i], dim)
            cards.append((s, dx, op, img))

        for s, dx, op, img in sorted(cards, key=lambda c: c[0]):
            if op <= 0.01:
                continue
            w, h = round(CARD_W * s), round(CARD_H * s)
            tile = img.resize((w, h), Image.LANCZOS).convert("RGBA")
            mask = rounded_mask(w, h, round(16 * s)).point(lambda v: v * op)
            tile.putalpha(mask)
            canvas.alpha_composite(tile, (round(W / 2 + dx - w / 2), round(CY - h / 2)))

        # Legenda do card central, entrando depois da troca.
        c = min(max((u - move_frames) / (0.4 * FPS), 0), 1)
        if c > 0:
            _, _, title, desc = MOTIONS[k % n]
            alpha = round(255 * c)
            d = ImageDraw.Draw(canvas)
            y = 336 + round(8 * (1 - c))
            d.text((W / 2, y), f"{k % n + 1:02d} / {n:02d}", font=f_num, fill=ACCENT + (alpha,), anchor="mm")
            d.text((W / 2, y + 26), title, font=f_title, fill=(150, 40, 230, alpha), anchor="mm")
            d.text((W / 2, y + 52), desc, font=f_desc, fill=(139, 148, 158, alpha), anchor="mm")
        # Barra de progresso do passo atual.
        d = ImageDraw.Draw(canvas)
        d.rounded_rectangle((W / 2 - 80, H - 12, W / 2 + 80, H - 9), 2, fill=(139, 148, 158, 80))
        d.rounded_rectangle((W / 2 - 80, H - 12, W / 2 - 80 + 160 * (u + 1) / step_frames, H - 9), 2, fill=ACCENT + (255,))
        frames.append(canvas)

    frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=round(1000 / FPS), loop=0,
                   quality=78, method=4, lossless=False)
    print(f"{OUT.relative_to(ROOT)}: {OUT.stat().st_size / 1024 / 1024:.1f} MB, {len(frames)} quadros")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
