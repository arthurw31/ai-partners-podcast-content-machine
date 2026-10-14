"""Gabarits du mail de Thomas (Arthur, 14/10/2026 : « améliorer le template des mails, que ça colle plus à la charte graphique
et que ça fasse mieux, plus de bleu foncé, propose-moi plusieurs templates pour que je voie mieux ce qu'on peut faire »).

Un gabarit = une fonction (c: dict de contenu) -> HTML d'e-mail. Contraintes d'un e-mail (Gmail, Outlook, Apple Mail) :
tableaux, styles EN LIGNE, `bgcolor` en plus des fonds CSS, 600 px, Helvetica/Arial (une police web comme Metropolis n'est pas
chargée par la plupart des boîtes : le texte du mail reste en Helvetica ; Metropolis n'existe que DANS les images : bandeau,
héros), images avec texte alternatif, pas d'italique, et une version qui reste lisible images bloquées.

Deux marqueurs sont remplacés à l'envoi par `newsletter.send_ready` quelle que soit la mise en page :
`<!--HELLO-->` (devient « Bonjour {{prenom}}, ») et `<!--FOOT-->` (devient la mention « Se désinscrire »).
"""
from __future__ import annotations

import html
import subprocess
from pathlib import Path

NAVY, NAVY_DEEP, NAVY_MID = "#151D53", "#0E1440", "#1D2C76"
BLUE, BLUE_DARK, BLUE_SKY, LIGHT = "#258AF3", "#0A47B6", "#5CA8FF", "#F1F6FD"
FONT = "Helvetica, Arial, sans-serif"

TEMPLATES = {
    "classique": "Classique : bandeau bleu nuit, fond clair (l'actuel)",
    "nuit": "A · Nuit : tout le mail en bleu nuit, cartes plus claires, texte blanc",
    "heros": "B · Héros : grande image bleue avec la photo de l'invité, puis corps clair",
    "editorial": "C · Éditorial : titre XL, bande bleu foncé du bouton, programme numéroté",
    "vedette": "D · Vedette : la miniature YouTube en tête, programme en 4 cartes",
    "duo": "D1 · Duo : Thomas et l'invité face à face en haut, corps clair",
    "ronds": "D2 · Ronds : deux photos rondes (Thomas, l'invité) puis la miniature",
    "lettre": "D3 · Lettre : le mail s'ouvre sur Thomas et son mot, puis la miniature",
    "duo_nuit": "D4 · Duo nuit : comme Duo, tout le corps en bleu nuit",
}


def esc(t) -> str:
    return html.escape(str(t or ""))


def para(t) -> str:
    return esc(t).replace("\n", "<br>")


def hl_words(text: str, n: int = 2) -> str:
    """Les n derniers mots mis en valeur (bandeau bleu nuit, comme la couverture des carrousels)."""
    words = str(text or "").split()
    if len(words) <= n:
        return f'<span class="hl">{esc(text)}</span>'
    return esc(" ".join(words[:-n])) + ' <span class="hl">' + esc(" ".join(words[-n:])) + "</span>"


# ---------------------------------------------------------------------------------------------------------------
# Image « héros » (gabarit B) : rendue par Chrome comme le bandeau
# ---------------------------------------------------------------------------------------------------------------

def make_hero(brand, d: Path, mail: dict, guest_png: Path | None, shot, fonts_css: str, uri) -> Path | None:
    if not guest_png:
        return None
    theme = str(mail.get("theme") or mail.get("guest") or "")
    words = theme.split()
    inner = (esc(" ".join(words[:-2])) + ' <span class="hl">' + esc(" ".join(words[-2:])) + "</span>") if len(words) > 2 \
        else f'<span class="hl">{esc(theme)}</span>'
    page = (f"<html><head><meta charset='utf-8'><style>{fonts_css}*{{margin:0}}"
            f"body{{width:1200px;height:760px;background:linear-gradient(160deg,{BLUE} 0%,{BLUE_DARK} 62%,{NAVY} 100%);"
            f"font-family:M,Arial;position:relative;overflow:hidden}}"
            f".person{{position:absolute;right:-50px;bottom:0;height:700px;filter:drop-shadow(0 30px 60px rgba(5,15,60,.45))}}"
            f".pill{{position:absolute;left:72px;top:64px;background:rgba(255,255,255,.18);color:#fff;font-weight:700;"
            f"font-size:26px;letter-spacing:.14em;padding:14px 26px;border-radius:999px;text-transform:uppercase;z-index:3}}"
            f"h1{{position:absolute;left:72px;top:170px;width:590px;color:#fff;font-weight:800;font-size:86px;line-height:1.1;"
            f"z-index:3;text-shadow:0 4px 30px rgba(5,15,60,.35)}}"
            f".hl{{background:{NAVY};padding:0 14px;box-decoration-break:clone;-webkit-box-decoration-break:clone}}"
            f"</style></head><body><img class='person' src='{uri(guest_png)}'><div class='pill'>AI Corner · {esc(mail['episode'])}</div>"
            f"<h1>{inner}</h1><script>document.fonts.ready.then(()=>{{const h=document.querySelector('h1');let s=86;"
            f"while((h.scrollWidth>h.clientWidth+1||h.offsetHeight>470)&&s>40){{s-=2;h.style.fontSize=s+'px'}}}});</script>"
            f"</body></html>")
    return shot(page, 1200, 760, d / "heros.png")


# ---------------------------------------------------------------------------------------------------------------
# Morceaux communs
# ---------------------------------------------------------------------------------------------------------------

def button(c: dict, bg: str = BLUE, fg: str = "#FFFFFF", margin: str = "28px auto") -> str:
    return (f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin:{margin}"><tr><td bgcolor="{bg}" '
            f'style="border-radius:999px"><a href="{esc(c["url"])}" style="display:inline-block;padding:16px 36px;font-family:{FONT};'
            f'font-size:16px;font-weight:bold;color:{fg};text-decoration:none;letter-spacing:.04em">{esc(c["button"])} ▶</a></td></tr></table>')


def youtube(c: dict, radius: int = 14, max_w: int = 552) -> str:
    if not c["img"].get("youtube"):
        return ""
    return (f'<a href="{esc(c["url"])}"><img src="{c["rel"]("youtube")}" width="{max_w}" alt="{esc(c["title"])}" '
            f'style="display:block;width:100%;max-width:{max_w}px;border-radius:{radius}px"></a>')


def shell(c: dict, outer_bg: str, body: str, footer_bg: str, footer_fg: str, card_bg: str = "#FFFFFF") -> str:
    """Document complet : texte d'aperçu caché, carte centrale de 600 px, pied de page avec le marqueur d'envoi."""
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light"><meta name="supported-color-schemes" content="light">
<title>{esc(c["subject"])}</title>
<style>@media (max-width:480px){{.col{{display:block!important;width:100%!important}}.pad{{padding-left:22px!important;padding-right:22px!important}}}}</style></head>
<body style="margin:0;padding:0;background:{outer_bg}">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{esc(c["preheader"])}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="{outer_bg}"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" bgcolor="{card_bg}" style="width:100%;max-width:600px;border-radius:16px;overflow:hidden">
{body}
<tr><td bgcolor="{footer_bg}" class="pad" style="padding:22px 40px;font-family:{FONT};font-size:12px;line-height:1.6;color:{footer_fg}">AI Corner, le podcast d'AI Partners.<!--FOOT--></td></tr>
</table></td></tr></table></body></html>"""


def closing_block(c: dict, fg: str, bg: str = "#FFFFFF", sig_fg: str | None = None) -> str:
    return (f'<tr><td bgcolor="{bg}" class="pad" style="padding:30px 40px 36px 40px;font-family:{FONT};font-size:17px;line-height:1.6;color:{fg}">'
            f'<p style="margin:0 0 18px 0">{para(c["closing"])}</p>'
            f'<p style="margin:0;font-weight:bold;color:{sig_fg or fg}">{c["sig"]}</p></td></tr>')


# ---------------------------------------------------------------------------------------------------------------
# A · Nuit
# ---------------------------------------------------------------------------------------------------------------

def nuit(c: dict) -> str:
    guest = (f'<img src="{c["rel"]("guest")}" width="150" height="150" alt="{esc(c["guest"])}" '
             f'style="display:block;border-radius:24px;width:150px;height:150px">' if c["img"].get("guest") else "")
    rows = "".join(
        f'<tr><td bgcolor="{NAVY_MID}" style="border-radius:14px;padding:16px 20px;font-family:{FONT};font-size:15px;line-height:1.55;color:#C9D3F5">'
        f'<span style="color:{BLUE_SKY};font-weight:bold;font-size:18px">{k:02d}</span>&nbsp; '
        f'<strong style="color:#FFFFFF;font-size:16px">{esc(p.get("title"))}</strong><br>{esc(p.get("text"))}</td></tr>'
        f'<tr><td height="10" style="font-size:0;line-height:0">&nbsp;</td></tr>' for k, p in enumerate(c["program"], 1))
    body = f"""<tr><td><img src="{c["rel"]("banner")}" width="600" alt="AI Corner, le podcast d'AI Partners" style="display:block;width:100%;max-width:600px"></td></tr>
<tr><td bgcolor="{NAVY}" class="pad" style="padding:36px 40px 8px 40px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
 <td class="col" width="150" valign="top">{guest}</td>
 <td class="col" valign="middle" style="padding-left:24px;font-family:{FONT}">
  <div style="font-size:21px;font-weight:bold;color:#FFFFFF">{esc(c["guest"])}</div>
  <div style="font-size:14px;color:#9DB8FF;padding-top:4px">{esc(c["role"])}</div>
  <div style="font-size:22px;font-weight:bold;color:{BLUE_SKY};line-height:1.25;padding-top:14px">{esc(c["theme"])}</div></td></tr></table></td></tr>
<tr><td bgcolor="{NAVY}" class="pad" style="padding:24px 40px 0 40px;font-family:{FONT};font-size:17px;line-height:1.6;color:#DCE3F7">
 <!--HELLO--><p style="margin:0 0 18px 0;font-weight:bold;color:#FFFFFF;font-size:19px">{para(c["hook"])}</p><p style="margin:0">{para(c["intro"])}</p></td></tr>
<tr><td bgcolor="{NAVY}" align="center">{button(c)}</td></tr>
<tr><td bgcolor="{NAVY}" class="pad" style="padding:10px 40px 14px 40px;font-family:{FONT}">
 <div style="font-size:20px;font-weight:bold;color:#FFFFFF;padding:22px 0 18px 0;border-top:1px solid #2B3A8C">Au programme de cet épisode</div>
 <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}</table></td></tr>
<tr><td bgcolor="{NAVY}" align="center" style="padding:6px 24px 0 24px;font-family:{FONT};font-size:16px;color:#FFFFFF">
 <p style="margin:0 0 14px 0;font-weight:bold">Retrouvez l'épisode complet sur YouTube 👇</p>{youtube(c)}</td></tr>
{closing_block(c, "#DCE3F7", NAVY, "#FFFFFF")}"""
    return shell(c, NAVY_DEEP, body, NAVY_DEEP, "#8A93B2", NAVY)


# ---------------------------------------------------------------------------------------------------------------
# B · Héros
# ---------------------------------------------------------------------------------------------------------------

def heros(c: dict) -> str:
    top = (f'<tr><td><a href="{esc(c["url"])}"><img src="{c["rel"]("hero")}" width="600" alt="AI Corner {esc(c["episode"])} : {esc(c["theme"])}" '
           f'style="display:block;width:100%;max-width:600px"></a></td></tr>' if c["img"].get("hero")
           else f'<tr><td bgcolor="{BLUE_DARK}" style="padding:48px 40px;font-family:{FONT};font-size:30px;font-weight:bold;color:#FFFFFF">{esc(c["theme"])}</td></tr>')
    rows = "".join(
        f'<tr><td bgcolor="{LIGHT}" style="border-left:4px solid {BLUE};border-radius:0 12px 12px 0;padding:14px 18px;font-family:{FONT};'
        f'font-size:15px;line-height:1.55;color:{NAVY_MID}"><span style="color:{BLUE};font-weight:bold">{k:02d}</span>&nbsp; '
        f'<strong style="color:{NAVY};font-size:16px">{esc(p.get("title"))}</strong><br>{esc(p.get("text"))}</td></tr>'
        f'<tr><td height="12" style="font-size:0;line-height:0">&nbsp;</td></tr>' for k, p in enumerate(c["program"], 1))
    body = f"""{top}
<tr><td bgcolor="{NAVY}" class="pad" style="padding:20px 40px;font-family:{FONT}">
 <span style="font-size:19px;font-weight:bold;color:#FFFFFF">{esc(c["guest"])}</span>
 <span style="font-size:14px;color:#9DB8FF">&nbsp;·&nbsp;{esc(c["role"])}</span></td></tr>
<tr><td class="pad" style="padding:30px 40px 0 40px;font-family:{FONT};font-size:17px;line-height:1.6;color:{NAVY_MID}">
 <!--HELLO--><p style="margin:0 0 16px 0;font-weight:bold;color:{NAVY};font-size:20px;line-height:1.45">{para(c["hook"])}</p><p style="margin:0">{para(c["intro"])}</p></td></tr>
<tr><td align="center">{button(c)}</td></tr>
<tr><td class="pad" style="padding:6px 40px 0 40px;font-family:{FONT}">
 <div style="font-size:20px;font-weight:bold;color:{NAVY};padding-bottom:16px">Au programme de cet épisode</div>
 <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}</table></td></tr>
<tr><td align="center" style="padding:4px 24px 0 24px;font-family:{FONT};font-size:16px;color:{NAVY}">
 <p style="margin:0 0 14px 0;font-weight:bold">Retrouvez l'épisode complet sur YouTube 👇</p>{youtube(c)}</td></tr>
{closing_block(c, NAVY_MID, "#FFFFFF", NAVY)}"""
    return shell(c, "#E9EEF9", body, NAVY, "#9DB8FF")


# ---------------------------------------------------------------------------------------------------------------
# C · Éditorial
# ---------------------------------------------------------------------------------------------------------------

def editorial(c: dict) -> str:
    guest = (f'<img src="{c["rel"]("guest")}" width="72" height="72" alt="{esc(c["guest"])}" '
             f'style="display:block;border-radius:36px;width:72px;height:72px">' if c["img"].get("guest") else "")
    rows = "".join(
        f'<tr><td width="58" valign="top" style="padding:18px 0;border-top:1px solid #E1E7F5;font-family:{FONT};font-size:30px;font-weight:bold;color:{BLUE};line-height:1">{k:02d}</td>'
        f'<td valign="top" style="padding:18px 0;border-top:1px solid #E1E7F5;font-family:{FONT};font-size:15px;line-height:1.55;color:{NAVY_MID}">'
        f'<strong style="color:{NAVY};font-size:17px">{esc(p.get("title"))}</strong><br>{esc(p.get("text"))}</td></tr>'
        for k, p in enumerate(c["program"], 1))
    body = f"""<tr><td bgcolor="{NAVY}" class="pad" style="padding:20px 40px;font-family:{FONT}"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
 <td style="font-size:20px;font-weight:bold;color:#FFFFFF;letter-spacing:.02em">AI <span style="color:{BLUE_SKY}">Corner</span> <span style="color:{BLUE_SKY};font-size:14px">&nbsp;{esc(c["episode"])}</span></td>
 <td align="right" style="font-size:11px;color:#9DB8FF;letter-spacing:.14em;text-transform:uppercase">Le podcast d'AI Partners</td></tr></table></td></tr>
<tr><td class="pad" style="padding:38px 40px 6px 40px;font-family:{FONT}">
 <div style="font-size:13px;font-weight:bold;color:{BLUE};letter-spacing:.14em;text-transform:uppercase;padding-bottom:12px">Nouvel épisode · {esc(c["guest"])}</div>
 <div style="font-size:34px;font-weight:bold;color:{NAVY};line-height:1.15">{esc(c["theme"])}</div></td></tr>
<tr><td class="pad" style="padding:22px 40px 4px 40px"><table role="presentation" cellpadding="0" cellspacing="0"><tr>
 <td width="72" valign="middle">{guest}</td>
 <td valign="middle" style="padding-left:16px;font-family:{FONT}"><div style="font-size:16px;font-weight:bold;color:{NAVY}">{esc(c["guest"])}</div>
  <div style="font-size:13px;color:#5A6488;padding-top:3px">{esc(c["role"])}</div></td></tr></table></td></tr>
<tr><td class="pad" style="padding:22px 40px 0 40px;font-family:{FONT};font-size:17px;line-height:1.6;color:{NAVY_MID}">
 <!--HELLO--><p style="margin:0 0 18px 0;padding-left:18px;border-left:4px solid {BLUE};font-weight:bold;color:{NAVY};font-size:19px;line-height:1.45">{para(c["hook"])}</p><p style="margin:0">{para(c["intro"])}</p></td></tr>
<tr><td height="28" style="font-size:0;line-height:0">&nbsp;</td></tr>
<tr><td bgcolor="{BLUE_DARK}" align="center" class="pad" style="padding:30px 40px;font-family:{FONT}">
 <div style="font-size:19px;font-weight:bold;color:#FFFFFF;padding-bottom:4px">Cet épisode est disponible</div>
 {button(c, "#FFFFFF", BLUE_DARK, "16px auto 0 auto")}</td></tr>
<tr><td class="pad" style="padding:34px 40px 8px 40px;font-family:{FONT}">
 <div style="font-size:22px;font-weight:bold;color:{NAVY};padding-bottom:16px">Au programme</div>
 <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}</table></td></tr>
<tr><td align="center" style="padding:14px 24px 0 24px">{youtube(c)}</td></tr>
{closing_block(c, NAVY_MID, "#FFFFFF", NAVY)}"""
    return shell(c, "#E9EEF9", body, NAVY, "#9DB8FF")


# ---------------------------------------------------------------------------------------------------------------
# D · Vedette
# ---------------------------------------------------------------------------------------------------------------

def vedette(c: dict) -> str:
    cards = list(c["program"])[:4]

    def card(k: int, p: dict) -> str:
        return (f'<td class="col" width="50%" valign="top" style="padding:0 6px 12px 6px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
                f'<td bgcolor="{LIGHT}" style="border-radius:14px;padding:16px 16px 18px 16px;font-family:{FONT};font-size:14px;line-height:1.5;color:{NAVY_MID}">'
                f'<div style="font-size:22px;font-weight:bold;color:{BLUE};padding-bottom:6px">{k:02d}</div>'
                f'<strong style="color:{NAVY};font-size:16px;line-height:1.3">{esc(p.get("title"))}</strong><br>{esc(p.get("text"))}</td></tr></table></td>')
    grid = "".join("<tr>" + card(i + 1, cards[i]) + (card(i + 2, cards[i + 1]) if i + 1 < len(cards) else '<td class="col" width="50%"></td>') + "</tr>"
                   for i in range(0, len(cards), 2))
    thumb = (f'<tr><td><a href="{esc(c["url"])}"><img src="{c["rel"]("youtube")}" width="600" alt="{esc(c["title"])}" '
             f'style="display:block;width:100%;max-width:600px"></a></td></tr>' if c["img"].get("youtube") else "")
    body = f"""<tr><td bgcolor="{NAVY}" class="pad" style="padding:18px 40px;font-family:{FONT}"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
 <td style="font-size:18px;font-weight:bold;color:#FFFFFF">AI <span style="color:{BLUE_SKY}">Corner</span></td>
 <td align="right" style="font-size:11px;color:#9DB8FF;letter-spacing:.14em;text-transform:uppercase">Nouvel épisode · {esc(c["episode"])}</td></tr></table></td></tr>
{thumb}
<tr><td bgcolor="{NAVY}" class="pad" style="padding:26px 40px 30px 40px;font-family:{FONT}">
 <div style="font-size:28px;font-weight:bold;color:#FFFFFF;line-height:1.2">{esc(c["theme"])}</div>
 <div style="font-size:15px;color:#9DB8FF;padding-top:12px"><strong style="color:#FFFFFF">{esc(c["guest"])}</strong> · {esc(c["role"])}</div></td></tr>
<tr><td class="pad" style="padding:30px 40px 0 40px;font-family:{FONT};font-size:17px;line-height:1.6;color:{NAVY_MID}">
 <!--HELLO--><p style="margin:0 0 16px 0;font-weight:bold;color:{NAVY};font-size:20px;line-height:1.45">{para(c["hook"])}</p><p style="margin:0">{para(c["intro"])}</p></td></tr>
<tr><td align="center">{button(c)}</td></tr>
<tr><td class="pad" style="padding:6px 34px 0 34px;font-family:{FONT}">
 <div style="font-size:20px;font-weight:bold;color:{NAVY};padding:0 6px 14px 6px">Au programme de cet épisode</div>
 <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{grid}</table></td></tr>
{closing_block(c, NAVY_MID, "#FFFFFF", NAVY)}"""
    return shell(c, "#E9EEF9", body, NAVY, "#9DB8FF")



# ---------------------------------------------------------------------------------------------------------------
# Variantes du style « Vedette » AVEC THOMAS EN HAUT (Arthur, 14/10/2026 : « comme le mail part de Thomas, les gens vont lire
# s'ils voient Thomas au début : il faut le mettre en haut aussi, avec l'invité ; fais des variations dans le style de la
# dernière ») : duo, ronds, lettre, duo_nuit
# ---------------------------------------------------------------------------------------------------------------

def make_duo(d: Path, mail: dict, host_png: Path | None, guest_png: Path | None, shot, fonts_css: str, uri) -> Path | None:
    """Image « duo » : Thomas (à gauche) et l'invité (à droite) face à face sur le dégradé bleu de la charte."""
    if not (host_png and guest_png):
        return None
    page = (f"<html><head><meta charset='utf-8'><style>{fonts_css}*{{margin:0}}"
            f"body{{width:1200px;height:700px;background:linear-gradient(160deg,{BLUE} 0%,{BLUE_DARK} 64%,{NAVY} 100%);"
            f"font-family:M,Arial;position:relative;overflow:hidden}}"
            f".a{{position:absolute;bottom:0;height:610px;filter:drop-shadow(0 30px 60px rgba(5,15,60,.40))}}"
            f".h{{left:-30px}}.g{{right:-40px;height:640px}}"
            f".pill{{position:absolute;left:50%;top:44px;transform:translateX(-50%);background:rgba(255,255,255,.18);color:#fff;"
            f"font-weight:700;font-size:26px;letter-spacing:.14em;padding:14px 28px;border-radius:999px;text-transform:uppercase;z-index:3}}"
            f"</style></head><body><img class='a h' src='{uri(host_png)}'><img class='a g' src='{uri(guest_png)}'>"
            f"<div class='pill'>AI Corner · {esc(mail['episode'])}</div></body></html>")
    return shot(page, 1200, 700, d / "duo.png")


def square_photo(png: Path | None, out: Path) -> Path | None:
    """Photo carrée à coins arrondis (dégradé bleu de la charte), comme `invite.jpg`."""
    if not png:
        return None
    from PIL import Image, ImageDraw
    size = 640
    bg = Image.new("RGB", (size, size))
    dr = ImageDraw.Draw(bg)
    for y in range(size):
        k = y / size
        dr.line([(0, y), (size, y)], fill=tuple(int(a + (b - a) * k) for a, b in zip((37, 138, 243), (10, 71, 182))))
    im = Image.open(png).convert("RGBA")
    sc = size * 1.05 / im.width
    im = im.resize((int(im.width * sc), int(im.height * sc)), Image.Resampling.LANCZOS)
    bg.paste(im, ((size - im.width) // 2, int(size * 0.06)), im)
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size - 1, size - 1], 48, fill=255)
    flat = Image.new("RGB", (size, size), (255, 255, 255))
    flat.paste(bg, (0, 0), m)
    flat.save(out, quality=90)
    return out


def _grid(cards: list, dark: bool = False) -> str:
    """Programme en cartes, 2 par ligne (empilées sur téléphone)."""
    bg, num, tt, tx = (NAVY_MID, BLUE_SKY, "#FFFFFF", "#C9D3F5") if dark else (LIGHT, BLUE, NAVY, NAVY_MID)

    def card(k, p):
        return (f'<td class="col" width="50%" valign="top" style="padding:0 6px 12px 6px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
                f'<td bgcolor="{bg}" style="border-radius:14px;padding:16px 16px 18px 16px;font-family:{FONT};font-size:14px;line-height:1.5;color:{tx}">'
                f'<div style="font-size:22px;font-weight:bold;color:{num};padding-bottom:6px">{k:02d}</div>'
                f'<strong style="color:{tt};font-size:16px;line-height:1.3">{esc(p.get("title"))}</strong><br>{esc(p.get("text"))}</td></tr></table></td>')
    cards = list(cards)[:4]
    return "".join("<tr>" + card(i + 1, cards[i]) + (card(i + 2, cards[i + 1]) if i + 1 < len(cards) else '<td class="col" width="50%"></td>') + "</tr>"
                   for i in range(0, len(cards), 2))


def _topbar(c: dict) -> str:
    return (f'<tr><td bgcolor="{NAVY}" class="pad" style="padding:18px 40px;font-family:{FONT}"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
            f'<td style="font-size:18px;font-weight:bold;color:#FFFFFF">AI <span style="color:{BLUE_SKY}">Corner</span></td>'
            f'<td align="right" style="font-size:11px;color:#9DB8FF;letter-spacing:.14em;text-transform:uppercase">Nouvel épisode · {esc(c["episode"])}</td></tr></table></td></tr>')


def _duo_hero(c: dict) -> str:
    if not c["img"].get("duo"):
        return ""
    return (f'<tr><td><a href="{esc(c["url"])}"><img src="{c["rel"]("duo")}" width="600" alt="{esc(c["host_name"])} et {esc(c["guest"])}" '
            f'style="display:block;width:100%;max-width:600px"></a></td></tr>')


def _thumb(c: dict, label: str = "") -> str:
    if not c["img"].get("youtube"):
        return ""
    lab = (f'<tr><td align="center" style="padding:6px 24px 14px 24px;font-family:{FONT};font-size:16px;font-weight:bold;color:{label}">'
           f"Retrouvez l'épisode complet sur YouTube 👇</td></tr>") if label else ""
    return (lab + f'<tr><td><a href="{esc(c["url"])}"><img src="{c["rel"]("youtube")}" width="600" alt="{esc(c["title"])}" '
            f'style="display:block;width:100%;max-width:600px"></a></td></tr>')


def _title_band(c: dict, with_names: bool = True) -> str:
    names = (f'<div style="font-size:15px;color:#9DB8FF;padding-top:12px"><strong style="color:#FFFFFF">{esc(c["host_name"])}</strong> reçoit '
             f'<strong style="color:#FFFFFF">{esc(c["guest"])}</strong> · {esc(c["role"])}</div>') if with_names else ""
    return (f'<tr><td bgcolor="{NAVY}" class="pad" style="padding:26px 40px 30px 40px;font-family:{FONT}">'
            f'<div style="font-size:28px;font-weight:bold;color:#FFFFFF;line-height:1.2">{esc(c["theme"])}</div>{names}</td></tr>')


def _text_block(c: dict, dark: bool = False, hook: bool = True) -> str:
    fg, strong = ("#DCE3F7", "#FFFFFF") if dark else (NAVY_MID, NAVY)
    bg = NAVY if dark else "#FFFFFF"
    h = (f'<p style="margin:0 0 16px 0;font-weight:bold;color:{strong};font-size:20px;line-height:1.45">{para(c["hook"])}</p>' if hook else "")
    return (f'<tr><td bgcolor="{bg}" class="pad" style="padding:30px 40px 0 40px;font-family:{FONT};font-size:17px;line-height:1.6;color:{fg}">'
            f'<!--HELLO-->{h}<p style="margin:0">{para(c["intro"])}</p></td></tr>')


def duo(c: dict) -> str:
    """D1 · Duo : Thomas et l'invité en grand, puis le titre ; corps clair, programme en cartes, miniature en bas."""
    body = f"""{_topbar(c)}
{_duo_hero(c)}
{_title_band(c)}
{_text_block(c)}
<tr><td align="center">{button(c)}</td></tr>
<tr><td class="pad" style="padding:6px 34px 0 34px;font-family:{FONT}">
 <div style="font-size:20px;font-weight:bold;color:{NAVY};padding:0 6px 14px 6px">Au programme de cet épisode</div>
 <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{_grid(c["program"])}</table></td></tr>
<tr><td align="center" style="padding:10px 24px 0 24px;font-family:{FONT};font-size:16px;font-weight:bold;color:{NAVY}">Retrouvez l'épisode complet sur YouTube 👇</td></tr>
<tr><td align="center" style="padding:14px 24px 0 24px">{youtube(c)}</td></tr>
{closing_block(c, NAVY_MID, "#FFFFFF", NAVY)}"""
    return shell(c, "#E9EEF9", body, NAVY, "#9DB8FF")


def ronds(c: dict) -> str:
    """D2 · Ronds : bandeau bleu nuit avec les deux photos rondes et « Thomas reçoit … », puis la miniature (comme Vedette)."""
    def person(key, name, role):
        img = (f'<img src="{c["rel"](key)}" width="104" height="104" alt="{esc(name)}" style="display:block;margin:0 auto;border-radius:52px;'
               f'width:104px;height:104px;border:3px solid {BLUE}">' if c["img"].get(key) else "")
        return (f'<td class="col" width="50%" align="center" valign="top" style="padding:0 8px;font-family:{FONT}">{img}'
                f'<div style="font-size:17px;font-weight:bold;color:#FFFFFF;padding-top:12px">{esc(name)}</div>'
                f'<div style="font-size:12px;color:#9DB8FF;padding-top:3px;line-height:1.4">{esc(role)}</div></td>')
    band = (f'<tr><td bgcolor="{NAVY}" class="pad" style="padding:8px 30px 26px 30px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
            f'{person("host", c["host_name"], c["host_role"])}{person("guest", c["guest"], c["role"])}</tr></table></td></tr>')
    body = f"""{_topbar(c)}
{band}
{_thumb(c)}
{_title_band(c, with_names=False)}
{_text_block(c)}
<tr><td align="center">{button(c)}</td></tr>
<tr><td class="pad" style="padding:6px 34px 0 34px;font-family:{FONT}">
 <div style="font-size:20px;font-weight:bold;color:{NAVY};padding:0 6px 14px 6px">Au programme de cet épisode</div>
 <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{_grid(c["program"])}</table></td></tr>
{closing_block(c, NAVY_MID, "#FFFFFF", NAVY)}"""
    return shell(c, "#E9EEF9", body, NAVY, "#9DB8FF")


def lettre(c: dict) -> str:
    """D3 · Lettre : le mail s'ouvre sur Thomas (photo + mot d'accroche, « Bonjour… »), puis la miniature avec l'invité."""
    me = (f'<img src="{c["rel"]("host")}" width="96" height="96" alt="{esc(c["host_name"])}" style="display:block;border-radius:20px;width:96px;height:96px">'
          if c["img"].get("host") else "")
    guest = (f'<img src="{c["rel"]("guest")}" width="56" height="56" alt="{esc(c["guest"])}" style="display:block;border-radius:28px;width:56px;height:56px">'
             if c["img"].get("guest") else "")
    head = f"""<tr><td bgcolor="{NAVY}" class="pad" style="padding:26px 40px 8px 40px;font-family:{FONT}"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
 <td class="col" width="96" valign="middle">{me}</td>
 <td class="col" valign="middle" style="padding-left:18px"><div style="font-size:21px;font-weight:bold;color:#FFFFFF">{esc(c["host_name"])}</div>
  <div style="font-size:13px;color:#9DB8FF;padding-top:4px">{esc(c["host_role"])}</div>
  <div style="font-size:12px;color:{BLUE_SKY};padding-top:8px;letter-spacing:.14em;text-transform:uppercase">Un mot sur AI Corner {esc(c["episode"])}</div></td></tr></table></td></tr>
<tr><td bgcolor="{NAVY}" class="pad" style="padding:14px 40px 30px 40px;font-family:{FONT};font-size:19px;line-height:1.5;color:#FFFFFF">
 <!--HELLO--><span style="font-weight:bold">{para(c["hook"])}</span></td></tr>"""
    band = (f'<tr><td bgcolor="{NAVY_MID}" class="pad" style="padding:20px 40px;font-family:{FONT}"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
            f'<td valign="middle"><div style="font-size:24px;font-weight:bold;color:#FFFFFF;line-height:1.2">{esc(c["theme"])}</div>'
            f'<div style="font-size:14px;color:#9DB8FF;padding-top:8px"><strong style="color:#FFFFFF">{esc(c["guest"])}</strong> · {esc(c["role"])}</div></td>'
            f'<td width="56" align="right" valign="middle" style="padding-left:14px">{guest}</td></tr></table></td></tr>')
    body = f"""{_topbar(c)}
{head}
{_thumb(c)}
{band}
<tr><td class="pad" style="padding:28px 40px 0 40px;font-family:{FONT};font-size:17px;line-height:1.6;color:{NAVY_MID}"><p style="margin:0">{para(c["intro"])}</p></td></tr>
<tr><td align="center">{button(c)}</td></tr>
<tr><td class="pad" style="padding:6px 34px 0 34px;font-family:{FONT}">
 <div style="font-size:20px;font-weight:bold;color:{NAVY};padding:0 6px 14px 6px">Au programme de cet épisode</div>
 <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{_grid(c["program"])}</table></td></tr>
{closing_block(c, NAVY_MID, "#FFFFFF", NAVY)}"""
    return shell(c, "#E9EEF9", body, NAVY, "#9DB8FF")


def duo_nuit(c: dict) -> str:
    """D4 · Duo nuit : comme Duo, mais tout le corps en bleu nuit (cartes plus claires, texte blanc)."""
    body = f"""{_topbar(c)}
{_duo_hero(c)}
{_title_band(c)}
{_text_block(c, dark=True)}
<tr><td bgcolor="{NAVY}" align="center">{button(c)}</td></tr>
<tr><td bgcolor="{NAVY}" class="pad" style="padding:6px 34px 0 34px;font-family:{FONT}">
 <div style="font-size:20px;font-weight:bold;color:#FFFFFF;padding:0 6px 14px 6px">Au programme de cet épisode</div>
 <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{_grid(c["program"], dark=True)}</table></td></tr>
<tr><td bgcolor="{NAVY}" align="center" style="padding:10px 24px 14px 24px;font-family:{FONT};font-size:16px;font-weight:bold;color:#FFFFFF">Retrouvez l'épisode complet sur YouTube 👇</td></tr>
<tr><td bgcolor="{NAVY}" align="center" style="padding:0 24px">{youtube(c)}</td></tr>
{closing_block(c, "#DCE3F7", NAVY, "#FFFFFF")}"""
    return shell(c, NAVY_DEEP, body, NAVY_DEEP, "#8A93B2", NAVY)


BUILDERS = {"nuit": nuit, "heros": heros, "editorial": editorial, "vedette": vedette,
            "duo": duo, "ronds": ronds, "lettre": lettre, "duo_nuit": duo_nuit}
VARIANTES = ["vedette", "duo", "ronds", "lettre", "duo_nuit"]


def context(brand_cfg: dict, mail: dict, imgs: dict, title: str) -> dict:
    return {"subject": mail.get("subject", ""), "preheader": mail.get("preheader", ""), "episode": mail.get("episode", ""),
            "guest": mail.get("guest", ""), "role": mail.get("role", ""), "theme": mail.get("theme", ""),
            "hook": mail.get("hook", ""), "intro": mail.get("intro", ""), "closing": mail.get("closing", ""),
            "program": mail.get("program") or [], "url": mail.get("youtube_url") or "#", "title": title, "img": imgs,
            "button": brand_cfg.get("button") or "REGARDER L'ÉPISODE",
            "host_name": brand_cfg.get("from_name") or "Thomas Spitz", "host_role": brand_cfg.get("host_role") or "CEO d'AI Partners",
            "sig": brand_cfg.get("signature") or "Thomas Spitz<br>CEO et fondateur d'AI Partners",
            "rel": lambda k: f"images/{imgs[k].name}" if imgs.get(k) else ""}
