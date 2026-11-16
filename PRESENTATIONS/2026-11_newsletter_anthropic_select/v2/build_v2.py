"""Mail d'annonce, version 2 (Arthur, 16/11/2026).

Style : celui du mail `EPISODES/ai-corner/_communiques/select-partner/email.html` (« repars plus sur ce style » : fond blanc,
640 px, icônes en verre, listes à filet bleu nuit, cartes à bord fin). Texte : la V6 de Thomas (« reprends le wording de la
dernière version de Thomas »). Ajouts d'Arthur : l'en-tête fourni (badge + « AI Partners est officiellement Partenaire de
Services Select… »), les cartes clients avec LOGO, le bloc « Ce qui ne change pas » (OpenAI, Dust, Google). Retirés : le
communiqué de presse et son lien, la section AI Factory / AI First Organization / AI Academy, le bouton d'agenda (remplacé
par « Répondez simplement à ce mail »).

Lancer depuis la racine du dépôt :  python PRESENTATIONS/2026-11_newsletter_anthropic_select/v2/build_v2.py
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageChops

HERE = Path(__file__).resolve().parent
V1 = HERE.parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from clipper.newsletter import _shot, _uri  # noqa: E402

REF = ROOT / "EPISODES" / "ai-corner" / "_communiques" / "select-partner"
IMG = HERE / "images"
IMG.mkdir(exist_ok=True)
PUBLIC = "https://arthurw31.github.io/ai-partners-podcast-content-machine/newsletters/anthropic-select/v2"

SUBJECT = "AI Partners devient partenaire Select du Claude Partner Network"
PREHEADER = "Une reconnaissance d'Anthropic, et ce qu'elle change pour vos projets IA."
F = "font-family:Helvetica, Arial, sans-serif"
TITLE, TEXT, NAVY, BORDER, BLUE, CLAUDE = "#05070F", "#141B45", "#151D53", "#D9DEEE", "#258AF3", "#D97757"
GAP = '<td width="2%" style="width:2%;font-size:0;line-height:0">&nbsp;</td>'


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


def strong(t: str) -> str:
    return f'<strong style="color:{TITLE}">{t}</strong>'


def card(top: str, title: str, text: str) -> str:
    """Carte au style des cartes d'offres du mail de référence (bord fin, coins arrondis, visuel centré en haut)."""
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
    return (f'<tr><td style="padding:4px 4px 34px 4px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'style="border-collapse:separate"><tr>{cells}</tr></table></td></tr>')


def stats() -> str:
    """Les 3 chiffres dans 3 encadrés côte à côte, comme les cartes clients, sans icône (Arthur, 16/11/2026)."""
    data = [("12", "experts certifiés par Anthropic"), ("5", "déploiements clients validés par Anthropic"),
            ("3", "références publiques")]
    cells = GAP.join(
        f'<td valign="top" width="32%" align="center" bgcolor="#FFFFFF" style="width:32%;background-color:#FFFFFF;border:1px solid {BORDER};'
        f'border-radius:18px;padding:22px 12px 22px 12px;text-align:center"><div style="{F};font-size:44px;line-height:1;font-weight:bold;'
        f'color:{NAVY}">{n}</div><div style="padding-top:10px;{F};font-size:15px;line-height:1.5;color:{TEXT}">{t}</div></td>'
        for n, t in data)
    return (f'<tr><td style="padding:6px 4px 26px 4px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'style="border-collapse:separate"><tr>{cells}</tr></table></td></tr>')


def bar_list(items: list) -> str:
    """Liste à filet bleu nuit à gauche, icône en verre devant chaque point (style « Ce que cela change pour vous » de la référence)."""
    # icône dans sa propre colonne, texte dans la colonne de droite : aucune ligne ne repasse sous l'icône (Arthur, 16/11/2026)
    rows = []
    for k, (icon, lead, text) in enumerate(items):
        bottom = "0" if k == len(items) - 1 else "18px"
        rows.append(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
                    f'<td valign="top" width="52" style="width:52px;padding:0 10px 0 0"><img src="images/{icon}" width="42" height="42" '
                    f'alt="" style="display:block;border:0;width:42px;height:42px;margin-top:-6px"></td>'
                    f'<td valign="top" style="padding:0 0 {bottom} 0;{F};font-size:17px;line-height:1.65;color:{TEXT}">'
                    f'{strong(lead)} {text}</td></tr></table>')
    return (f'<tr><td style="padding:0 4px 26px 4px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
            f'<td style="border-left:4px solid {NAVY};padding:2px 0 2px 22px;{F};font-size:17px;line-height:1.65;color:{TEXT}">'
            + "".join(rows) + "</td></tr></table></td></tr>")


def independence() -> str:
    def partner(f, title, w, h):
        return (f'<td width="32%" valign="top" align="center" bgcolor="#FFFFFF" style="width:32%;border:1px solid {BORDER};border-radius:18px;'
                f'padding:16px 6px 18px 6px;{F};text-align:center">'
                f'<div style="font-size:14px;line-height:1.3;font-weight:bold;color:{TITLE}">{title}</div>'
                f'<table role="presentation" align="center" cellpadding="0" cellspacing="0" style="margin:10px auto 12px auto"><tr>'
                f'<td width="50" height="2" bgcolor="{BLUE}" style="width:50px;height:2px;font-size:0;line-height:0">&nbsp;</td></tr></table>'
                f'<table role="presentation" align="center" cellpadding="0" cellspacing="0"><tr><td height="56" valign="middle" align="center" '
                f'style="height:56px">{img(f, w, h, title)}</td></tr></table></td>')
    # encadré du nouveau partenaire = une image, sur le MÊME fond que l'en-tête (dégradé bleu grainé ; Arthur, 16/11/2026) :
    # un dégradé CSS n'est pas gardé par Gmail / Outlook, l'image l'est partout
    new = img("encadre_nouveau_partenaire.png", 592, 400, "Nouveau partenaire : Select Services Partner du Claude Partner Network",
              "width:100%;max-width:592px;height:auto")
    small = (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:separate"><tr>'
             f'{partner("partenaire_openai.png", "OpenAI Select Partner", 124, 54)}{GAP}{partner("partenaire_dust.png", "Dust Partner", 130, 46)}'
             f'{GAP}{partner("partenaire_google.png", "Google Cloud Partner", 110, 56)}</tr></table>')
    return (h2("Ce qui ne change pas&nbsp;: notre indépendance", 0)
            + para("Ce statut renforce notre expertise sur Claude, sans rien changer à notre position. AI Partners reste indépendant et "
                   "agnostique. Nous sommes également partenaires d'OpenAI, de Dust et de Google.", "0 4px 16px 4px")
            + f'<tr><td style="padding:0 4px">{new}<div style="height:12px;font-size:0;line-height:0">&nbsp;</div>{small}</td></tr>'
            + para("Nous ne percevons aucune commission d'apport de la part des éditeurs. Notre seul critère reste votre besoin réel&nbsp;: "
                   "nous vous recommandons la solution la plus adaptée, y compris quand ce n'est pas Claude. "
                   + strong("Je m'y engage personnellement."), "18px 4px 34px 4px"))


FONTS = ROOT / "MARQUES" / "ai-corner" / "assets" / "fonts"


def partner_box(out: Path) -> Path:
    """Encadré « Nouveau partenaire » rendu par Chrome (1184 px = 2 x 592) : dégradé bleu grainé repris des couleurs de l'en-tête
    fourni (bleu nuit en bas à gauche, bleu clair en haut à droite), titre blanc, « Claude Partner Network » sur pavé orange
    comme dans l'en-tête, badge officiel à plat."""
    css = "".join(f'@font-face{{font-family:M;src:url("{_uri(FONTS / f"Metropolis-{n}.ttf")}");font-weight:{w}}}'
                  for n, w in (("Regular", 400), ("Bold", 700), ("ExtraBold", 800)))
    noise = ("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='n'>"
             "<feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/></filter>"
             "<rect width='100%25' height='100%25' filter='url(%23n)' opacity='.55'/></svg>")
    page = f"""<html><head><meta charset='utf-8'><style>{css}*{{margin:0;box-sizing:border-box}}
body{{width:1184px;height:500px;background:#FFFFFF}}
.box{{position:relative;width:1184px;height:500px;border-radius:36px;overflow:hidden;text-align:center;font-family:M,Arial;
background:linear-gradient(32deg,#12203A 0%,#082E72 28%,#0A4B9C 52%,#3F7BC0 76%,#93A3CE 100%)}}
.grain{{position:absolute;inset:0;background:url("{noise}");mix-blend-mode:overlay;opacity:.45}}
.in{{position:relative;padding-top:46px}}
.k{{font-weight:700;font-size:24px;letter-spacing:.2em;color:#FFFFFF;opacity:.85}}
h1{{font-weight:800;font-size:46px;line-height:1.25;color:#FFFFFF;margin:14px 0 30px}}
h1 span{{background:#F28A32;padding:0 12px}}
.badge{{height:200px;display:block;margin:0 auto}}
</style></head><body><div class='box'><div class='grain'></div><div class='in'><div class='k'>NOUVEAU PARTENAIRE</div>
<h1>Select Services Partner<br>du <span>Claude Partner Network</span></h1>
<img class='badge' src='{_uri(IMG / "partenaire_anthropic.png")}'></div></div></body></html>"""
    _shot(page, 1184, 500, out)
    return out


def images() -> None:
    for p in (REF / "images").iterdir():                      # images du mail de référence (icônes en verre, photo de Thomas)
        if p.suffix in (".png", ".jpg") and not p.name.startswith("_"):
            shutil.copy2(p, IMG / p.name)
    for n in ("client_loreal.png", "client_isagri.png", "client_trench.png", "partenaire_anthropic.png", "partenaire_openai.png",
              "partenaire_dust.png", "partenaire_google.png"):
        shutil.copy2(V1 / "images" / n, IMG / n)
    head = Image.open(HERE / "sources" / "entete_fourni.webp").convert("RGB")   # en-tête fourni par Arthur (1280 × 720)
    head.save(IMG / "entete_select.jpg", quality=90)
    partner_box(IMG / "encadre_nouveau_partenaire.png")
    (IMG / "hero.png").unlink(missing_ok=True)


def build() -> str:
    hero = ('<tr><td style="padding:0"><img src="images/entete_select.jpg" width="640" alt="AI Partners est officiellement Partenaire '
            'de Services Select au sein du Claude Partner Network" style="display:block;width:100%;max-width:640px;height:auto;border:0">'
            '</td></tr>')
    sig = (f'<tr><td style="padding:0 4px"><table role="presentation" cellpadding="0" cellspacing="0"><tr>'
           f'<td valign="middle" width="100" style="width:100px;padding:0 18px 0 0"><img src="images/thomas_portrait.jpg" width="84" '
           f'height="84" alt="Thomas Spitz" style="display:block;border:0;border-radius:42px;width:84px;height:84px"></td>'
           f'<td valign="middle" style="{F};font-size:17px;line-height:1.7;color:{TEXT}">{strong("Thomas Spitz")}<br>'
           f'<span style="color:#4A5683">Co-founder &amp; CEO, AI Partners</span></td></tr></table></td></tr>')
    rows = [
        para("Bonjour,", "34px 4px 14px 4px"),
        para("Je tenais à vous partager une étape importante pour AI Partners&nbsp;: nous avons obtenu le statut de "
             + strong("partenaire Select du Claude Partner Network") + " (Services Track), le programme d'Anthropic dédié aux sociétés "
             "qui déploient Claude, powered by Anthropic, chez leurs clients.", "0 4px 14px 4px"),
        para("Ce statut valide une pratique Claude éprouvée sur le terrain&nbsp;: des équipes certifiées, des clients en production et "
             "des cas publics. Cette reconnaissance vient consacrer deux années de travail aux côtés de nos clients, et une conviction "
             "qui ne m'a pas quitté depuis la création d'AI Partners&nbsp;: la valeur de l'IA se joue en production, au-delà des pilotes.",
             "0 4px 30px 4px"),
        h2("Une expertise reconnue, et déjà à l'œuvre chez nos clients", 0),
        stats(),
        bar_list([("verre_users_42.png", "Des experts qui pratiquent.", "Nos consultants et ingénieurs utilisent Claude au quotidien, "
                   "y compris Claude Code dans notre propre ingénierie."),
                  ("verre_rocket_42.png", "Des projets en production.", "Nos 5 déploiements clients validés par Anthropic vont au-delà "
                   "des POC et des expérimentations.")]),
        para(strong("Des résultats mesurés") + ", sur 3 références publiques&nbsp;:", "0 4px 14px 4px"),
        clients(),
        independence(),
        h2("Ce que nous pouvons faire pour vous", 0),
        bar_list([("verre_target_42.png", "Stratégie et gouvernance&nbsp;:", "identifier les cas d'usage où l'IA crée réellement de "
                   "la valeur, et poser le cadre de sécurité et de gouvernance pour passer à l'échelle."),
                  ("verre_rocket_42.png", "Build et production&nbsp;:", "concevoir, déployer et industrialiser des agents au cœur de "
                   "vos processus métier."),
                  ("verre_layers_42.png", "Déploiement de Claude Enterprise et Claude Team&nbsp;:", "configurer les accès, les niveaux "
                   "d'usage et l'administration, puis faire adopter l'outil par vos équipes. Sur certains déploiements Claude Enterprise, "
                   "Anthropic peut cofinancer une partie de l'accompagnement à l'adoption, sous réserve d'éligibilité déterminée par "
                   "Anthropic. Nous vous indiquons si votre projet peut en bénéficier."),
                  ("verre_users_42.png", "Adoption et montée en compétences&nbsp;:", "des programmes de build où vos équipes construisent "
                   "leurs propres usages, de Claude Cowork aux équipes de développement sur Claude Code.")]),
        h2("Parlons de vos projets", 8),
        para("Vous avez un pilote à faire passer en production, un déploiement Claude à réussir, ou un cas d'usage à cadrer&nbsp;? "
             "Je vous propose un échange de 30 minutes avec l'un de nos experts.", "0 4px 16px 4px"),
        f'<tr><td style="padding:0 4px 30px 4px;{F};font-size:19px;line-height:1.4;font-weight:bold;color:{NAVY}">'
        f'Répondez simplement à ce mail &rarr;</td></tr>',
        para("Merci pour votre confiance. C'est avec vous que cette étape s'est construite.", "0 4px 22px 4px"),
        sig,
    ]
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light"><title>{SUBJECT}</title></head>
<body style="margin:0;padding:0;background:#FFFFFF">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{PREHEADER}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#FFFFFF"><tr><td align="center" style="padding:0">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="width:100%;max-width:640px;text-align:left">
{hero}
<tr><td style="padding:0 20px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">
{chr(10).join(rows)}
</table></td></tr>
<tr><td height="56" style="font-size:0;line-height:0">&nbsp;</td></tr>
</table></td></tr></table></body></html>"""


def module(h: str) -> str:
    """Module HubSpot : sans html / head / body, images en adresses absolues (GitHub Pages)."""
    body = h[h.index('<table role="presentation" width="100%"'):h.rindex("</body>")]
    return body.replace('src="images/', f'src="{PUBLIC}/').strip() + "\n"


def preview(h: str, width: int, out: Path, inner: int = 640) -> None:
    page = h.replace('src="images/', f'src="{_uri(IMG)}/').replace("max-width:640px;text-align:left", f"max-width:{inner}px;text-align:left")
    tmp = HERE / "_tmp.png"
    _shot(page, width, 7000, tmp)
    im = Image.open(tmp).convert("RGB")
    box = ImageChops.difference(im, Image.new("RGB", im.size, im.getpixel((0, im.height - 1)))).getbbox()   # ligne entière
    im.crop((0, 0, im.width, min(im.height, (box[3] if box else im.height) + 30))).save(out)
    tmp.unlink()


def main():
    images()
    h = build()
    if "—" in h or "–" in h:
        raise SystemExit("tiret cadratin dans le mail")
    (HERE / "email.html").write_text(h, encoding="utf-8")
    (HERE / "email_hubspot_module.html").write_text(module(h), encoding="utf-8")
    (HERE / "objet.txt").write_text(SUBJECT + "\n", encoding="utf-8")
    (HERE / "preheader.txt").write_text(PREHEADER + "\n", encoding="utf-8")
    preview(h, 700, HERE / "apercu.png")
    preview(h, 520, HERE / "apercu_hubspot_480px.png", 480)
    used = sorted(set(re.findall(r'src="images/([^"]+)"', h)))
    print("images utilisées :", ", ".join(used))


if __name__ == "__main__":
    main()
