"""Maquettes du mail podcast inspirées d'elevenlabs.io, aux couleurs d'AI Partners (Arthur, 19/10/2026 : « on aime bien le design
comme celui en bleu [dégradé granuleux + bulles de conversation], les deux de la 2e image [cartes à motif d'ondes] ou la 3e [affiches
en dégradé avec le titre au centre] ; propose plusieurs maquettes de podcast avec ce genre de choses, aux couleurs d'AI Partners »).

Trois pistes, rendues avec le vrai contenu de l'épisode :
  A « Grain »    : grande carte en dégradé granuleux bleu nuit avec la question en bulles de conversation, cartes grises sobres.
  B « Ondes »    : cartes « article de blog » : visuel en dégradé à motif d'ondes + pastille, légende blanche dessous.
  C « Affiches » : grandes affiches en dégradé avec le titre en blanc au centre, programme en 4 petites affiches.

Contraintes d'un e-mail : les dégradés, le grain et les ondes n'existent pas en HTML d'e-mail -> ce sont des IMAGES (rendues par Chrome,
2× la taille affichée pour rester nettes) ; tout le reste est du texte HTML (tableaux, styles en ligne, Helvetica/Arial).
Usage : python -m clipper.newsletter_maquettes  (épisode E22 par défaut) -> travail/newsletter/maquettes/
"""
from __future__ import annotations

import sys
from pathlib import Path

from .newsletter_templates import (BLUE, BLUE_SKY, FONT, LIGHT, NAVY, NAVY_MID, PILL_CLOSE, _intro_html, _platforms, button,
                                   closing_block, esc, para, pill_open)

GREY_BG = "#F3F5F9"      # fond des cartes (le gris très clair d'ElevenLabs, teinté bleu)
GREY_LINE = "#E3E7F0"
GREY_TXT = "#6B7394"

# Palettes de dégradés, toutes dans la charte : bleu nuit, bleu AI Partners, bleu ciel, bleu foncé
PALETTES = {
    "nuit":    {"base": "#151D53", "blobs": [("#258AF3", "28% 62%", "62%"), ("#5CA8FF", "82% 18%", "48%"), ("#0E1440", "85% 95%", "60%"),
                                             ("#7C93F5", "12% 12%", "40%")]},
    "ciel":    {"base": "#0A47B6", "blobs": [("#5CA8FF", "20% 30%", "55%"), ("#B9D8FF", "78% 28%", "42%"), ("#151D53", "70% 100%", "62%")]},
    "aube":    {"base": "#1D2C76", "blobs": [("#258AF3", "50% 35%", "55%"), ("#CFE4FF", "50% 12%", "35%"), ("#0E1440", "50% 105%", "55%")]},
    "profond": {"base": "#0E1440", "blobs": [("#2B3A8C", "30% 20%", "55%"), ("#258AF3", "60% 95%", "50%"), ("#5CA8FF", "95% 60%", "30%")]},
    "glacier": {"base": "#258AF3", "blobs": [("#E3F0FF", "25% 20%", "45%"), ("#5CA8FF", "80% 40%", "50%"), ("#1D2C76", "40% 105%", "60%")]},
}

NOISE = ("<svg class='n' xmlns='http://www.w3.org/2000/svg'><filter id='g'><feTurbulence type='fractalNoise' baseFrequency='{f}' "
         "numOctaves='3' stitchTiles='stitch'/><feColorMatrix type='saturate' values='0'/></filter>"
         "<rect width='100%' height='100%' filter='url(#g)'/></svg>")

WAVES = ("<svg class='w' xmlns='http://www.w3.org/2000/svg'><defs><pattern id='p' width='{s}' height='{s}' patternUnits='userSpaceOnUse'>"
         "<path d='M0 {q} C{q} {q} {q} {t} {h} {t} S{t} {q} {s} {q}' fill='none' stroke='white' stroke-width='{lw}' stroke-opacity='{o}'/>"
         "<path d='M0 {t2} C{q} {t2} {q} {s2} {h} {s2} S{t} {t2} {s} {t2}' fill='none' stroke='white' stroke-width='{lw}' stroke-opacity='{o}'/>"
         "</pattern></defs><rect width='100%' height='100%' fill='url(#p)'/></svg>")


def _waves(size: int = 220, lw: float = 3, opacity: float = .32) -> str:
    s, h, q = size, size / 2, size / 4
    return WAVES.format(s=s, h=h, q=q, t=3 * q, t2=h + q * .25, s2=s - q * .25 + 0.01, lw=lw, o=opacity)


def art(brand, out: Path, w: int, h: int, palette: str, inner: str = "", waves: bool = False, grain: float = .28,
        radius: int = 48, outside: str = "#FFFFFF", extra_css: str = "") -> Path:
    """Image en dégradé (grain et/ou ondes) aux coins arrondis, posée sur la couleur de fond du mail (`outside`)."""
    from .newsletter import _fonts_css, _shot
    p = PALETTES[palette]
    grads = ",".join(f"radial-gradient(ellipse {size} {size} at {pos},{col} 0%,rgba(0,0,0,0) 100%)" for col, pos, size in p["blobs"])
    page = (f"<html><head><meta charset='utf-8'><style>{_fonts_css(brand)}*{{margin:0;padding:0;box-sizing:border-box}}"
            f"body{{width:{w}px;height:{h}px;background:{outside};overflow:hidden}}"
            f".a{{position:relative;width:{w}px;height:{h}px;border-radius:{radius}px;overflow:hidden;background:{grads},{p['base']};"
            f"font-family:M,Arial;color:#fff}}"
            f".n{{position:absolute;inset:0;width:100%;height:100%;opacity:{grain};mix-blend-mode:overlay}}"
            f".w{{position:absolute;inset:0;width:100%;height:100%}}{extra_css}</style></head><body><div class='a'>"
            + (_waves() if waves else "") + (NOISE.format(f=.85) if grain else "") + inner + "</div></body></html>")
    return _shot(page, w, h, out)


# ---------------------------------------------------------------------------------------------------------------
# Éléments communs
# ---------------------------------------------------------------------------------------------------------------

def _topbar(c: dict) -> str:
    """En-tête sobre en texte (comme le haut du site ElevenLabs) : nom de l'émission à gauche, numéro à droite."""
    return (f'<tr><td style="padding:26px 34px 18px 34px;font-family:{FONT}"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
            f'<td style="font-size:22px;font-weight:bold;color:{NAVY};letter-spacing:-.01em">AI <span style="color:{BLUE}">Corner</span>'
            f'<span style="font-size:13px;font-weight:normal;color:{GREY_TXT};letter-spacing:0">&nbsp;&nbsp;par AI Partners</span></td>'
            f'<td align="right"><span style="display:inline-block;border:1px solid {GREY_LINE};border-radius:999px;padding:7px 16px;'
            f'font-size:13px;font-weight:bold;color:{NAVY}">Nouvel épisode · {esc(c["episode"])}</span></td></tr></table></td></tr>')


def _img(c: dict, key: str, w: int, alt: str, link: bool = True, radius: int = 0) -> str:
    img = (f'<img src="{c["rel"](key)}" width="{w}" alt="{esc(alt)}" style="display:block;width:100%;max-width:{w}px;border:0;'
           f'border-radius:{radius}px">')
    return f'<a href="{esc(c["url"])}" style="text-decoration:none">{img}</a>' if link else img


def _body_text(c: dict, with_question: bool) -> str:
    q = (f'<p style="margin:0 0 16px 0;font-size:21px;line-height:1.35;font-weight:bold;color:{NAVY}">{para(c["hook"])}</p>'
         if with_question else _hook_rest(c))
    return (f'<tr><td class="pad" style="padding:26px 40px 0 40px;font-family:{FONT};font-size:17px;line-height:1.6;color:{NAVY_MID}">'
            f'<!--HELLO-->{q}{_intro_html(c)}</td></tr>')


def _split_hook(c: dict) -> tuple[str, str]:
    import re
    text = str(c.get("hook") or "").strip()
    sents = [x for x in re.split(r"(?<=[?!.])\s+", text) if x]
    k = max((i for i, x in enumerate(sents) if x.endswith("?")), default=-1)
    return " ".join(sents[:k + 1]) or text, " ".join(sents[k + 1:])


def _hook_rest(c: dict) -> str:
    rest = _split_hook(c)[1]
    return f'<p style="margin:0 0 16px 0">{para(rest)}</p>' if rest else ""


def _heading(text: str) -> str:
    return (f'<tr><td class="pad" style="padding:8px 34px 14px 34px;font-family:{FONT};font-size:22px;font-weight:bold;color:{NAVY};'
            f'letter-spacing:-.01em">{esc(text)}</td></tr>')


def _booking_grey(c: dict) -> str:
    b = c.get("booking") or {}
    if not b.get("url"):
        return ""
    return (f'<tr><td style="padding:10px 24px 0 24px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
            f'<td bgcolor="{GREY_BG}" align="center" style="border-radius:24px;padding:34px 30px 36px 30px;font-family:{FONT}">'
            f'<div style="font-size:22px;font-weight:bold;color:{NAVY};line-height:1.3">{esc(b.get("title") or "")}</div>'
            f'<div style="font-size:16px;line-height:1.55;color:{NAVY_MID};padding-top:8px">{esc(b.get("text") or "")}</div>'
            + pill_open(NAVY, "22px auto 0 auto") +
            f'<a href="{esc(b["url"])}" style="display:inline-block;padding:16px 34px;font-family:{FONT};font-size:16px;font-weight:bold;'
            f'color:#FFFFFF;text-decoration:none;letter-spacing:.02em">{esc(b.get("button") or "Réserver un échange")}</a>' + PILL_CLOSE +
            '</td></tr></table></td></tr>')


def _shell(c: dict, body: str) -> str:
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light"><meta name="supported-color-schemes" content="light">
<title>{esc(c["subject"])}</title>
<style>@media (max-width:600px){{.col{{display:block!important;width:100%!important;box-sizing:border-box!important}}.pad{{padding-left:22px!important;padding-right:22px!important}}}}</style></head>
<body style="margin:0;padding:0;background:{GREY_BG}">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{esc(c["preheader"])}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="{GREY_BG}"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="680" cellpadding="0" cellspacing="0" bgcolor="#FFFFFF" style="width:100%;max-width:680px;border-radius:24px;overflow:hidden">
{body}
<tr><td bgcolor="{NAVY}" class="pad" style="padding:22px 40px;font-family:{FONT};font-size:12px;line-height:1.6;color:#9DB8FF">AI Corner, le podcast d'AI Partners.<!--FOOT--></td></tr>
</table></td></tr></table></body></html>"""


def _two_by_two(cells: list[str]) -> str:
    gap = '<td width="4%" style="width:4%;font-size:0;line-height:0">&nbsp;</td>'
    space = '<tr><td colspan="3" height="16" style="font-size:0;line-height:0;height:16px">&nbsp;</td></tr>'
    return (f'<tr><td class="pad" style="padding:0 24px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
            f"<tr>{cells[0]}{gap}{cells[1]}</tr>{space}<tr>{cells[2]}{gap}{cells[3]}</tr></table></td></tr>")


def _tail(c: dict) -> str:
    return (f'<tr><td align="center" style="padding:30px 24px 0 24px">{_img(c, "youtube", 632, c["title"], radius=20)}</td></tr>'
            + closing_block(c, NAVY_MID, "#FFFFFF", NAVY) + _booking_grey(c)
            + '<tr><td height="34" style="font-size:0;line-height:0">&nbsp;</td></tr>' + _platforms(c))


# ---------------------------------------------------------------------------------------------------------------
# A · Grain : la question en bulles de conversation sur un dégradé granuleux (1re image)
# ---------------------------------------------------------------------------------------------------------------

def images_a(brand, d: Path, c: dict) -> dict:
    question = _split_hook(c)[0]
    bubbles = (
        "<div style='position:absolute;right:120px;top:150px;max-width:760px;padding:30px 40px;border-radius:44px;"
        "background:rgba(255,255,255,.12);border:2px solid rgba(255,255,255,.45);font-weight:700;font-size:38px;line-height:1.3'>"
        f"{esc(question)}</div>"
        "<div style='position:absolute;left:150px;top:400px;max-width:720px;padding:28px 40px 32px 40px;border-radius:44px;"
        f"background:#fff;color:{NAVY};font-size:34px;line-height:1.35'>"
        f"<div style='font-size:24px;color:{GREY_TXT};padding-bottom:10px;letter-spacing:.02em'>"
        f"<span style='letter-spacing:3px;color:{BLUE}'>❙❙❙❙</span>&nbsp; AI Corner · {esc(c['episode'])}</div>"
        f"{esc(c['guest'])} répond à {esc(c['host_name'])} dans le nouvel épisode.</div>"
        "<div style='position:absolute;left:72px;right:72px;bottom:64px'>"
        "<div style='font-size:30px;color:rgba(255,255,255,.75);padding-bottom:14px'>Nouvel épisode</div>"
        f"<div style='font-size:46px;font-weight:700;line-height:1.2'>{esc(c['theme'])}</div>"
        f"<div style='font-size:28px;color:rgba(255,255,255,.8);padding-top:14px'>{esc(c['guest'])} · {esc(c['role'])}</div></div>")
    return {"maq_a_hero": art(brand, d / "maq_a_hero.png", 1264, 1100, "nuit", bubbles, grain=.32, radius=48)}


def maquette_a(c: dict) -> str:
    def card(p):
        icon = (f'<table role="presentation" cellpadding="0" cellspacing="0"><tr><td bgcolor="#FFFFFF" style="border:1px solid {GREY_LINE};'
                f'border-radius:12px;padding:9px"><img src="images/icone_{p.get("icon")}.png" width="26" height="26" alt="" '
                f'style="display:block;width:26px;height:26px;border:0"></td></tr></table>') if p.get("icon") else ""
        return (f'<td width="48%" valign="top" bgcolor="{GREY_BG}" style="width:48%;border-radius:22px;padding:22px 22px 26px 22px;'
                f'font-family:{FONT};text-align:left">{icon}'
                f'<div style="font-size:15px;color:{GREY_TXT};padding-top:34px">{esc(p.get("title"))}</div>'
                f'<div style="font-size:15px;line-height:1.5;color:{NAVY};padding-top:8px">{esc(p.get("text"))}</div></td>')
    cells = [card(p) for p in c["program"][:4]]
    body = (_topbar(c)
            + f'<tr><td style="padding:0 24px">{_img(c, "maq_a_hero", 632, c["theme"])}</td></tr>'
            + _body_text(c, with_question=False)
            + f'<tr><td align="center">{button(c, bg=NAVY)}</td></tr>'
            + _heading("Au programme de cet épisode") + _two_by_two(cells) + _tail(c))
    return _shell(c, body)


# ---------------------------------------------------------------------------------------------------------------
# B · Ondes : cartes « article » avec un visuel à motif d'ondes et une pastille (2e image)
# ---------------------------------------------------------------------------------------------------------------

def _pill_html(text: str, size: int = 26) -> str:
    return (f"<div style='position:absolute;left:32px;top:32px;background:#fff;color:{NAVY};font-weight:700;font-size:{size}px;"
            f"padding:10px 22px;border-radius:999px'>{esc(text)}</div>")


def images_b(brand, d: Path, c: dict) -> dict:
    out = {"maq_b_hero": art(brand, d / "maq_b_hero.png", 1264, 640, "nuit", _pill_html(f"AI Corner · {c['episode']}", 30),
                             waves=True, grain=.18, radius=0)}
    for k, (p, pal) in enumerate(zip(c["program"][:4], ["ciel", "profond", "glacier", "aube"]), 1):
        out[f"maq_b_{k}"] = art(brand, d / f"maq_b_{k}.png", 600, 330, pal, _pill_html(f"{k:02d}", 26), waves=True, grain=.18,
                                radius=0)
    return out


def maquette_b(c: dict) -> str:
    def article(img_key: str, title: str, text: str, title_size: int = 16, text_size: int = 14, pad: str = "16px 18px 20px 18px"):
        return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid {GREY_LINE};'
                f'border-radius:22px;overflow:hidden;border-collapse:separate"><tr><td style="line-height:0;font-size:0">'
                f'<img src="images/{img_key}.png" width="100%" alt="" style="display:block;width:100%;border:0;border-radius:21px 21px 0 0"></td></tr>'
                f'<tr><td style="padding:{pad};font-family:{FONT};text-align:left">'
                f'<div style="font-size:{title_size}px;font-weight:bold;color:{NAVY};line-height:1.3">{esc(title)}</div>'
                + (f'<div style="font-size:{text_size}px;line-height:1.5;color:{NAVY_MID};padding-top:8px">{text}</div>' if text else "")
                + '</td></tr></table>')
    hero = article("maq_b_hero", c["theme"], f'<strong style="color:{NAVY}">{esc(c["host_name"])}</strong> reçoit '
                   f'<strong style="color:{NAVY}">{esc(c["guest"])}</strong>, {esc(c["role"][:1].lower() + c["role"][1:])}',
                   title_size=26, text_size=16, pad="22px 26px 26px 26px")
    cells = [f'<td width="48%" valign="top" style="width:48%">{article(f"maq_b_{k}", p.get("title"), esc(p.get("text")))}</td>'
             for k, p in enumerate(c["program"][:4], 1)]
    body = (_topbar(c) + f'<tr><td style="padding:0 24px">{hero}</td></tr>'
            + _body_text(c, with_question=True)
            + f'<tr><td align="center">{button(c, bg=NAVY)}</td></tr>'
            + _heading("Au programme de cet épisode") + _two_by_two(cells) + _tail(c))
    return _shell(c, body)


# ---------------------------------------------------------------------------------------------------------------
# C · Affiches : dégradés avec le titre en blanc au centre (3e image)
# ---------------------------------------------------------------------------------------------------------------

def _poster_text(text: str, size: int) -> str:
    return (f"<div style='position:absolute;inset:0;display:flex;align-items:center;justify-content:center;text-align:center;"
            f"padding:0 9%;font-size:{size}px;line-height:1.18;font-weight:400;letter-spacing:-.005em'>{esc(text)}</div>")


def images_c(brand, d: Path, c: dict) -> dict:
    lines = ("<svg class='w' xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100' preserveAspectRatio='none'>"
             + "".join(f"<path d='M{x} 0 C{x - 6} 30 {x + 6} 70 {x} 100' fill='none' stroke='white' stroke-opacity='.10' stroke-width='.18'/>"
                       for x in range(-10, 112, 4)) + "</svg>")
    out = {"maq_c_hero": art(brand, d / "maq_c_hero.png", 1264, 1000, "aube", lines + _poster_text(c["theme"], 76), grain=.30,
                             radius=48)}
    for k, (p, pal) in enumerate(zip(c["program"][:4], ["nuit", "glacier", "profond", "ciel"]), 1):
        out[f"maq_c_{k}"] = art(brand, d / f"maq_c_{k}.png", 600, 600, pal, _poster_text(p.get("title"), 50), grain=.30, radius=36)
    return out


def maquette_c(c: dict) -> str:
    def poster(k, p):
        return (f'<td width="48%" valign="top" style="width:48%;font-family:{FONT};text-align:left">'
                f'<img src="images/maq_c_{k}.png" width="100%" alt="{esc(p.get("title"))}" style="display:block;width:100%;border:0">'
                f'<div style="font-size:13px;font-weight:bold;color:{BLUE};padding:12px 4px 0 4px;letter-spacing:.06em">{k:02d}</div>'
                f'<div style="font-size:14px;line-height:1.5;color:{NAVY_MID};padding:4px 4px 0 4px">{esc(p.get("text"))}</div></td>')
    cells = [poster(k, p) for k, p in enumerate(c["program"][:4], 1)]
    caption = (f'<tr><td class="pad" style="padding:16px 34px 0 34px;font-family:{FONT}">'
               f'<div style="font-size:22px;color:{NAVY};line-height:1.3">AI Corner {esc(c["episode"])} : {esc(c["host_name"])} reçoit '
               f'{esc(c["guest"])}</div><div style="font-size:15px;color:{GREY_TXT};padding-top:6px"><strong style="color:{NAVY}">Podcast</strong>'
               f'&nbsp;&nbsp;{esc(c["role"])}</div></td></tr>')
    body = (_topbar(c) + f'<tr><td style="padding:0 24px">{_img(c, "maq_c_hero", 632, c["theme"])}</td></tr>' + caption
            + _body_text(c, with_question=True)
            + f'<tr><td align="center">{button(c, bg=NAVY)}</td></tr>'
            + _heading("Au programme de cet épisode") + _two_by_two(cells) + _tail(c))
    return _shell(c, body)


MAQUETTES = {"A": ("A · Grain", images_a, maquette_a), "B": ("B · Ondes", images_b, maquette_b),
             "C": ("C · Affiches", images_c, maquette_c)}


def build(brand, ep: Path) -> list[Path]:
    import json
    from PIL import Image, ImageDraw
    from .canva_template import font
    from .newsletter import _cfg, _preview, episode_title
    from .newsletter_templates import context
    nd = ep / "newsletter"
    imgdir = nd / "images"
    mail = json.loads((nd / "contenu.json").read_text(encoding="utf-8"))
    names = {"header": "entete.png", "thumb_plain": "miniature_sans_play.jpg", "youtube": "episode_youtube.jpg",
             "btn_play": "bouton_play.png", "plat_title": "plateformes_titre.png", "host_round": "thomas_rond.jpg"}
    imgs = {k: imgdir / v for k, v in names.items() if (imgdir / v).exists()}
    for f in imgdir.glob("plateforme_*.png"):
        imgs["plat_" + f.stem.split("_", 1)[1]] = f
    title, _ = episode_title(ep)
    out_dir = nd / "maquettes"
    out_dir.mkdir(exist_ok=True)
    previews = []
    for key, (label, make, page_of) in MAQUETTES.items():
        c = context(_cfg(brand), mail, dict(imgs), title)
        c["img"].update(make(brand, imgdir, c))
        page = page_of(c)
        (out_dir / f"maquette_{key}.html").write_text(page, encoding="utf-8")
        previews.append(_preview(nd, page, out_dir / f"apercu_{key}.png"))
    # planche côte à côte
    w, pad, head = 460, 30, 70
    ims = [Image.open(p).convert("RGB") for p in previews]
    ims = [i.resize((w, int(i.height * w / i.width)), Image.Resampling.LANCZOS) for i in ims]
    sheet = Image.new("RGB", (pad + len(ims) * (w + pad), head + max(i.height for i in ims) + pad), (244, 246, 251))
    dr = ImageDraw.Draw(sheet)
    f = font(brand.assets_dir, "Montserrat", "Bold", 22)
    for k, (key, im) in enumerate(zip(MAQUETTES, ims)):
        x = pad + k * (w + pad)
        dr.text((x, 24), MAQUETTES[key][0], font=f, fill=(21, 29, 83))
        sheet.paste(im, (x, head))
    sheet.save(out_dir / "planche_maquettes.png")
    return previews + [out_dir / "planche_maquettes.png"]


if __name__ == "__main__":
    from .config import Brand, EPISODES_DIR
    brand = Brand("ai-corner")
    pattern = sys.argv[1] if len(sys.argv) > 1 else "E22_*"
    ep = next((EPISODES_DIR / "ai-corner").glob(pattern)) / "travail"
    for p in build(brand, ep):
        print(p)
