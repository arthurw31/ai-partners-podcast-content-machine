"""Mail d'annonce, version 2 (Arthur, 16/11/2026 : « repars plus sur ce style ») : on part du mail
`EPISODES/ai-corner/_communiques/select-partner/email.html` (en-tête, communiqué 3D, icônes en verre, cartes des offres)
et on y ajoute :
  1. l'en-tête fourni par Arthur (badge + « AI Partners est officiellement Partenaire de Services Select… ») ;
  2. une section « Des résultats mesurés » : 3 cartes dans le style des cartes d'offres, avec le LOGO du client à la place de l'icône ;
  3. le bloc « Ce qui ne change pas : notre indépendance » (encadré du nouveau partenaire + OpenAI, Dust, Microsoft).

Lancer depuis la racine du dépôt :  python PRESENTATIONS/2026-11_newsletter_anthropic_select/v2/build_v2.py
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
V1 = HERE.parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from clipper.newsletter import _shot, _uri  # noqa: E402

REF = ROOT / "EPISODES" / "ai-corner" / "_communiques" / "select-partner"
IMG = HERE / "images"
IMG.mkdir(exist_ok=True)
PUBLIC = "https://arthurw31.github.io/ai-partners-podcast-content-machine/newsletters/anthropic-select/v2"

F = "font-family:Helvetica, Arial, sans-serif"
TITLE, TEXT, NAVY, BORDER, BLUE, CLAUDE = "#05070F", "#141B45", "#151D53", "#D9DEEE", "#258AF3", "#D97757"


def size(p: Path, w: int, h: int) -> tuple[int, int]:
    W, H = Image.open(p).size
    k = min(w / W, h / H)
    return round(W * k), round(H * k)


def img(name: str, w: int, h: int, alt: str = "", extra: str = "") -> str:
    a, b = size(IMG / name, w, h)
    return (f'<img src="images/{name}" width="{a}" height="{b}" alt="{alt}" '
            f'style="display:block;border:0;width:{a}px;height:{b}px;{extra}">')


def h2(t: str, top: int = 14) -> str:
    return (f'<tr><td style="padding:{top}px 4px 12px 4px"><h2 style="margin:0;{F};font-size:22px;line-height:1.3;font-weight:bold;'
            f'color:{TITLE}">{t}</h2></td></tr>')


def para(t: str, pad: str = "0 4px 18px 4px") -> str:
    return f'<tr><td style="padding:{pad};{F};font-size:17px;line-height:1.7;color:{TEXT}">{t}</td></tr>'


GAP = '<td width="2%" style="width:2%;font-size:0;line-height:0">&nbsp;</td>'


def card(top: str, title: str, text: str) -> str:
    """Carte au style des cartes « Comment nous pouvons vous accompagner » (bord fin, coins arrondis, visuel centré en haut)."""
    return (f'<td valign="top" width="32%" bgcolor="#FFFFFF" style="width:32%;background-color:#FFFFFF;border:1px solid {BORDER};'
            f'border-radius:18px;padding:18px 16px 22px 16px">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td height="96" align="center" valign="middle" '
            f'style="height:96px">{top}</td></tr></table>'
            f'<div style="padding:16px 0 8px 0;{F};font-size:18px;line-height:1.25;font-weight:bold;color:{TITLE}">{title}</div>'
            f'<div style="{F};font-size:15px;line-height:1.55;color:{TEXT}">{text}</div></td>')


def clients() -> str:
    cards = [("client_loreal.png", "L'Oréal", "150 experts tech et produit formés en trois jours de build."),
             ("client_isagri.png", "ISAGRI", "Une chaîne de développement en production sur Claude Code, désormais utilisée au "
                                            "quotidien par les équipes produit."),
             ("client_trench.png", "Trench Group", "12 applications construites en trois jours, dont 3 en production, qui économisent "
                                                   "plus de 200 heures de travail par an.")]
    cells = GAP.join(card(img(f, 130, 34, n, "margin:0 auto"), n, t) for f, n, t in cards)
    return (h2("Des résultats mesurés")
            + para("Sur nos 3 références publiques&nbsp;:", "0 4px 14px 4px")
            + f'<tr><td style="padding:4px 4px 34px 4px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
              f'style="border-collapse:separate"><tr>{cells}</tr></table></td></tr>')


def independence() -> str:
    def partner(f, title, w, h):
        return (f'<td width="32%" valign="top" align="center" bgcolor="#FFFFFF" style="width:32%;border:1px solid {BORDER};border-radius:18px;'
                f'padding:16px 6px 18px 6px;{F};text-align:center">'
                f'<div style="font-size:14px;line-height:1.3;font-weight:bold;color:{TITLE}">{title}</div>'
                f'<table role="presentation" align="center" cellpadding="0" cellspacing="0" style="margin:10px auto 12px auto"><tr>'
                f'<td width="50" height="2" bgcolor="{BLUE}" style="width:50px;height:2px;font-size:0;line-height:0">&nbsp;</td></tr></table>'
                f'<table role="presentation" align="center" cellpadding="0" cellspacing="0"><tr><td height="56" valign="middle" align="center" '
                f'style="height:56px">{img(f, w, h, title)}</td></tr></table></td>')
    new = (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:separate"><tr>'
           f'<td bgcolor="{NAVY}" align="center" style="background-color:{NAVY};border:2px solid {BLUE};border-radius:18px;'
           f'padding:22px 20px 26px 20px;{F};text-align:center">'
           f'<div style="font-size:12px;line-height:1;font-weight:bold;letter-spacing:.16em;color:#5CA8FF">NOUVEAU PARTENAIRE</div>'
           f'<div style="font-size:20px;line-height:1.3;font-weight:bold;color:#FFFFFF;padding:8px 0 16px 0">Select Services Partner<br>'
           f'du <span style="color:{CLAUDE}">Claude Partner Network</span></div>'
           f'<table role="presentation" align="center" cellpadding="0" cellspacing="0"><tr><td align="center">'
           f'{img("partenaire_anthropic.png", 330, 110, "Select Services Partner, Claude Partner Network")}</td></tr></table></td></tr></table>')
    small = (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:separate"><tr>'
             f'{partner("partenaire_openai.png", "OpenAI Select Partner", 124, 54)}{GAP}{partner("partenaire_dust.png", "Dust Partner", 130, 46)}'
             f'{GAP}{partner("partenaire_microsoft.png", "Microsoft Partner", 120, 30)}</tr></table>')
    return (h2("Ce qui ne change pas&nbsp;: notre indépendance")
            + para("Ce statut renforce notre expertise sur Claude, sans rien changer à notre position. AI Partners reste indépendant et "
                   "agnostique. Nous sommes également partenaires d'OpenAI, de Dust et de Microsoft.", "0 4px 16px 4px")
            + f'<tr><td style="padding:0 4px">{new}<div style="height:12px;font-size:0;line-height:0">&nbsp;</div>{small}</td></tr>'
            + para("Nous ne percevons aucune commission d'apport de la part des éditeurs. Notre seul critère reste votre besoin réel&nbsp;: "
                   "nous vous recommandons la solution la plus adaptée, y compris quand ce n'est pas Claude. "
                   f'<strong style="color:{TITLE}">Je m\'y engage personnellement.</strong>', "18px 4px 34px 4px"))


def images() -> None:
    for p in (REF / "images").iterdir():                      # images du mail de référence
        if p.suffix in (".png", ".jpg") and not p.name.startswith("_"):
            shutil.copy2(p, IMG / p.name)
    for n in ("client_loreal.png", "client_isagri.png", "client_trench.png", "partenaire_anthropic.png", "partenaire_openai.png",
              "partenaire_dust.png", "partenaire_microsoft.png"):
        shutil.copy2(V1 / "images" / n, IMG / n)
    head = Image.open(HERE / "sources" / "entete_fourni.webp").convert("RGB")   # en-tête fourni par Arthur (1280 × 720)
    head.save(IMG / "entete_select.jpg", quality=90)
    (IMG / "hero.png").unlink(missing_ok=True)


def build() -> str:
    h = (REF / "email.html").read_text(encoding="utf-8")
    h = h.replace('src="images/hero.png"', 'src="images/entete_select.jpg"')
    h = h.replace('alt="AI Partners est désormais partenaire Select du Claude Partner Network, le programme qui réunit les sociétés de '
                  'services déployant Claude chez leurs clients"',
                  'alt="AI Partners est officiellement Partenaire de Services Select au sein du Claude Partner Network"')
    a = h.index('<tr><td style="padding:0 4px 12px 4px"><h2 style="margin:0;font-family:Helvetica, Arial, sans-serif;font-size:22px;'
                'line-height:1.3;font-weight:bold;color:#05070F">Ce que cela change pour vous')
    h = h[:a] + clients() + h[a:]
    b = h.index('<tr><td style="padding:14px 4px 12px 4px"><h2 style="margin:0;font-family:Helvetica, Arial, sans-serif;font-size:22px;'
                'line-height:1.3;font-weight:bold;color:#05070F">Comment nous pouvons vous accompagner')
    return h[:b] + independence() + h[b:]


def module(h: str) -> str:
    """Module HubSpot : sans html / head / body, images en adresses absolues (GitHub Pages)."""
    body = h[h.index('<table role="presentation" width="100%"'):h.rindex("</body>")]
    return body.replace('src="images/', f'src="{PUBLIC}/').strip() + "\n"


def preview(h: str, width: int, out: Path, inner: int = 640) -> None:
    page = h.replace('src="images/', f'src="{_uri(IMG)}/').replace("max-width:640px;text-align:left", f"max-width:{inner}px;text-align:left")
    tmp = HERE / "_tmp.png"
    _shot(page, width, 7000, tmp)
    from PIL import ImageChops
    im = Image.open(tmp).convert("RGB")
    box = ImageChops.difference(im, Image.new("RGB", im.size, im.getpixel((0, im.height - 1)))).getbbox()   # ligne entière, pas le centre
    im.crop((0, 0, im.width, min(im.height, (box[3] if box else im.height) + 30))).save(out)
    tmp.unlink()


def main():
    images()
    h = build()
    if "—" in h or "–" in h:
        raise SystemExit("tiret cadratin dans le mail")
    (HERE / "email.html").write_text(h, encoding="utf-8")
    (HERE / "email_hubspot_module.html").write_text(module(h), encoding="utf-8")
    shutil.copy2(REF / "objet.txt", HERE / "objet.txt")
    (HERE / "preheader.txt").write_text("Plus qu'une annonce : ce que ce statut signifie, et ce qu'il change pour vos projets.\n",
                                        encoding="utf-8")
    preview(h, 700, HERE / "apercu.png")
    preview(h, 520, HERE / "apercu_hubspot_480px.png", 480)
    used = sorted(set(re.findall(r'src="images/([^"]+)"', h)))
    print("images utilisées :", ", ".join(used))


if __name__ == "__main__":
    main()
