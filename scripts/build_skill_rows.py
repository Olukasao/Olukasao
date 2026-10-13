# Gera as linhas de ícones da seção Stack (assets/skills/*.svg) no estilo do skill-icons.
# Fontes: github.com/tandpfun/skill-icons (clone em EXT/skill-icons) e os pacotes npm
# simple-icons, devicon e lucide-static (em EXT/npmi/node_modules).
# Uso: python3 scripts/build_skill_rows.py EXT assets/skills '{"linha": ["React", "gsap", ...]}'
import re, sys, json, os
EXT = sys.argv[1]; OUT = sys.argv[2]
SKI = f"{EXT}/skill-icons/icons"; DEV = f"{EXT}/npmi/node_modules/devicon/icons"
LUC = f"{EXT}/npmi/node_modules/lucide-static/icons"; SI = f"{EXT}/npmi/node_modules/simple-icons/icons"
BG = '<rect width="256" height="256" rx="60" fill="#242938"/>'

def inner(svg):
    svg = re.sub(r'<!--.*?-->', '', svg, flags=re.S)
    return re.sub(r'^.*?<svg[^>]*>|</svg>\s*$', '', svg.strip(), flags=re.S)

def tile(body):
    return f'<svg width="256" height="256" viewBox="0 0 256 256" fill="none" xmlns="http://www.w3.org/2000/svg">{BG}{body}</svg>'

def si(slug, color, size=140):
    d = re.search(r' d="([^"]+)"', open(f"{SI}/{slug}.svg").read()).group(1)
    s = size/24; o = (256-size)/2
    return tile(f'<g transform="translate({o} {o}) scale({s})"><path fill="#{color}" d="{d}"/></g>')

def dev(name, size=150):
    s = size/128; o = (256-size)/2
    return tile(f'<g transform="translate({o} {o}) scale({s})">{inner(open(f"{DEV}/{name}").read())}</g>')

def luc(name, color, size=140):
    s = size/24; o = (256-size)/2
    return tile(f'<g transform="translate({o} {o}) scale({s})" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{inner(open(f"{LUC}/{name}.svg").read())}</g>')

def text(t, color, size):
    return tile(f'<text x="128" y="128" dominant-baseline="central" text-anchor="middle" font-family="Segoe UI,Helvetica,Arial,sans-serif" font-weight="800" font-size="{size}" fill="{color}">{t}</text>')

systemd = tile('<g fill="none" stroke="#FFFFFF" stroke-width="16" stroke-linecap="square">'
               '<path d="M86 70H58V186H86"/><path d="M170 70H198V186H170"/></g>'
               '<circle cx="128" cy="128" r="26" fill="#30D475"/>')

CUSTOM = {
  "sql": luc("database", "#4DA3FF", 170),
  "framermotion": si("framer", "FFFFFF", 135),
  "gsap": si("gsap", "0AE448", 185),
  "leaflet": si("leaflet", "199900"),
  "fastify": si("fastify", "FFFFFF"),
  "socketio": si("socketdotio", "FFFFFF"),
  "mariadb": si("mariadb", "C49A6C", 150),
  "zod": si("zod", "408AFF"),
  "playwright": dev("playwright/playwright-original.svg", 170),
  "hostinger": si("hostinger", "8C6BFF", 130),
  "pm2": si("pm2", "FFFFFF", 150),
  "systemd": systemd,
  "ssh": luc("square-terminal", "#4FD1C5", 170),
  "vps": luc("server", "#A78BFA", 170),
  "vegas": si("vegas", "FFFFFF", 200),
}

def icon(name):
    if name in CUSTOM: return CUSTOM[name]
    for f in (f"{name}-Dark.svg", f"{name}.svg"):
        if os.path.exists(f"{SKI}/{f}"): return open(f"{SKI}/{f}").read()
    raise SystemExit(f"sem ícone: {name}")

def row(names):
    parts = []
    for i, n in enumerate(names):
        body = inner(icon(n))
        # prefixa ids para não colidir entre ícones
        p = f"i{i}_"
        body = re.sub(r'id="([^"]+)"', lambda m: f'id="{p}{m.group(1)}"', body)
        body = re.sub(r'url\(#([^)]+)\)', lambda m: f'url(#{p}{m.group(1)})', body)
        body = re.sub(r'href="#([^"]+)"', lambda m: f'href="#{p}{m.group(1)}"', body)
        parts.append(f'<svg x="{i*300}" width="256" height="256" viewBox="0 0 256 256" fill="none">{body}</svg>')
    w = len(names)*300 - 44
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w*48/256:.0f}" height="48" viewBox="0 0 {w} 256" fill="none">' + "".join(parts) + '</svg>\n')

ROWS = json.loads(sys.argv[3])
os.makedirs(OUT, exist_ok=True)
for k, names in ROWS.items():
    open(f"{OUT}/{k}.svg", "w").write(row(names))
    print(k, len(names))
