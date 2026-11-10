"""Concept « Lumière » du labo newsletter (10/11/2026), d'après les retours d'Arthur sur les trois concepts « wahou » :
- trop foncé -> page BLANCHE ; seul le visuel d'ouverture est dans une arche bleu nuit, et le bloc final de réservation ;
- on garde l'onde sonore animée (version bleu nuit sur blanc) et la frise verticale du programme ;
- PAS d'horodatage dans la frise (« ça n'a pas trop de sens ») ;
- contenu repris de la TRANSCRIPTION (phrases et faits dits par Nicolas), pas des textes déjà écrits : `lumiere_contenu.json`.
Palette : noir, bleu foncé, blanc. Image d'ouverture : portrait de la caméra de Nicolas en bichromie dans une arche.

EXPLORATION : non branchée sur la production. Sortie : travail/newsletter_lab/lumiere/.
Lancer : python -m clipper.newsletter_lab.piste_lumiere [--episode E23]
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from ..newsletter_templates import FONT, NAVY, PILL_CLOSE, esc, pill_open
from .piste_nouveau import _fonts, _render, _tr, _uri, preview
from .piste_wahou import duotone

BLACK, INK, MUTED, RULE = "#05070F", "#141B45", "#4A5683", "#D9DEEE"


def waveform_gif(out: Path, frames: int = 10) -> None:
    """Onde sonore animée : barres bleu nuit sur blanc (version claire de celle du concept Verbatim)."""
    import math

    from PIL import Image, ImageDraw
    W, H, n = 1280, 170, 64
    ims = []
    for f in range(frames):
        im = Image.new("RGB", (W, H), (255, 255, 255))
        d = ImageDraw.Draw(im)
        for i in range(n):
            env = math.sin(math.pi * i / (n - 1)) ** 0.8
            h = 12 + 140 * env * abs(math.sin(i * 0.55 + f * 0.63) * math.cos(i * 0.21 - f * 0.4))
            x = 20 + i * (W - 40) / n
            d.rounded_rectangle([x, H / 2 - h / 2, x + 10, H / 2 + h / 2], 5, fill=(21, 29, 83) if h > 38 else (150, 158, 196))
        ims.append(im.quantize(colors=24))
    ims[0].save(out, save_all=True, append_images=ims[1:], duration=110, loop=0, optimize=True)


def btn(label: str, href: str, bg: str, fg: str = "#FFFFFF") -> str:
    return (pill_open(bg, "0") + f'<a href="{esc(href)}" style="display:inline-block;padding:16px 34px;font-family:{FONT};font-size:16px;'
            f'font-weight:bold;letter-spacing:.03em;color:{fg};text-decoration:none">{esc(label)}</a>' + PILL_CLOSE)


def build(episode: str = "E23") -> Path:
    tr = _tr(episode)
    mail = json.loads((tr / "newsletter" / "contenu.json").read_text(encoding="utf-8"))
    c = json.loads((Path(__file__).with_name("lumiere_contenu.json")).read_text(encoding="utf-8"))
    yt = mail["youtube_url"]
    out = tr / "newsletter_lab" / "lumiere"
    img = out / "images"
    img.mkdir(parents=True, exist_ok=True)
    shutil.copy2(tr / "newsletter" / "images" / "thomas_rond.jpg", img / "thomas_rond.jpg")
    guest = duotone(tr / "carrousel" / "assets" / "guest.png", img / "guest_duo.png", grain=4)
    mont = _uri(Path(__file__).resolve().parents[2] / "MARQUES" / "ai-corner" / "assets" / "outro_bg.png")
    waveform_gif(img / "onde.gif")

    quote = c["citation_ouverture"]["texte"].rstrip(".")
    words = quote.split()
    big = " ".join(words)
    hero = (f"<html><head><style>{_fonts()}body{{margin:0}}</style></head><body><div style=\"position:relative;width:1280px;height:1260px;"
            f"background:#fff;overflow:hidden;font-family:M\">"
            f"<div style='position:absolute;left:660px;top:120px;width:560px;height:1140px;border-radius:280px 280px 0 0;background:{NAVY};overflow:hidden'>"
            f"<img src='{mont}' style='position:absolute;left:-380px;top:-60px;width:1400px;mix-blend-mode:screen;opacity:.7'>"
            f"<img src='{_uri(guest)}' style='position:absolute;left:-390px;bottom:0;height:980px'></div>"
            f"<div style='position:absolute;left:60px;top:60px;color:{INK};font-weight:800;font-size:40px;letter-spacing:.04em'>AI CORNER · ÉPISODE 23</div>"
            f"<div style='position:absolute;left:60px;top:280px;width:600px;font-weight:800;font-size:112px;line-height:1.04;letter-spacing:-.03em;color:{BLACK}'>"
            f"<span style='color:transparent;-webkit-text-stroke:3px {BLACK}'>«</span>&nbsp;{esc(big)}.</div>"
            f"<div style='position:absolute;left:60px;bottom:110px;color:{INK};font-weight:800;font-size:46px'>Nicolas Comestaz</div>"
            f"<div style='position:absolute;left:60px;bottom:56px;color:{MUTED};font-weight:400;font-size:30px'>Coty · Data &amp; AI Center of Excellence</div>"
            f"</div></body></html>")
    _render(hero, 1280, 1260, img / "hero.png")

    steps = ""
    n = len(c["etapes"])
    for i, e in enumerate(c["etapes"]):
        last = i == n - 1
        line = f"border-left:2px solid {'#FFFFFF' if last else NAVY};"
        steps += (f'<tr><td valign="top" width="30" style="width:30px;padding:6px 0 0 0"><div style="width:14px;height:14px;border-radius:7px;background:{NAVY}"></div></td>'
                  f'<td valign="top" style="{line}padding:0 0 {0 if last else 30}px 24px;margin-left:-8px;font-family:{FONT};font-size:16px;line-height:1.65;color:{INK}">'
                  f'<strong style="color:{BLACK};font-size:20px;line-height:1.3">{esc(e["titre"])}</strong><br>{esc(e["phrase"])}</td></tr>')

    inner = f"""<tr><td style="padding:16px 0 0 0"><a href="{esc(yt)}"><img src="images/hero.png" width="640" alt="« {esc(quote)}. » Nicolas Comestaz, Data &amp; AI Center of Excellence chez Coty, invité d'AI Corner, épisode 23" style="display:block;width:100%;max-width:640px;height:auto;border:0"></a></td></tr>
<tr><td style="padding:6px 0 0 0"><img src="images/onde.gif" width="640" alt="" style="display:block;width:100%;max-width:640px;height:auto;border:0"></td></tr>
<tr><td style="padding:22px 4px 10px 4px"><h1 style="margin:0;font-family:{FONT};font-size:28px;line-height:1.22;font-weight:bold;letter-spacing:-.01em;color:{BLACK}">{esc(c["question"])}</h1></td></tr>
<tr><td style="padding:0 4px 26px 4px;font-family:{FONT};font-size:17px;line-height:1.65;color:{INK}">{esc(c["intro_thomas"])}</td></tr>
<tr><td style="padding:0 4px 44px 4px">{btn("Regarder l'épisode", yt, NAVY)}</td></tr>
<tr><td style="padding:0 4px 24px 4px;font-family:{FONT};font-size:14px;font-weight:bold;letter-spacing:.14em;color:{MUTED}">CE QUE COTY A MIS EN PLACE</td></tr>
<tr><td style="padding:0 4px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{steps}</table></td></tr>
<tr><td style="padding:44px 4px 0 4px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid {RULE}"><tr>
<td valign="top" width="64" style="width:64px;padding:28px 16px 0 0"><img src="images/thomas_rond.jpg" width="56" height="56" alt="Thomas Spitz" style="display:block;border:0;border-radius:28px;width:56px;height:56px"></td>
<td valign="top" style="padding-top:28px;font-family:{FONT};font-size:18px;line-height:1.6;color:{INK}">{esc(mail["closing"])}<br><strong style="color:{BLACK}">Thomas Spitz</strong><span style="color:{MUTED}">, CEO et fondateur d'AI Partners</span></td></tr></table></td></tr>
<tr><td style="padding:34px 0 0 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="{NAVY}" style="background-color:{NAVY};border-radius:18px"><tr><td style="padding:32px 30px 34px 30px">
<div style="font-family:{FONT};font-size:25px;line-height:1.25;font-weight:bold;letter-spacing:-.01em;color:#FFFFFF;padding-bottom:10px">Vos équipes testent l'IA. Et après ?</div>
<div style="font-family:{FONT};font-size:16px;line-height:1.6;color:#C9D0EC;padding-bottom:22px">Passons de l'expérimentation à l'impact : 30 minutes avec moi pour en parler.</div>
{btn("Réserver un échange avec Thomas", "https://calendly.com/", "#FFFFFF", NAVY)}</td></tr></table></td></tr>
<tr><td height="40" style="font-size:0;line-height:0">&nbsp;</td></tr>"""
    page = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light"><title>{esc(mail["subject"])}</title></head>
<body style="margin:0;padding:0;background:#FFFFFF">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{esc(mail["preheader"])}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#FFFFFF"><tr><td align="center" style="padding:0 16px">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="width:100%;max-width:640px;text-align:left">
{inner}
</table></td></tr></table></body></html>"""
    (out / "email.html").write_text(page, encoding="utf-8")
    return out


if __name__ == "__main__":
    print(preview(build(sys.argv[sys.argv.index("--episode") + 1] if "--episode" in sys.argv else "E23"), 2500))
