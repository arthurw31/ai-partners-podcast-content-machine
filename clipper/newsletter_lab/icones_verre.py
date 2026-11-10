"""Icônes « verre 3D » dans le style des formes du site weareaipartners.com (A, losange, barre de la section « Our Approach ») :
corps translucide blanc-lilas, tranche bleue, reflet en haut, halo bleu en bas, légère inclinaison en perspective.
Fabriquées à partir des tracés Lucide (ISC, MARQUES/ai-corner/assets/icons/) rendus en tube épais par Chrome (aucune image du site recopiée).
Arthur, 10/11/2026 : « garde ceux qui existent pour nos trois offres ; pour le reste, crée toi-même des images dans le même style mais qui ont du sens ».

python -m clipper.newsletter_lab.icones_verre   -> planche de contrôle dans MARQUES/ai-corner/assets/icones_verre/
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ICONS = ROOT / "MARQUES" / "ai-corner" / "assets" / "icons"
OUT = ROOT / "MARQUES" / "ai-corner" / "assets" / "icones_verre"


def _inner(nom: str) -> str:
    svg = (ICONS / f"lucide_{nom}.svg").read_text(encoding="utf-8")
    return re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)


EPAISSEUR = {"landmark": .72, "rocket": .78, "server": .9, "message-square-quote": .9}   # tracés détaillés : tube plus fin


def glass(nom: str, px: int = 240, tilt: tuple = (14, -18)) -> Path:
    """Icône `nom` (Lucide) en verre 3D, carré de `px` (fond blanc), enregistrée dans OUT/<nom>.png."""
    from .piste_nouveau import _render
    g = _inner(nom)
    rx, ry = tilt
    k = EPAISSEUR.get(nom, 1.0)

    def layer(stroke: str, width: float, dx: float = 0, dy: float = 0, extra: str = "") -> str:
        body = re.sub(r"<(path|circle|rect|line|polyline|polygon|ellipse)", r"<\1", g)
        return (f'<g transform="translate({dx} {dy})" fill="none" stroke="{stroke}" stroke-width="{width}" stroke-linecap="round" '
                f'stroke-linejoin="round" {extra}>{body}</g>')

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="-3 -3 30 30" width="{px}" height="{px}">
<defs>
 <linearGradient id="tranche" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#C3CCFF"/><stop offset=".55" stop-color="#7F90F5"/><stop offset="1" stop-color="#5368E8"/></linearGradient>
 <linearGradient id="corps" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFFFF"/><stop offset=".6" stop-color="#F1F2FC"/><stop offset="1" stop-color="#D6DBFB"/></linearGradient>
 <linearGradient id="reflet" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFFFFF" stop-opacity=".95"/><stop offset=".6" stop-color="#FFFFFF" stop-opacity="0"/></linearGradient>
 <filter id="ombre" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation=".9"/></filter>
 <filter id="flou" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation=".18"/></filter>
</defs>
{layer("#3B4FD8", 3.3 * k, .9, 1.4, 'opacity=".18" filter="url(#ombre)"')}
{layer("url(#tranche)", 3.5 * k, .5, .75)}
{layer("#9FADF8", 3.3 * k, 0, 0)}
{layer("url(#corps)", 2.75 * k, 0, 0, 'filter="url(#flou)"')}
{layer("url(#reflet)", 1.0 * k, -.3, -.4)}
</svg>"""
    page = (f"<html><body style='margin:0;background:#fff'><div style='width:{px}px;height:{px}px;perspective:{px * 4}px'>"
            f"<div style='width:100%;height:100%;transform:rotateX({rx}deg) rotateY({ry}deg) scale(.86)'>{svg}</div></div></body></html>")
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / f"{nom}.png"
    _render(page, px, px, f)
    return f


if __name__ == "__main__":
    from PIL import Image
    noms = ["badge-check", "server", "message-square-quote", "users", "rocket", "target", "landmark"]
    files = [glass(n) for n in noms]
    sheet = Image.new("RGB", (240 * len(files), 240), "white")
    for i, f in enumerate(files):
        sheet.paste(Image.open(f).convert("RGB"), (i * 240, 0))
    sheet.save(OUT / "_planche.png")
    print(OUT / "_planche.png")
