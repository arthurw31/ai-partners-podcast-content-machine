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


ICONS = ROOT / "MARQUES" / "ai-corner" / "assets" / "icons"


def tile_icon(name: str) -> str:
    """Pictogramme Lucide (ISC) en traits bleus sur une pastille bleu très pâle, rendu par Chrome en 2x (88 px pour 44 px affichés).
    Arthur, 16/11/2026 : des icônes qui correspondent au contenu, en haut à gauche des carrés (pas d'icônes en verre, « des emoji »)."""
    out = IMG / f"pastille_{name}.png"
    svg = (ICONS / f"lucide_{name}.svg").read_text(encoding="utf-8").replace("currentColor", BLUE)
    tmp = HERE / f"_{name}.svg"
    tmp.write_text(svg, encoding="utf-8")
    page = (f"<html><body style='margin:0;background:#FFFFFF'><div style='width:88px;height:88px;border-radius:22px;background:#EAF1FD;"
            f"display:flex;align-items:center;justify-content:center'><img src='{_uri(tmp)}' style='width:48px;height:48px'></div>"
            f"</body></html>")
    _shot(page, 88, 88, out)
    tmp.unlink()
    return out.name


def square(icon: str, inner: str) -> str:
    """Carré à bord fin, pastille d'icône en haut à gauche, contenu aligné à gauche dessous."""
    return (f'<td valign="top" width="32%" bgcolor="#FFFFFF" style="width:32%;background-color:#FFFFFF;border:1px solid {BORDER};'
            f'border-radius:18px;padding:18px 16px 22px 16px;{F};font-size:15px;line-height:1.55;color:{TEXT};text-align:left">'
            f'<img src="images/{tile_icon(icon)}" width="44" height="44" alt="" style="display:block;border:0;width:44px;height:44px;'
            f'margin:0 0 14px 0">{inner}</td>')


def row(cells: list, pad: str) -> str:
    return (f'<tr><td style="padding:{pad}"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'style="border-collapse:separate"><tr>{GAP.join(cells)}</tr></table></td></tr>')


def clients() -> str:
    # clients ANONYMISÉS : « une entreprise de tel secteur » à la place du nom et du logo (Arthur, 16/11/2026)
    data = [("graduation-cap", "Un leader mondial de la cosmétique", strong("150 experts") + " tech et produit formés en trois jours "
             "de build."),
            ("git-compare", "Un éditeur de logiciels agricoles", "Une " + strong("chaîne de développement en production") + " sur "
             "Claude Code, désormais utilisée au quotidien par les équipes produit."),
            ("zap", "Un industriel de l'équipement électrique", strong("12 applications") + " construites en trois jours, dont 3 en "
             "production, qui économisent " + strong("plus de 200 heures") + " de travail par an.")]
    return row([square(i, f'<div style="padding:0 0 10px 0;font-size:16px;line-height:1.3;font-weight:bold;color:{NAVY}">{who}</div>{t}')
                for i, who, t in data], "4px 4px 34px 4px")


def stats() -> str:
    """Les 3 chiffres dans 3 carrés, pastille d'icône en haut à gauche (Arthur, 16/11/2026)."""
    data = [("badge-check", "12", "experts certifiés par Anthropic"),
            ("rocket", "5", "déploiements clients validés par Anthropic"),
            ("message-square-quote", "3", "références publiques")]
    return row([square(i, f'<div style="font-size:44px;line-height:1;font-weight:bold;color:{NAVY}">{n}</div>'
                          f'<div style="padding-top:10px">{t}</div>') for i, n, t in data], "6px 4px 26px 4px")


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
            f'<td style="padding:2px 0 2px 0;{F};font-size:17px;line-height:1.65;color:{TEXT}">'
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
            + para("Ce statut ne change rien à notre position&nbsp;: AI Partners reste un acteur indépendant. Il nous permet en revanche "
                   "d'aller plus loin dans la maîtrise de Claude, au plus près des équipes d'Anthropic et de leurs dernières avancées.",
                   "0 4px 14px 4px")
            + para("Cette expertise, nous la mettons au service d'une seule ambition&nbsp;: vous aider à choisir la solution la plus adaptée "
                   "à vos besoins réels, et non à une technologie en particulier. C'est pourquoi ce partenariat s'inscrit dans une démarche "
                   "plus large, construite avec les acteurs de référence du marché. Il vient compléter nos partenariats avec OpenAI, Dust "
                   "et Google.", "0 4px 16px 4px")
            + f'<tr><td style="padding:0 4px 34px 4px">{new}<div style="height:12px;font-size:0;line-height:0">&nbsp;</div>{small}</td></tr>')


FONTS = ROOT / "MARQUES" / "ai-corner" / "assets" / "fonts"


def header_background(out: Path) -> Path:
    """Fond de l'en-tête fourni, À L'IDENTIQUE, sans le badge ni le texte (Arthur, 16/11/2026 : « refais exactement le même gradient,
    avec les petits points blancs légers ») : dégradé lissé (polynôme de degré 3 ajusté sur les zones vides de l'en-tête) + le VRAI
    grain de l'en-tête (résidu pris dans la bande vide du haut, recopié par blocs dans les zones masquées)."""
    import numpy as np
    im = np.asarray(Image.open(HERE / "sources" / "entete_fourni.webp").convert("RGB")).astype(float)
    H, W, _ = im.shape
    mask = np.ones((H, W), bool)
    mask[80:680, 130:450] = False                              # badge
    mask[160:600, 500:1230] = False                            # logo et textes
    yy, xx = np.mgrid[0:H, 0:W]
    X, Y = xx / W, yy / H
    basis = lambda X, Y: np.stack([np.ones_like(X), X, Y, X * X, X * Y, Y * Y, X ** 3, X * X * Y, X * Y * Y, Y ** 3], -1)  # noqa: E731
    B = basis(X, Y)
    smooth = np.stack([B @ np.linalg.lstsq(B[mask], im[..., c][mask], rcond=None)[0] for c in range(3)], -1)
    res = im - smooth
    band = res[2:78, :, :]                                     # bande vide du haut : grain réel
    # on ne garde que le GRAIN (passe-haut) : sans ça, les écarts lents de la bande se voyaient en carreaux
    k = np.ones(13) / 13                                       # flou séparable (moyenne glissante 13 px)
    low = np.apply_along_axis(lambda v: np.convolve(np.pad(v, 6, mode="edge"), k, "valid"), 1, band)
    low = np.apply_along_axis(lambda v: np.convolve(np.pad(v, 6, mode="edge"), k, "valid"), 0, low)
    band = band - low
    rng = np.random.default_rng(7)
    fill = np.zeros_like(res)
    for y0 in range(0, H, 76):
        for x0 in range(0, W, 256):
            sx = int(rng.integers(0, W - 256))
            h, w = min(76, H - y0), min(256, W - x0)
            fill[y0:y0 + h, x0:x0 + w] = band[:h, sx:sx + w]
    out_img = smooth + fill                                    # tout le fond recalculé : aucune couture entre zones
    Image.fromarray(np.clip(out_img, 0, 255).astype("uint8")).save(out)
    return out


def partner_box(out: Path, fond: Path) -> Path:
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
background:url("{_uri(fond)}") 0 0/1184px 500px no-repeat}}
.in{{position:relative;padding-top:46px}}
.k{{font-weight:700;font-size:24px;letter-spacing:.2em;color:#FFFFFF;opacity:.85}}
h1{{font-weight:800;font-size:46px;line-height:1.25;color:#FFFFFF;margin:14px 0 30px}}
h1 span{{background:#F28A32;padding:0 12px}}
.badge{{height:200px;display:block;margin:0 auto}}
</style></head><body><div class='box'><div class='in'><div class='k'>NOUVEAU PARTENAIRE</div>
<h1>Select Services Partner<br>du <span>Claude Partner Network</span></h1>
<img class='badge' src='{_uri(IMG / "partenaire_anthropic.png")}'></div></div></body></html>"""
    _shot(page, 1184, 500, out)
    return out


def badge_cutout(out: Path) -> Path:
    """Badge vertical de l'en-tête fourni, découpé avec ses coins arrondis (fond transparent autour)."""
    from PIL import ImageDraw
    im = Image.open(HERE / "sources" / "entete_fourni.webp").convert("RGB").crop((140, 92, 438, 666))
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), 18, fill=255)
    im.putalpha(m)
    im.save(out)
    return out


def banner(out: Path, fond: Path) -> Path:
    """Bannière du haut, même mise en page que l'en-tête fourni (badge à gauche, logo, titre, filet orange, paragraphe), texte des
    retours du 16/11/2026 : « AI Partners rejoint le Claude Partner Network comme partenaire Select. », surlignage orange sur
    « Claude Partner Network »."""
    badge = badge_cutout(HERE / "_badge.png")
    css = "".join(f'@font-face{{font-family:M;src:url("{_uri(FONTS / f"Metropolis-{n}.ttf")}");font-weight:{w}}}'
                  for n, w in (("Regular", 400), ("Bold", 700), ("ExtraBold", 800)))
    logo = ROOT / "MARQUES" / "ai-corner" / "assets" / "logo_horizontal.svg"
    page = f"""<html><head><meta charset='utf-8'><style>{css}*{{margin:0;box-sizing:border-box}}
body{{width:1280px;height:720px;background:url("{_uri(fond)}") 0 0/1280px 720px no-repeat;font-family:M,Arial;color:#FFFFFF;
position:relative;overflow:hidden}}
.badge{{position:absolute;left:140px;top:92px;width:298px;height:574px}}
.col{{position:absolute;left:518px;top:0;width:700px;height:720px;display:flex;flex-direction:column;justify-content:center}}
.logo{{height:34px;width:auto;align-self:flex-start;filter:brightness(0) invert(1)}}
h1{{font-weight:800;font-size:44px;line-height:1.2;margin:34px 0 26px}}
h1 span{{background:#F28A32;padding:0 8px;box-decoration-break:clone;-webkit-box-decoration-break:clone}}
.rule{{width:60px;height:4px;background:#F28A32;margin:0 0 26px}}
p{{font-weight:400;font-size:24px;line-height:1.5}}
</style></head><body><img class='badge' src='{_uri(badge)}'><div class='col'><img class='logo' src='{_uri(logo)}'>
<h1>AI Partners rejoint le <span>Claude Partner Network</span> comme partenaire Select.</h1><div class='rule'></div>
<p>Le programme d'Anthropic réunit les sociétés qui déploient Claude chez leurs clients. Notre mission&nbsp;: faire passer vos
projets IA de l'expérimentation à la production.</p></div></body></html>"""
    _shot(page, 1280, 720, HERE / "_banniere.png")
    Image.open(HERE / "_banniere.png").convert("RGB").save(out, quality=90)
    (HERE / "_banniere.png").unlink()
    badge.unlink()
    return out


def images() -> None:
    for p in (REF / "images").iterdir():                      # images du mail de référence (icônes en verre, photo de Thomas)
        if p.suffix in (".png", ".jpg") and not p.name.startswith("_"):
            shutil.copy2(p, IMG / p.name)
    for n in ("client_loreal.png", "client_isagri.png", "client_trench.png", "partenaire_anthropic.png", "partenaire_openai.png",
              "partenaire_dust.png", "partenaire_google.png"):
        shutil.copy2(V1 / "images" / n, IMG / n)
    fond = header_background(HERE / "_fond_entete.png")    # fond de l'en-tête fourni, sans badge ni texte
    banner(IMG / "banniere_select.jpg", fond)
    partner_box(IMG / "encadre_nouveau_partenaire.png", fond)
    fond.unlink()
    (IMG / "entete_select.jpg").unlink(missing_ok=True)
    (IMG / "hero.png").unlink(missing_ok=True)


def build() -> str:
    hero = ('<tr><td style="padding:0"><img src="images/banniere_select.jpg" width="640" alt="AI Partners rejoint le Claude Partner '
            'Network comme partenaire Select" style="display:block;width:100%;max-width:640px;height:auto;border:0">'
            '</td></tr>')
    sig = (f'<tr><td style="padding:0 4px"><table role="presentation" cellpadding="0" cellspacing="0"><tr>'
           f'<td valign="middle" width="100" style="width:100px;padding:0 18px 0 0"><img src="images/thomas_portrait.jpg" width="84" '
           f'height="84" alt="Thomas Spitz" style="display:block;border:0;border-radius:42px;width:84px;height:84px"></td>'
           f'<td valign="middle" style="{F};font-size:17px;line-height:1.7;color:{TEXT}">{strong("Thomas Spitz")}<br>'
           f'<span style="color:#4A5683">Co-founder &amp; CEO, AI Partners</span></td></tr></table></td></tr>')
    rows = [
        para("Bonjour,", "34px 4px 14px 4px"),
        para("Je tenais à vous partager une étape importante pour AI Partners&nbsp;: nous avons obtenu le statut de "
             + strong("partenaire Select du Claude Partner Network") + ", le programme d'Anthropic dédié aux sociétés "
             "qui déploient Claude, powered by Anthropic, chez leurs clients.", "0 4px 14px 4px"),
        para("Cette reconnaissance vient consacrer deux années de travail aux côtés de nos clients, et une conviction "
             "qui ne m'a pas quitté depuis la création d'AI Partners&nbsp;: la valeur de l'IA se joue en production, au-delà des pilotes.",
             "0 4px 30px 4px"),
        h2("Une expertise reconnue, et déjà à l'œuvre chez nos clients", 0),
        stats(),
        h2("Des résultats mesurés", 0),
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
