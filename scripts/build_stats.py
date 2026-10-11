"""Gera os cards de estatísticas do GitHub (stats.svg e languages.svg).

Roda no GitHub Actions (workflow stats.yml) com o GITHUB_TOKEN e grava em
dist/. Os cards têm fundo transparente, detalhes no roxo do perfil e texto
que se adapta ao tema claro/escuro.

Uso: GITHUB_TOKEN=... python3 scripts/build_stats.py <usuario> [pasta_saida]
"""
import json
import os
import sys
import urllib.request
from html import escape
from pathlib import Path

ACCENT = "#A020F0"
W, H = 440, 200

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar { totalContributions }
    }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""

STYLE = f"""
    .card {{ fill: none; stroke: {ACCENT}; stroke-opacity: .35; }}
    .title {{ font: 700 17px 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; fill: {ACCENT}; }}
    .label {{ font: 500 13px 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; fill: #59636e; }}
    .value {{ font: 700 14px 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; fill: #1f2328; }}
    .icon {{ fill: {ACCENT}; }}
    .track {{ fill: #8b949e; fill-opacity: .2; }}
    .row {{ opacity: 0; animation: in .5s ease-out forwards; }}
    @keyframes in {{ from {{ opacity: 0; transform: translateX(-6px); }} to {{ opacity: 1; transform: none; }} }}
    .grow {{ transform-box: fill-box; transform-origin: left; animation: grow 1s cubic-bezier(.2,.8,.2,1) forwards; transform: scaleX(0); }}
    @keyframes grow {{ to {{ transform: scaleX(1); }} }}
    @media (prefers-color-scheme: dark) {{
      .title {{ fill: #c27bff; }}
      .label {{ fill: #9198a1; }}
      .value {{ fill: #f0f6fc; }}
    }}"""


def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(f"GraphQL: {data['errors']}")
    return data["data"]["user"]


def svg(title, body, label):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(label)}">
  <style>{STYLE}
  </style>
  <rect class="card" x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16"/>
  <text class="title" x="24" y="38">{title}</text>
{body}
</svg>
'''


def stats_card(user):
    c = user["contributionsCollection"]
    repos = user["repositories"]
    rows = [
        ("Contribuições no ano", c["contributionCalendar"]["totalContributions"]),
        ("Commits no ano", c["totalCommitContributions"]),
        ("Pull requests", c["totalPullRequestContributions"]),
        ("Issues", c["totalIssueContributions"]),
        ("Repositórios públicos", repos["totalCount"]),
        ("Estrelas recebidas", sum(n["stargazerCount"] for n in repos["nodes"])),
    ]
    body = []
    for i, (label, value) in enumerate(rows):
        col, line = divmod(i, 3)
        x, y = 24 + col * 208, 78 + line * 38
        body.append(f'''  <g class="row" style="animation-delay:{i * 0.08:.2f}s">
    <circle class="icon" cx="{x + 5}" cy="{y - 5}" r="4"/>
    <text class="label" x="{x + 18}" y="{y}">{label}</text>
    <text class="value" x="{x + 18}" y="{y + 18}">{value:,}</text>
  </g>'''.replace(f"{value:,}", f"{value:,}".replace(",", ".")))
    return svg("Estatísticas do GitHub", "\n".join(body),
               "Estatísticas do GitHub: " + ", ".join(f"{l} {v}" for l, v in rows))


def languages_card(user, top=6):
    sizes = {}
    colors = {}
    for repo in user["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            name = e["node"]["name"]
            sizes[name] = sizes.get(name, 0) + e["size"]
            colors[name] = e["node"]["color"] or "#8b949e"
    total = sum(sizes.values()) or 1
    langs = sorted(sizes.items(), key=lambda kv: -kv[1])[:top]

    bar_x, bar_y, bar_w = 24, 62, W - 48
    segs, x = [], bar_x
    for name, size in langs:
        w = bar_w * size / total
        segs.append(f'<rect x="{x:.1f}" y="{bar_y}" width="{max(w, 2):.1f}" height="10" fill="{colors[name]}"/>')
        x += w
    body = [
        f'  <clipPath id="bar"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" rx="5"/></clipPath>',
        f'  <rect class="track" x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" rx="5"/>',
        f'  <g clip-path="url(#bar)"><g class="grow">{"".join(segs)}</g></g>',
    ]
    for i, (name, size) in enumerate(langs):
        col, line = divmod(i, 3)
        lx, ly = 24 + col * 208, 104 + line * 30
        body.append(f'''  <g class="row" style="animation-delay:{0.4 + i * 0.08:.2f}s">
    <circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{colors[name]}"/>
    <text class="value" x="{lx + 18}" y="{ly}">{escape(name)}</text>
    <text class="label" x="{lx + 180}" y="{ly}" text-anchor="end">{size / total * 100:.1f}%</text>
  </g>''')
    if not langs:
        body.append('  <text class="label" x="24" y="110">Sem repositórios públicos com código ainda.</text>')
    return svg("Linguagens mais usadas", "\n".join(body),
               "Linguagens mais usadas: " + ", ".join(f"{n} {s / total * 100:.1f}%" for n, s in langs))


def main():
    login = sys.argv[1]
    out = Path(sys.argv[2] if len(sys.argv) > 2 else "dist")
    out.mkdir(parents=True, exist_ok=True)
    if os.environ.get("STATS_FIXTURE"):
        user = json.loads(Path(os.environ["STATS_FIXTURE"]).read_text())
    else:
        user = fetch(login, os.environ["GITHUB_TOKEN"])
    (out / "stats.svg").write_text(stats_card(user))
    (out / "languages.svg").write_text(languages_card(user))
    print(f"cards gerados em {out}/")


if __name__ == "__main__":
    main()
