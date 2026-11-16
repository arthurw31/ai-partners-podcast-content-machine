"""Mail d'annonce « AI Partners devient partenaire Select du Claude Partner Network » (texte de Thomas, V6, 16/11/2026).

Lancer depuis la racine du dépôt :  python PRESENTATIONS/2026-11_newsletter_anthropic_select/build.py
Sorties (dans ce dossier) :
  images/                    images du mail (à publier sur GitHub Pages : docs/newsletters/anthropic-select/)
  email.html                 mail complet, images locales (aperçu)
  email_hubspot_module.html  à coller dans un module « Modifier HTML » de HubSpot (liens d'images absolus)
  objet.txt, preheader.txt   à saisir dans les réglages du mail HubSpot
  apercu.png, apercu_hubspot_480px.png
"""
from __future__ import annotations

import html
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from clipper.newsletter import _shot, _uri  # noqa: E402

SRC, IMG = HERE / "sources", HERE / "images"
IMG.mkdir(exist_ok=True)
ASSETS = ROOT / "MARQUES" / "ai-corner" / "assets"
PUBLIC = "https://arthurw31.github.io/ai-partners-podcast-content-machine/newsletters/anthropic-select"

NAVY, NAVY_MID, BLUE, LIGHT, LINE = "#151D53", "#1D2C76", "#258AF3", "#F1F6FD", "#E3E8F2"
SKY, LINE_DARK, ON_NAVY = "#5CA8FF", "#B9C4E2", "#D6DEF5"
CLAUDE = "#D97757"     # orange Claude (l'astérisque du badge) : « Claude Partner Network » en orange (Arthur, 16/11/2026)     # plus de contraste en bleu nuit (Arthur, 16/11/2026)
FONT = "Helvetica, Arial, sans-serif"
FONTS_CSS = "".join(f'@font-face{{font-family:M;src:url("{_uri(ASSETS / "fonts" / f"Metropolis-{n}.ttf")}");font-weight:{w}}}'
                    for n, w in (("Regular", 400), ("Bold", 700), ("ExtraBold", 800)))

SUBJECT = "AI Partners devient partenaire Select du Claude Partner Network"
PREHEADER = "Une reconnaissance d'Anthropic, et ce qu'elle change pour vos projets IA."


def esc(t) -> str:
    return html.escape(str(t))


# ------------------------------------------------------------------------------------------------------------------
# 1. Images
# ------------------------------------------------------------------------------------------------------------------

def crop_badge(src: Path, box: tuple, out: Path, pad: int = 6, thr: int = 28) -> Path:
    """Badge officiel découpé dans la capture de la carte partenaire (zone sous le filet), à sa taille d'origine."""
    im = Image.open(src).convert("RGB").crop(box)
    px = im.load()
    xs, ys = [], []
    for y in range(im.height):
        for x in range(im.width):
            if max(abs(255 - v) for v in px[x, y]) > thr:
                xs.append(x)
                ys.append(y)
    b = (max(min(xs) - pad, 0), max(min(ys) - pad, 0), min(max(xs) + pad + 1, im.width), min(max(ys) + pad + 1, im.height))
    im.crop(b).save(out)
    return out


def svg_png(svg: Path, out: Path, h: int, color: str | None = None, bg: str = "#FFFFFF") -> Path:
    """Logo SVG rendu par Chrome à la hauteur voulue (2× la taille d'affichage), marges blanches rognées."""
    txt = svg.read_text(encoding="utf-8")
    if color:
        txt = txt.replace("currentColor", color)
    tmp = IMG / ("_" + svg.stem + ".svg")
    tmp.write_text(txt, encoding="utf-8")
    page = (f"<html><body style='margin:0;background:{bg}'><img src='{_uri(tmp)}' style='height:{h}px;display:block;margin:20px'>"
            f"</body></html>")
    _shot(page, 1400, h + 40, out)
    tmp.unlink()
    im = Image.open(out).convert("RGB")
    ref = im.getpixel((0, 0))
    px = im.load()
    xs = [x for x in range(im.width) for y in range(0, im.height, 2) if px[x, y] != ref]
    im.crop((max(min(xs) - 2, 0), 18, min(max(xs) + 3, im.width), h + 22)).save(out)
    return out


def hero(out: Path) -> Path:
    logo = (ASSETS / "logo_horizontal.svg")
    badge = SRC / "badge_claude_partner_network_select.png"
    page = f"""<html><head><meta charset='utf-8'><style>{FONTS_CSS}*{{margin:0}}
body{{width:1360px;height:820px;background:linear-gradient(155deg,{NAVY_MID} 0%,{NAVY} 55%,#0E1440 100%);font-family:M,Arial;
position:relative;overflow:hidden;color:#fff}}
.bg{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;mix-blend-mode:screen;opacity:.55}}
.logo{{position:absolute;left:96px;top:84px;height:52px;filter:brightness(0) invert(1)}}
.kick{{position:absolute;left:96px;top:236px;font-weight:700;font-size:26px;letter-spacing:.16em;color:#9DB8FF;text-transform:uppercase}}
h1{{position:absolute;left:96px;top:272px;width:1180px;font-weight:800;font-size:64px;line-height:1.12}}
h1 span{{color:{CLAUDE}}}
.badge{{position:absolute;left:96px;top:560px;height:180px}}   /* badge à plat : ni ombre ni arrondi (guidelines Anthropic) */
</style></head><body><img class='bg' src='{_uri(ASSETS / "outro_bg.png")}'><img class='logo' src='{_uri(logo)}'>
<div class='kick'>Annonce</div><h1>AI Partners devient<br>Select Services Partner<br>in the <span>Claude Partner Network</span></h1>
<img class='badge' src='{_uri(badge)}'></body></html>"""
    _shot(page, 1360, 820, out)
    Image.open(out).convert("RGB").save(out.with_suffix(".jpg"), quality=88)
    out.unlink()
    return out.with_suffix(".jpg")


def thomas(out: Path) -> Path:
    # photo de FACE, souriant (Arthur, 16/11/2026 : « met celle de face qui est mieux ») : photo 04 de la planche des photos de profil
    src = SRC / "thomas_face.jpg"
    Image.open(src).convert("RGB").save(out, quality=90)
    return out


def make_images() -> dict:
    i = {
        "hero": hero(IMG / "annonce_titre.png"),   # nouveau nom : pas d'ancienne version en cache
        "p_anthropic": IMG / "partenaire_anthropic.png",
        "p_openai": crop_badge(SRC / "capture_openai_google.png", (12, 78, 304, 188), IMG / "partenaire_openai.png"),
        "p_dust": crop_badge(SRC / "capture_dust.png", (12, 78, 306, 188), IMG / "partenaire_dust.png", pad=4, thr=8),
        "p_microsoft": svg_png(SRC / "microsoft.svg", IMG / "partenaire_microsoft.png", 84),
        "c_loreal": svg_png(SRC / "loreal.svg", IMG / "client_loreal.png", 56),
        "c_isagri": svg_png(SRC / "isagri.svg", IMG / "client_isagri.png", 64),
        "c_trench": IMG / "client_trench.png",
        "thomas": thomas(IMG / "thomas_face.jpg"),   # nouveau nom : pas de vieille photo en cache
    }
    Image.open(SRC / "badge_claude_partner_network_select.png").save(i["p_anthropic"])
    t = Image.open(SRC / "trench.png").convert("RGBA")
    flat = Image.new("RGB", t.size, "white")
    flat.paste(t, (0, 0), t)
    flat.save(i["c_trench"])
    for name in ("compass", "factory", "layers", "graduation-cap"):
        i["icon_" + name] = svg_png(ASSETS / "icons" / f"lucide_{name}.svg", IMG / f"icone_{name}.png", 56, SKY, NAVY)
    return i


# ------------------------------------------------------------------------------------------------------------------
# 2. Mail
# ------------------------------------------------------------------------------------------------------------------

def size(p: Path, w: int | None = None, h: int | None = None) -> tuple[int, int]:
    W, H = Image.open(p).size
    if w and h:                                                   # tient dans la boîte w × h
        k = min(w / W, h / H)
    else:
        k = (w / W) if w else (h / H)
    return round(W * k), round(H * k)


def body(i: dict, src) -> str:
    P = f'style="margin:0 0 16px 0;font-family:{FONT};font-size:17px;line-height:1.6;color:{NAVY_MID}"'

    def h2(t, top=34):
        return (f'<tr><td style="padding:{top}px 40px 14px 40px;font-family:{FONT};font-size:22px;line-height:1.3;font-weight:bold;'
                f'color:{NAVY}"><table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 10px 0"><tr>'
                f'<td width="40" height="4" bgcolor="{BLUE}" style="width:40px;height:4px;font-size:0;line-height:0;border-radius:2px">'
                f'&nbsp;</td></tr></table>{esc(t)}</td></tr>')

    def img(key, w, h, alt, extra=""):
        a, b = size(i[key], w, h)
        return (f'<img src="{src(i[key])}" width="{a}" height="{b}" alt="{esc(alt)}" '
                f'style="display:block;width:{a}px;height:{b}px;border:0;{extra}">')

    # chiffres
    stats = [("12", "experts certifiés par Anthropic"), ("5", "déploiements clients validés par Anthropic"),
             ("3", "références publiques")]
    stat_cells = '<td width="2%" style="font-size:0">&nbsp;</td>'.join(
        f'<td width="32%" valign="top" bgcolor="{NAVY}" style="width:32%;background-color:{NAVY};border-radius:14px;padding:20px 12px;'
        f'text-align:center;font-family:{FONT}"><div style="font-size:42px;line-height:1;font-weight:bold;color:#FFFFFF">{n}</div>'
        f'<div style="font-size:14px;line-height:1.35;color:#FFFFFF;padding-top:8px">{esc(t)}</div></td>' for n, t in stats)

    # cas clients
    clients = [("c_loreal", "L'Oréal", "150 experts tech et produit formés en trois jours de build."),
               ("c_isagri", "ISAGRI", "Une chaîne de développement en production sur Claude Code, désormais utilisée au quotidien par "
                                      "les équipes produit."),
               ("c_trench", "Trench Group", "12 applications construites en trois jours, dont 3 en production, qui économisent plus "
                                            "de 200 heures de travail par an.")]
    client_rows = "".join(
        f'<tr><td style="padding:0 0 10px 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="border:1px solid {LINE_DARK};border-left:4px solid {NAVY};border-radius:14px;border-collapse:separate"><tr>'
        f'<td width="140" valign="middle" align="center" style="width:140px;padding:16px 10px 16px 16px">{img(k, 120, 30, n)}</td>'
        f'<td valign="middle" style="padding:16px 18px 16px 8px;font-family:{FONT};font-size:15px;line-height:1.5;color:{NAVY_MID}">'
        f'<strong style="color:{NAVY}">{esc(n)}</strong><br>{esc(t)}</td></tr></table></td></tr>' for k, n, t in clients)

    # partenaires : cartes dans le style des cartes partenaires du site
    def partner(key, title, w, h):
        return (f'<td width="31%" valign="top" align="center" bgcolor="#FFFFFF" style="width:31%;border:1px solid {LINE_DARK};border-radius:14px;'
                f'padding:16px 6px 18px 6px;font-family:{FONT};text-align:center">'
                f'<div style="font-size:14px;line-height:1.3;font-weight:bold;color:{NAVY}">{esc(title)}</div>'
                f'<table role="presentation" align="center" cellpadding="0" cellspacing="0" style="margin:10px auto 12px auto"><tr>'
                f'<td width="50" height="2" bgcolor="{BLUE}" style="width:50px;height:2px;font-size:0;line-height:0">&nbsp;</td></tr></table>'
                f'<table role="presentation" align="center" cellpadding="0" cellspacing="0"><tr><td height="56" valign="middle" '
                f'align="center" style="height:56px">{img(key, w, h, title)}</td></tr></table></td>')
    gap = '<td width="2%" style="width:2%;font-size:0;line-height:0">&nbsp;</td>'
    space = '<tr><td colspan="3" height="12" style="height:12px;font-size:0;line-height:0">&nbsp;</td></tr>'
    # le NOUVEAU partenaire en grand, dans un encadré bleu nuit (Arthur, 16/11/2026), les trois autres dessous
    new = (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:separate"><tr>'
           f'<td bgcolor="{NAVY}" align="center" style="background-color:{NAVY};border:2px solid {BLUE};border-radius:16px;'
           f'padding:22px 20px 26px 20px;font-family:{FONT};text-align:center">'
           f'<div style="font-size:12px;line-height:1;font-weight:bold;letter-spacing:.16em;color:{SKY}">NOUVEAU PARTENAIRE</div>'
           f'<div style="font-size:20px;line-height:1.3;font-weight:bold;color:#FFFFFF;padding:8px 0 16px 0">Select Services Partner<br>in the <span style="color:{CLAUDE}">Claude Partner Network</span></div>'
           f'<table role="presentation" align="center" cellpadding="0" cellspacing="0"><tr><td align="center">'
           f'{img("p_anthropic", 330, 110, "Select Services Partner, Claude Partner Network", "")}</td></tr></table>'
           f'</td></tr></table>')
    gap = '<td width="10" style="width:10px;min-width:10px;font-size:0;line-height:0">&nbsp;</td>'
    partners = (new + '<div style="height:12px;font-size:0;line-height:0">&nbsp;</div>'
                f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:separate"><tr>'
                f'{partner("p_openai", "OpenAI Select Partner", 124, 54)}{gap}{partner("p_dust", "Dust Partner", 130, 46)}{gap}'
                f'{partner("p_microsoft", "Microsoft Partner", 120, 30)}</tr></table>')

    # offres
    offers = [("compass", "Stratégie et gouvernance", "Identifier les cas d'usage où l'IA crée réellement de la valeur, et poser le cadre "
                                                     "de sécurité et de gouvernance pour passer à l'échelle."),
              ("factory", "Build et production", "Concevoir, déployer et industrialiser des agents au cœur de vos processus métier."),
              ("layers", "Déploiement de Claude Enterprise et Claude Team", "Configurer les accès, les niveaux d'usage et "
                                                                           "l'administration, puis faire adopter l'outil par vos équipes."),
              ("graduation-cap", "Adoption et montée en compétences", "Des programmes de build où vos équipes construisent leurs propres "
                                                                       "usages, de Claude Cowork aux équipes de développement sur Claude Code.")]

    def offer(o):
        ic, t, x = o
        return (f'<td width="49%" valign="top" bgcolor="{NAVY}" style="width:49%;background-color:{NAVY};border-radius:14px;'
                f'padding:18px 16px 20px 16px;font-family:{FONT};font-size:15px;line-height:1.5;color:{ON_NAVY};text-align:left">'
                f'{img("icon_" + ic, 28, 28, "")}<div style="height:10px;font-size:0;line-height:0">&nbsp;</div>'
                f'<strong style="color:#FFFFFF;font-size:16px;line-height:1.3">{esc(t)}</strong><br>{esc(x)}</td>')
    offers_html = (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:separate">'
                   f'<tr>{offer(offers[0])}{gap}{offer(offers[1])}</tr>{space}<tr>{offer(offers[2])}{gap}{offer(offers[3])}</tr></table>')

    a, b = size(i["hero"], 680)
    return f"""<table role="presentation" width="680" cellpadding="0" cellspacing="0" bgcolor="#FFFFFF" style="width:100%;max-width:680px;background-color:#FFFFFF;border-radius:16px;overflow:hidden">
<tr><td><img src="{src(i["hero"])}" width="680" alt="AI Partners devient Select Services Partner in the Claude Partner Network" style="display:block;width:100%;max-width:680px;height:auto;border:0"></td></tr>
<tr><td style="padding:34px 40px 0 40px">
<p {P}>Bonjour,</p>
<p {P}>Je tenais à vous partager une étape importante pour AI Partners : nous avons obtenu le statut de <strong style="color:{NAVY}">partenaire Select du Claude Partner Network</strong> (Services Track), le programme d'Anthropic dédié aux sociétés qui déploient Claude, powered by Anthropic, chez leurs clients.</p>
<p {P}>Ce statut valide une pratique Claude éprouvée sur le terrain : des équipes certifiées, des clients en production et des cas publics. Cette reconnaissance vient consacrer deux années de travail aux côtés de nos clients, et une conviction qui ne m'a pas quitté depuis la création d'AI Partners : la valeur de l'IA se joue en production, au-delà des pilotes.</p>
</td></tr>
{h2("Une expertise reconnue, et déjà à l'œuvre chez nos clients", 18)}
<tr><td style="padding:0 40px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:separate"><tr>{stat_cells}</tr></table></td></tr>
<tr><td style="padding:22px 40px 0 40px">
<p {P}><strong style="color:{NAVY}">Des experts qui pratiquent.</strong> Nos consultants et ingénieurs utilisent Claude au quotidien, y compris Claude Code dans notre propre ingénierie.</p>
<p {P}><strong style="color:{NAVY}">Des projets en production.</strong> Nos 5 déploiements clients validés par Anthropic vont au-delà des POC et des expérimentations.</p>
<p {P}><strong style="color:{NAVY}">Des résultats mesurés</strong>, sur 3 références publiques :</p>
</td></tr>
<tr><td style="padding:0 40px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{client_rows}</table></td></tr>
{h2("Ce qui ne change pas : notre indépendance")}
<tr><td style="padding:0 40px">
<p {P}>Ce statut renforce notre expertise sur Claude, sans rien changer à notre position. AI Partners reste indépendant et agnostique. Nous sommes également partenaires d'OpenAI, de Dust et de Microsoft.</p>
</td></tr>
<tr><td style="padding:4px 40px 22px 40px">{partners}</td></tr>
<tr><td style="padding:0 40px">
<p {P}>Nous ne percevons aucune commission d'apport de la part des éditeurs. Notre seul critère reste votre besoin réel : nous vous recommandons la solution la plus adaptée, y compris quand ce n'est pas Claude. <strong style="color:{NAVY}">Je m'y engage personnellement.</strong></p>
</td></tr>
{h2("Ce que nous pouvons faire pour vous", 22)}
<tr><td style="padding:0 40px">{offers_html}</td></tr>
<tr><td style="padding:12px 40px 0 40px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td style="border:1px solid {BLUE};border-radius:14px;padding:16px 18px;font-family:{FONT};font-size:15px;line-height:1.55;color:{NAVY_MID}">
<strong style="color:{NAVY}">Bon à savoir.</strong> Sur certains déploiements Claude Enterprise, Anthropic peut cofinancer une partie de l'accompagnement à l'adoption, sous réserve d'éligibilité déterminée par Anthropic. Nous vous indiquons si votre projet peut en bénéficier.</td></tr></table></td></tr>
<tr><td style="padding:30px 40px 0 40px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td bgcolor="{NAVY}" align="center" style="background-color:{NAVY};border-radius:16px;padding:32px 28px 34px 28px;font-family:{FONT}">
<div style="font-size:22px;line-height:1.3;font-weight:bold;color:#FFFFFF">Parlons de vos projets</div>
<div style="font-size:16px;line-height:1.6;color:{ON_NAVY};padding-top:10px">Vous avez un pilote à faire passer en production, un déploiement Claude à réussir, ou un cas d'usage à cadrer ? Je vous propose un échange de 30 minutes avec l'un de nos experts.</div>
<div style="font-size:17px;line-height:1.4;font-weight:bold;color:{SKY};padding-top:16px">Répondez simplement à ce mail &rarr;</div>
</td></tr></table></td></tr>
<tr><td style="padding:30px 40px 38px 40px;font-family:{FONT}">
<p style="margin:0 0 20px 0;font-size:17px;line-height:1.6;color:{NAVY_MID}">Merci pour votre confiance. C'est avec vous que cette étape s'est construite.</p>
<table role="presentation" cellpadding="0" cellspacing="0"><tr>
<td valign="middle" width="64" style="width:64px;padding-right:14px">{img("thomas", 64, 64, "Thomas Spitz", "border-radius:32px")}</td>
<td valign="middle" style="font-family:{FONT};font-size:15px;line-height:1.45;color:{NAVY_MID}"><strong style="font-size:17px;color:{NAVY}">Thomas Spitz</strong><br>Co-founder &amp; CEO, AI Partners</td>
</tr></table></td></tr>
</table>"""


def full(inner: str) -> str:
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light"><title>{esc(SUBJECT)}</title></head>
<body style="margin:0;padding:0;background:#E9EEF9">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{esc(PREHEADER)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#E9EEF9"><tr><td align="center" style="padding:24px 12px">
{inner}
</td></tr></table></body></html>"""


def preview(page: str, width: int, out: Path) -> Path:
    tmp = HERE / "_apercu_tmp.png"
    _shot(page, width, 5200, tmp)
    im = Image.open(tmp).convert("RGB")
    px, bottom = im.load(), im.height - 1
    while bottom > 0 and px[im.width // 2, bottom] == px[im.width // 2, im.height - 1]:
        bottom -= 1
    im.crop((0, 0, im.width, min(im.height, bottom + 30))).save(out)
    tmp.unlink()
    return out


def main():
    i = make_images()
    local = body(i, lambda p: "images/" + p.name)
    (HERE / "email.html").write_text(full(local), encoding="utf-8")
    module = body(i, lambda p: f"{PUBLIC}/{p.name}")
    (HERE / "email_hubspot_module.html").write_text(module + "\n", encoding="utf-8")
    (HERE / "objet.txt").write_text(SUBJECT + "\n", encoding="utf-8")
    (HERE / "preheader.txt").write_text(PREHEADER + "\n", encoding="utf-8")
    page = full(body(i, lambda p: _uri(p)))
    preview(page, 760, HERE / "apercu.png")
    preview(page.replace('max-width:680px;background', 'max-width:480px;background'), 540, HERE / "apercu_hubspot_480px.png")
    if "—" in module or "–" in module:
        raise SystemExit("tiret cadratin dans le mail")
    print("ok :", ", ".join(sorted(p.name for p in IMG.iterdir())))


if __name__ == "__main__":
    main()
