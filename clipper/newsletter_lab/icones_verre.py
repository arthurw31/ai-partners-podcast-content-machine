"""Icônes « verre 3D » dans le style EXACT des formes du site weareaipartners.com (A, losange, barre de la section « Our Approach ») :
des SOLIDES pleins (pas des traits) à face avant blanche et dépolie, tranche épaisse bleu translucide visible en bas à droite, liseré bleu,
halo bleu au pied de la forme, reflet blanc en haut à gauche, légère perspective. Détails (coche, guillemets…) gravés en creux dans la face.
Arthur, 10/11/2026 : « garde ceux qui existent pour nos trois offres ; pour le reste, crée toi-même des images dans le même style mais qui ont
du sens », puis « fais vraiment dans le même style que les composants que je t'ai donnés ».
Dessinées ici (formes géométriques simples, comme le A / losange / barre), aucune image du site recopiée.

python -m clipper.newsletter_lab.icones_verre   -> MARQUES/ai-corner/assets/icones_verre/<nom>.png + _planche.png (avec les formes du site)
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "MARQUES" / "ai-corner" / "assets" / "icones_verre"
SITE = ROOT / "MARQUES" / "ai-corner" / "assets" / "formes_site"

# Silhouettes pleines (viewBox 200 x 200) et détails gravés, par icône. « fill-rule » evenodd pour les anneaux.
FORMES = {
    "badge-check": ('<circle cx="100" cy="94" r="62"/>',
                    '<path d="M70 95 L92 117 L132 74"/>'),
    "server": ('<rect x="38" y="36" width="124" height="54" rx="20"/><rect x="38" y="110" width="124" height="54" rx="20"/>',
               '<path d="M64 63 h0 M64 137 h0 M92 63 h44 M92 137 h44"/>'),
    "message-square-quote": ('<rect x="32" y="38" width="136" height="98" rx="26"/><path d="M58 128 L58 170 L100 132 Z"/>',
                             '<path d="M92 70 l-18 17 l18 17 M126 70 l-18 17 l18 17"/>'),
    "users": ('<circle cx="132" cy="70" r="21"/><path d="M98 162 a36 36 0 0 1 70 0 Z"/><circle cx="80" cy="66" r="26"/><path d="M34 164 a46 46 0 0 1 92 0 Z"/>',
              ''),
    "rocket": ('<path d="M156 44 L156 118 L130 92 L72 150 L50 128 L108 70 L82 44 Z"/>', ''),
    "target": ('<path fill-rule="evenodd" d="M100 30 a64 64 0 1 1 -0.1 0 Z M100 56 a38 38 0 1 0 0.1 0 Z"/><circle cx="100" cy="94" r="17"/>', ''),
    "layers": ('<path d="M100 98 L164 132 L100 166 L36 132 Z"/><path d="M100 66 L164 100 L100 134 L36 100 Z"/><path d="M100 34 L164 68 L100 102 L36 68 Z"/>', ''),
}


# Palettes : « verre » = formes du site (blanc translucide) ; « bleu » = EXACTEMENT le même verre, mais translucide BLEU (Arthur, 10/11/2026 :
# « refais exactement pareil, mais au lieu que nos icônes soient translucides blanches, mets-les en translucide bleu »).
THEMES = {
    "verre": dict(t=("#E6E9FF", "#AEBAFB", "#6F82F0"), f=("#FBFBFD", "#EEEFF5", "#E1E4F3"), halo="#4F62EE", rim="#A3B0F8",
                  g=("#FFFFFF", "#93A2F8", "#C6CEFC")),
    "bleu": dict(t=("#9DB7FF", "#5E83F2", "#3557DC"), f=("#DCE7FF", "#A9C2FF", "#7C9DF8"), halo="#3E63EC", rim="#C7D7FF",
                 g=("#FFFFFF", "#5677EE", "#B9CBFF")),
}


def solide(nom: str, px: int = 240, tilt: tuple = (10, -14), theme: str = "verre") -> Path:
    """Icône `nom` en verre 3D plein, carré de `px` px sur fond blanc -> OUT/[bleu/]<nom>.png."""
    from .piste_nouveau import _render
    corps, gravure = FORMES[nom]
    c = THEMES[theme]
    ext = "".join(f'<g transform="translate({i * 0.5:.2f} {i * 0.85:.2f})" fill="url(#tranche)" fill-opacity=".85">{corps}</g>' for i in range(9, 0, -1))
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="10 10 190 190" width="{px}" height="{px}">
<defs>
 <linearGradient id="tranche" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c['t'][0]}"/><stop offset=".5" stop-color="{c['t'][1]}"/><stop offset="1" stop-color="{c['t'][2]}"/></linearGradient>
 <linearGradient id="face" x1=".1" y1="0" x2=".7" y2="1"><stop offset="0" stop-color="{c['f'][0]}"/><stop offset=".5" stop-color="{c['f'][1]}"/><stop offset="1" stop-color="{c['f'][2]}"/></linearGradient>
 <radialGradient id="halo" cx=".5" cy="1.02" r=".6"><stop offset="0" stop-color="{c['halo']}" stop-opacity=".55"/><stop offset="1" stop-color="{c['halo']}" stop-opacity="0"/></radialGradient>
 <linearGradient id="reflet" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFFFFF" stop-opacity="1"/><stop offset=".5" stop-color="#FFFFFF" stop-opacity="0"/></linearGradient>
 <clipPath id="clip">{corps}</clipPath>
 <filter id="ombre" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="7"/></filter>
 <filter id="doux" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2.2"/></filter>
</defs>
<g transform="translate(12 20)" fill="#3445C9" opacity=".16" filter="url(#ombre)">{corps}</g>
{ext}
<g fill="url(#face)" stroke="{c['rim']}" stroke-width="1.7" stroke-linejoin="round">{corps}</g>
<g clip-path="url(#clip)"><rect x="0" y="0" width="200" height="200" fill="url(#halo)" filter="url(#doux)"/>
 <g fill="none" stroke="url(#reflet)" stroke-width="5" transform="translate(-2.5 -3)">{corps}</g></g>
<g fill="none" stroke-linecap="round" stroke-linejoin="round">
 <g stroke="{c['g'][0]}" stroke-width="15" transform="translate(1.6 2.2)">{gravure}</g>
 <g stroke="{c['g'][1]}" stroke-width="13">{gravure}</g>
 <g stroke="{c['g'][2]}" stroke-width="7" transform="translate(1 1.5)">{gravure}</g>
</g>
</svg>"""
    page = (f"<html><body style='margin:0;background:#fff'><div style='width:{px}px;height:{px}px;perspective:{px * 4}px'>"
            f"<div style='width:100%;height:100%;transform:rotateX({tilt[0]}deg) rotateY({tilt[1]}deg) scale(.82)'>{svg}</div></div></body></html>")
    d = OUT if theme == "verre" else OUT / theme
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{nom}.png"
    _render(page, px, px, f)
    return f


glass = solide          # ancien nom, utilisé par piste_select.py


def forme_bleue(src: Path, out: Path) -> Path:
    """Forme du site (A, losange, barre) passée en verre translucide BLEU : luminance -> dégradé bleu, fond blanc gardé."""
    import numpy as np
    from PIL import Image, ImageFilter, ImageOps
    im = Image.open(src).convert("RGB")
    a = np.asarray(im).astype("float32")
    dist = np.clip((255 - a.min(axis=2)) / 40.0, 0, 1)                       # 0 = fond blanc, 1 = forme
    mask = Image.fromarray((dist * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(.6))
    lum = ImageOps.autocontrast(ImageOps.grayscale(im), cutoff=1)
    col = ImageOps.colorize(lum, black=(44, 79, 214), mid=(111, 149, 247), white=(214, 227, 255), midpoint=150)
    Image.composite(col, Image.new("RGB", im.size, "white"), mask).save(out)
    return out


if __name__ == "__main__":
    from PIL import Image
    files = [solide(n) for n in FORMES] + [solide(n, theme="bleu") for n in FORMES]
    refs = [SITE / f"forme_{k}.png" for k in ("A", "losange", "barre")]
    n = len(FORMES)
    sheet = Image.new("RGB", (240 * n, 720), "white")
    for i, f in enumerate(files):
        sheet.paste(Image.open(f).convert("RGB"), ((i % n) * 240, (i // n) * 240))
    for i, f in enumerate(refs):
        sheet.paste(Image.open(f).convert("RGB").resize((240, 240)), (i * 240, 480))
    sheet.save(OUT / "_planche.png")
    print(OUT / "_planche.png")
