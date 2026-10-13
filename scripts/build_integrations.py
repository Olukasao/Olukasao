# Gera assets/integracoes.svg: cartões das integrações usadas nos projetos.
# Ícones: lucide-static e simple-icons (npm), em EXT/npmi/node_modules.
# Uso: python3 scripts/build_integrations.py EXT assets/integracoes.svg
import re, sys
EXT, OUT = sys.argv[1], sys.argv[2]
NM = f"{EXT}/npmi/node_modules"

def inner(path):
    s = re.sub(r'<!--.*?-->', '', open(path).read(), flags=re.S)
    return re.sub(r'^.*?<svg[^>]*>|</svg>\s*$', '', s.strip(), flags=re.S)

def luc(name, color):
    return f'<g fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{inner(f"{NM}/lucide-static/icons/{name}.svg")}</g>'

def si(slug, color):
    d = re.search(r' d="([^"]+)"', open(f"{NM}/simple-icons/icons/{slug}.svg").read()).group(1)
    return f'<path fill="{color}" d="{d}"/>'

CARDS = [
    ("SGP", "Gestão do provedor", luc("network", "#C084FC")),
    ("OLT Cloud", "Alertas da rede", luc("cloud", "#60A5FA")),
    ("Rastreio GPS", "Técnicos ao vivo", luc("satellite", "#F472B6")),
    ("Nominatim", "Geocodificação", si("openstreetmap", "#7EBC6F")),
    ("ViaCEP", "Busca por CEP", luc("map-pin", "#FBBF24")),
    ("Nuvemshop", "Catálogo da loja", luc("shopping-bag", "#38BDF8")),
    ("Nodemailer", "E-mail transacional", luc("mail", "#34D399")),
    ("WhatsApp", "Atendimento", si("whatsapp", "#25D366")),
]

COLS, W, H, GAP = 4, 214, 76, 12
width = COLS * W + (COLS - 1) * GAP
rows = (len(CARDS) + COLS - 1) // COLS
height = rows * H + (rows - 1) * GAP
out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none">',
       '<style>.t{font:700 15px "Segoe UI",Helvetica,Arial,sans-serif;fill:#F0E6FF}.s{font:400 12px "Segoe UI",Helvetica,Arial,sans-serif;fill:#A99BC0}</style>']
for i, (title, sub, icon) in enumerate(CARDS):
    x = (i % COLS) * (W + GAP); y = (i // COLS) * (H + GAP)
    out.append(f'<g transform="translate({x} {y})">'
               f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="#242938" stroke="#A020F0" stroke-opacity="0.45"/>'
               f'<rect x="14" y="16" width="44" height="44" rx="11" fill="#1A1D29"/>'
               f'<g transform="translate(24 26) scale(1)">{icon}</g>'
               f'<text class="t" x="70" y="34">{title}</text>'
               f'<text class="s" x="70" y="53">{sub}</text></g>')
out.append('</svg>\n')
open(OUT, "w").write("".join(out))
