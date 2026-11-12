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

NOMS = {"youtube": "YouTube", "spotify": "Spotify", "ausha": "Ausha"}
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
    import yaml
    BOOKING = yaml.safe_load((Path(__file__).resolve().parents[2] / "MARQUES" / "ai-corner" / "brand.yaml").read_text(encoding="utf-8"))["newsletter"]["booking"]["url"]   # agenda de Thomas (comme la production)
    out = tr / "newsletter_lab" / "lumiere"
    img = out / "images"
    img.mkdir(parents=True, exist_ok=True)
    # portrait de Thomas : la photo de profil que Arthur a choisie (E23, 1:56 du rush), recadrée carré centré sur le visage (la photo ronde
    # du gabarit actuel était trop serrée et décentrée)
    from PIL import Image
    Image.open(tr / "photos_profil_thomas" / "profil_large_04.png").convert("RGB").crop((180, 20, 920, 760)).resize((280, 280), Image.Resampling.LANCZOS).save(img / "thomas_portrait.jpg", quality=92)
    from .piste_nostra_v2 import platform_pills
    platform_pills(out)
    plat_urls = {"youtube": mail["youtube_url"], "spotify": "https://open.spotify.com/show/4chUmiipM4KiK4sEdL9BeP", "ausha": "https://podcast.ausha.co/ai-partners-podcast"}
    plats = "".join(
        f'<td align="center" style="padding:0 18px 0 0"><a href="{esc(u)}" style="text-decoration:none"><img src="images/pastille_{k}.png" width="60" height="60" alt="{NOMS[k]}" '
        f'style="display:block;border:0;width:60px;height:60px;margin:0 auto"><span style="display:block;padding-top:6px;font-family:{FONT};font-size:13px;color:{MUTED}">{NOMS[k]}</span></a></td>'
        for k, u in plat_urls.items())
    guest = duotone(tr / "carrousel" / "assets" / "guest.png", img / "guest_duo.png", grain=4)
    mont = _uri(Path(__file__).resolve().parents[2] / "MARQUES" / "ai-corner" / "assets" / "outro_bg.png")
    waveform_gif(img / "onde.gif")

    # --- ouverture « couverture » : panneau bleu nuit (marque + nom de l'invité) à gauche, photo EN COULEUR de la caméra de Nicolas à droite
    #     (modèle : la couverture carrée de « Nostra » d'On Train). Image extraite du rush à 2913 s, recadrée sur le visage.
    from PIL import Image
    frame = tr.parent / "rushs" / "cameras" / "cam1_nicolas.mp4"
    cand = img / "nicolas_2913.jpg"
    if not cand.exists():
        import subprocess
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "2913", "-i", str(frame), "-frames:v", "1", "-q:v", "2", str(cand)],
                       check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    Image.open(cand).convert("RGB").crop((486, 0, 1134, 1080)).resize((720, 1200), Image.Resampling.LANCZOS).save(img / "nicolas_couleur.jpg", quality=92)
    logo = _uri(Path(__file__).resolve().parents[2] / "MARQUES" / "ai-corner" / "assets" / "logo.png")
    quote = c["citation_ouverture"]["texte"].rstrip(".")      # gardée dans le contenu, plus utilisée en ouverture
    hero = (f"<html><head><style>{_fonts()}body{{margin:0}}</style></head><body><div style=\"position:relative;width:1280px;height:1200px;"
            f"background:{NAVY};overflow:hidden;font-family:M;border-radius:36px\">"
            f"<img src='{mont}' style='position:absolute;left:-420px;top:380px;width:1300px;mix-blend-mode:screen;opacity:.55'>"
            f"<img src='{_uri(img / 'nicolas_couleur.jpg')}' style='position:absolute;right:0;top:0;width:720px;height:1200px'>"
            f"<div style='position:absolute;left:72px;top:96px;color:#fff;font-weight:800;font-size:108px;line-height:1;letter-spacing:-.03em'>AI Corner</div>"
            f"<img src='{logo}' style='position:absolute;left:76px;top:236px;height:44px'>"
            f"<div style='position:absolute;left:76px;top:400px;width:110px;height:8px;background:#fff'></div>"
            f"<div style='position:absolute;left:72px;top:480px;width:480px;color:#fff;font-weight:800;font-size:78px;line-height:1.08;letter-spacing:-.01em'>NICOLAS<br>COMESTAZ</div>"
            f"<div style='position:absolute;left:76px;top:700px;color:#C9D0EC;font-weight:400;font-size:36px;line-height:1.3;width:470px'>Data &amp; AI Center of Excellence, Coty</div>"
            f"<div style='position:absolute;left:76px;bottom:80px;border:4px solid #fff;border-radius:999px;padding:10px 34px;color:#fff;font-weight:800;font-size:34px;letter-spacing:.1em'>ÉPISODE 23</div>"
            f"</div></body></html>")
    _render(hero, 1280, 1200, img / "hero.png")

    paras = "".join(f'<p style="margin:0 0 14px 0">{esc(x)}</p>' for x in c["intro_paragraphes"])
    steps = ""
    n = len(c["etapes"])
    for i, e in enumerate(c["etapes"]):
        last = i == n - 1
        line = f"border-left:2px solid {'#FFFFFF' if last else NAVY};"
        steps += (f'<tr><td valign="top" width="30" style="width:30px;padding:6px 0 0 0"><div style="width:14px;height:14px;border-radius:7px;background:{NAVY}"></div></td>'
                  f'<td valign="top" style="{line}padding:0 0 {0 if last else 30}px 24px;margin-left:-8px;font-family:{FONT};font-size:16px;line-height:1.65;color:{INK}">'
                  f'<strong style="color:{BLACK};font-size:20px;line-height:1.3">{esc(e["titre"])}</strong><br>{esc(e["phrase"])}</td></tr>')

    inner = f"""<tr><td style="padding:16px 0 0 0"><a href="{esc(yt)}"><img src="images/hero.png" width="640" alt="AI Corner, épisode 23 : Nicolas Comestaz, Data &amp; AI Center of Excellence chez Coty" style="display:block;width:100%;max-width:640px;height:auto;border:0"></a></td></tr>
<tr><td style="padding:6px 0 0 0"><img src="images/onde.gif" width="640" alt="" style="display:block;width:100%;max-width:640px;height:auto;border:0"></td></tr>
<tr><td style="padding:22px 4px 10px 4px"><h1 style="margin:0;font-family:{FONT};font-size:28px;line-height:1.22;font-weight:bold;letter-spacing:-.01em;color:{BLACK}">{esc(c["question"])}</h1></td></tr>
<tr><td style="padding:0 4px 18px 4px;font-family:{FONT};font-size:19px;line-height:1.55;font-weight:bold;color:{INK}">{esc(c["accroche"])}</td></tr>
<tr><td style="padding:0 4px 12px 4px;font-family:{FONT};font-size:17px;line-height:1.65;color:{INK}">{paras}</td></tr>
<tr><td style="padding:0 4px 44px 4px">{btn("Regarder l'épisode", yt, NAVY)}</td></tr>
<tr><td style="padding:0 4px 24px 4px;font-family:{FONT};font-size:14px;font-weight:bold;letter-spacing:.14em;color:{MUTED}">CE QUE COTY A MIS EN PLACE</td></tr>
<tr><td style="padding:0 4px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{steps}</table></td></tr>
<tr><td style="padding:44px 4px 0 4px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid {RULE}"><tr>
<td valign="top" width="100" style="width:100px;padding:28px 18px 0 0"><img src="images/thomas_portrait.jpg" width="84" height="84" alt="Thomas Spitz, CEO et fondateur d'AI Partners" style="display:block;border:0;border-radius:42px;width:84px;height:84px"></td>
<td valign="top" style="padding-top:28px;font-family:{FONT};font-size:18px;line-height:1.6;color:{INK}">{esc(mail["closing"])}<br><strong style="color:{BLACK}">Thomas Spitz</strong><span style="color:{MUTED}">, CEO et fondateur d'AI Partners</span></td></tr></table></td></tr>
<tr><td style="padding:34px 0 0 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="{NAVY}" style="background-color:{NAVY};border-radius:18px"><tr><td style="padding:32px 30px 34px 30px">
<div style="font-family:{FONT};font-size:25px;line-height:1.25;font-weight:bold;letter-spacing:-.01em;color:#FFFFFF;padding-bottom:10px">Vos équipes testent l'IA. Et après ?</div>
<div style="font-family:{FONT};font-size:16px;line-height:1.6;color:#C9D0EC;padding-bottom:22px">Passons de l'expérimentation à l'impact : 30 minutes avec moi pour en parler.</div>
{btn("Réserver un échange avec Thomas", BOOKING, "#FFFFFF", NAVY)}</td></tr></table></td></tr>
<tr><td style="padding:44px 4px 10px 4px;font-family:{FONT};font-size:22px;line-height:1.3;font-weight:bold;color:{BLACK}">{esc(c["rejoignez"]["titre"])}</td></tr>
<tr><td style="padding:0 4px 20px 4px;font-family:{FONT};font-size:17px;line-height:1.65;color:{INK}">{esc(c["rejoignez"]["texte"])}</td></tr>
<tr><td style="padding:6px 4px 0 4px"><table role="presentation" cellpadding="0" cellspacing="0"><tr>{plats}</tr></table></td></tr>
<tr><td height="48" style="font-size:0;line-height:0">&nbsp;</td></tr>"""
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
    print(preview(build(sys.argv[sys.argv.index("--episode") + 1] if "--episode" in sys.argv else "E23"), 3050))
