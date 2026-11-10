"""Deux concepts NOUVEAUX du labo newsletter (10/11/2026), sans lien de forme avec le gabarit actuel ni avec « Nostra » :

A « Verbatim » : mail SOMBRE, qui s'ouvre sur UNE phrase de l'invité en très grand (citation exacte de l'épisode, 5:15), portrait détouré,
   motif montagne de la charte. Pas de cartes ni de puces : « 4 moments à écouter », chacun avec son horodatage en bleu et un lien qui ouvre
   YouTube À CET INSTANT (youtu.be/<id>?t=<s>). Fin = mot de Thomas, réservation.
B « Affiche » : mail CLAIR construit comme une affiche : un « 23 » géant, le portrait de l'invité qui le chevauche, une seule ligne de
   titre. Dessous, le programme est une frise verticale (trait + horodatages), pas des puces.

Les grandes zones visuelles sont des images dessinées par Chrome (Metropolis, motifs) ; tout le reste est du texte de mail (tableaux, styles en
ligne, polices système) avec `alt` complets. Aucun bleu très clair (retour d'Arthur, 10/11/2026).
EXPLORATION : non branchée sur la production. Sortie : travail/newsletter_lab/nouveau/{verbatim,affiche}/ (+ planche.png).
Lancer : python -m clipper.newsletter_lab.piste_nouveau
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from ..newsletter_templates import BLUE, FONT, NAVY, PILL_CLOSE, esc, pill_open

ROOT = Path(__file__).resolve().parents[2]
BRAND = ROOT / "MARQUES" / "ai-corner"
BLACK, INK = "#05070F", "#1B2559"


def _tr(episode: str) -> Path:
    return next((ROOT / "EPISODES" / "ai-corner").glob(f"{episode}_*")) / "travail"


def _secs(mmss: str) -> int:
    m, s = mmss.split(":")
    return int(m) * 60 + int(s)


def _uri(p: Path) -> str:
    return p.resolve().as_uri()


def _render(page: str, w: int, h: int, f: Path) -> tuple[int, int]:
    """Rend `page` (HTML) à w x h px (échelle 1 = déjà le double de l'affichage) et enregistre en PNG."""
    from ..newsletter import _shot
    _shot(page, w, h, f)
    from PIL import Image
    return Image.open(f).size


def _fonts() -> str:
    from ..config import Brand
    from ..newsletter import _fonts_css
    return _fonts_css(Brand("ai-corner"))


def _btn(label: str, href: str, bg: str) -> str:
    return (pill_open(bg, "0") + f'<a href="{esc(href)}" style="display:inline-block;padding:16px 34px;font-family:{FONT};font-size:16px;'
            f'font-weight:bold;letter-spacing:.03em;color:#FFFFFF;text-decoration:none">{esc(label)}</a>' + PILL_CLOSE)


def verbatim(tr: Path, mail: dict, yt: str, base: Path) -> Path:
    out = base / "verbatim"
    (out / "images").mkdir(parents=True, exist_ok=True)
    shutil.copy2(tr / "newsletter" / "images" / "thomas_rond.jpg", out / "images" / "thomas_rond.jpg")
    guest = tr / "carrousel" / "assets" / "guest.png"
    mont = BRAND / "assets" / "outro_bg.png"
    # --- hero : la phrase de Nicolas (transcript, 315 s : « attention, c'est un marché de vendeurs »)
    hero = (f"<html><head><style>{_fonts()}body{{margin:0}}</style></head><body><div style=\"position:relative;width:1280px;height:1500px;"
            f"background:{BLACK};overflow:hidden;font-family:M\">"
            f"<img src='{_uri(mont)}' style='position:absolute;right:-260px;top:-40px;width:1500px;mix-blend-mode:screen;opacity:.9'>"
            f"<div style='position:absolute;left:72px;top:72px;display:flex;align-items:center;gap:22px;color:#fff;font-weight:800;font-size:46px'>"
            f"AI Corner<span style='background:{BLUE};border-radius:999px;padding:8px 26px;font-size:30px'>Épisode 23</span></div>"
            f"<img src='{_uri(guest)}' style='position:absolute;right:-300px;bottom:0;height:1060px'>"
            f"<div style='position:absolute;left:0;right:0;bottom:0;height:260px;background:linear-gradient(to bottom,rgba(5,7,15,0),{BLACK})'></div>"
            f"<div style='position:absolute;left:72px;top:290px;width:760px;color:#fff;font-weight:800;font-size:132px;line-height:1.04;"
            f"letter-spacing:-.03em'><span style='color:{BLUE}'>«</span>&nbsp;C'est un <span style='color:{BLUE}'>marché de vendeurs</span>.</div>"
            f"</div></body></html>")
    _render(hero, 1280, 1500, out / "images" / "hero.png")

    base_yt = yt.split("?")[0]
    rows = ""
    for p in mail["program"]:
        s = _secs(p["chapter"])
        href = f"{base_yt}?t={s}"
        rows += (f'<tr><td style="padding:22px 0;border-top:1px solid #26305F"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
                 f'<td valign="top" width="92" style="width:92px;padding:2px 18px 0 0"><a href="{esc(href)}" style="display:inline-block;background:{BLUE};'
                 f'border-radius:999px;padding:7px 14px;font-family:{FONT};font-size:15px;font-weight:bold;color:#FFFFFF;text-decoration:none">&#9654; {esc(p["chapter"])}</a></td>'
                 f'<td valign="top" style="font-family:{FONT};font-size:16px;line-height:1.6;color:#C9D3F4"><a href="{esc(href)}" style="color:#FFFFFF;'
                 f'font-size:20px;font-weight:bold;line-height:1.3;text-decoration:none">{esc(p["title"])}</a><br>{esc(p["text"])}</td></tr></table></td></tr>')
    page = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark"><title>{esc(mail["subject"])}</title></head>
<body style="margin:0;padding:0;background:{BLACK}">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{esc(mail["preheader"])}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="{BLACK}"><tr><td align="center" style="padding:0">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" bgcolor="{BLACK}" style="width:100%;max-width:640px;text-align:left">
<tr><td><a href="{esc(yt)}"><img src="images/hero.png" width="640" alt="« C'est un marché de vendeurs. » Nicolas Comestaz, VP Global Data &amp; AI Center of Excellence chez Coty, invité d'AI Corner, épisode 23" style="display:block;width:100%;max-width:640px;height:auto;border:0"></a></td></tr>
<tr><td style="padding:6px 28px 26px 28px;font-family:{FONT};font-size:16px;line-height:1.5;color:#8FA0D6"><strong style="color:#FFFFFF;font-size:18px">Nicolas Comestaz</strong><br>VP Global Data &amp; AI Center of Excellence, Coty · 5:15 dans l'épisode</td></tr>
<tr><td style="padding:10px 28px 6px 28px;font-family:{FONT};font-size:20px;line-height:1.5;font-weight:bold;color:#FFFFFF">{esc(mail["hook"].split(" Vos équipes")[0])}</td></tr>
<tr><td style="padding:12px 28px 8px 28px">{_btn("Regarder l'épisode", yt, BLUE)}</td></tr>
<tr><td style="padding:34px 28px 6px 28px;font-family:{FONT};font-size:14px;font-weight:bold;letter-spacing:.14em;color:#8FB3F5">4 MOMENTS À ÉCOUTER</td></tr>
<tr><td style="padding:0 28px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}</table></td></tr>
<tr><td style="padding:14px 28px 0 28px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid #26305F"><tr>
<td valign="top" width="64" style="width:64px;padding:28px 16px 0 0"><img src="images/thomas_rond.jpg" width="56" height="56" alt="Thomas Spitz" style="display:block;border:0;border-radius:28px;width:56px;height:56px"></td>
<td valign="top" style="padding-top:28px;font-family:{FONT};font-size:18px;line-height:1.6;color:#E6EBFB">{esc(mail["closing"])}<br><strong style="color:#FFFFFF">Thomas Spitz</strong><span style="color:#8FA0D6">, CEO et fondateur d'AI Partners</span></td></tr></table></td></tr>
<tr><td style="padding:34px 28px 8px 28px;font-family:{FONT};font-size:24px;line-height:1.25;font-weight:bold;color:#FFFFFF">Vos équipes testent l'IA. Et après ?</td></tr>
<tr><td style="padding:0 28px 18px 28px;font-family:{FONT};font-size:16px;line-height:1.6;color:#C9D3F4">Passons de l'expérimentation à l'impact : 30 minutes avec moi pour en parler.</td></tr>
<tr><td style="padding:0 28px 48px 28px">{_btn("Réserver un échange avec Thomas", "https://calendly.com/", "#FFFFFF").replace("color:#FFFFFF;text-decoration", f"color:{NAVY};text-decoration")}</td></tr>
</table></td></tr></table></body></html>"""
    (out / "email.html").write_text(page, encoding="utf-8")
    return out


def affiche(tr: Path, mail: dict, yt: str, base: Path) -> Path:
    out = base / "affiche"
    (out / "images").mkdir(parents=True, exist_ok=True)
    shutil.copy2(tr / "newsletter" / "images" / "thomas_rond.jpg", out / "images" / "thomas_rond.jpg")
    guest = tr / "carrousel" / "assets" / "guest.png"
    hero = (f"<html><head><style>{_fonts()}body{{margin:0}}</style></head><body><div style=\"position:relative;width:1280px;height:1400px;"
            f"background:#fff;overflow:hidden;font-family:M\">"
            f"<div style='position:absolute;left:30px;top:100px;font-weight:800;font-size:880px;line-height:1;letter-spacing:-.06em;color:{NAVY}'>23</div>"
            f"<img src='{_uri(guest)}' style='position:absolute;left:520px;bottom:0;height:1080px'>"
            f"<div style='position:absolute;left:56px;top:48px;font-weight:800;font-size:40px;color:{BLUE};letter-spacing:.06em'>AI CORNER · ÉPISODE</div>"
            f"</div></body></html>")
    _render(hero, 1280, 1400, out / "images" / "hero.png")
    title = _render_title(out, "Comment passer de l'expérimentation à l'impact ?", 76)
    steps = ""
    n = len(mail["program"])
    for i, p in enumerate(mail["program"]):
        last = i == n - 1
        line = "" if last else f'border-left:2px solid {NAVY};'
        steps += (f'<tr><td valign="top" width="86" style="width:86px;padding:0 0 0 0"><table role="presentation" cellpadding="0" cellspacing="0"><tr>'
                  f'<td style="font-family:{FONT};font-size:15px;font-weight:bold;color:{NAVY};padding:2px 14px {0 if last else 28}px 0;text-align:right;width:56px">{esc(p["chapter"])}</td>'
                  f'<td style="width:14px;padding:6px 0 0 0" valign="top"><div style="width:12px;height:12px;border-radius:6px;background:{BLUE}"></div></td></tr></table></td>'
                  f'<td valign="top" style="{line}padding:0 0 {0 if last else 28}px 22px;font-family:{FONT};font-size:16px;line-height:1.6;color:{INK}">'
                  f'<strong style="color:{NAVY};font-size:19px;line-height:1.3">{esc(p["title"])}</strong><br>{esc(p["text"])}</td></tr>')
    page = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light"><title>{esc(mail["subject"])}</title></head>
<body style="margin:0;padding:0;background:#FFFFFF">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{esc(mail["preheader"])}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#FFFFFF"><tr><td align="center" style="padding:0 16px">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="width:100%;max-width:640px;text-align:left">
<tr><td style="padding:16px 0 0 0"><a href="{esc(yt)}"><img src="images/hero.png" width="640" alt="AI Corner, épisode 23 : Nicolas Comestaz, VP Global Data &amp; AI Center of Excellence chez Coty" style="display:block;width:100%;max-width:640px;height:auto;border:0;border-radius:14px"></a></td></tr>
<tr><td style="padding:16px 0 0 0;font-family:{FONT};font-size:16px;line-height:1.5;color:{INK}"><strong style="font-size:18px;color:{NAVY}">Nicolas Comestaz</strong><br>VP Global Data &amp; AI Center of Excellence, Coty</td></tr>
<tr><td style="padding:30px 0 10px 0">{title}</td></tr>
<tr><td style="font-family:{FONT};font-size:17px;line-height:1.65;color:{INK};padding:0 0 22px 0">{esc(mail["intro_court"])}</td></tr>
<tr><td style="padding:0 0 44px 0">{_btn("Regarder l'épisode", yt, NAVY)}</td></tr>
<tr><td><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{steps}</table></td></tr>
<tr><td style="padding:44px 0 0 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="{NAVY}" style="background-color:{NAVY};border-radius:16px"><tr><td style="padding:30px 30px 32px 30px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td valign="top" width="64" style="width:64px;padding:0 16px 0 0"><img src="images/thomas_rond.jpg" width="56" height="56" alt="Thomas Spitz" style="display:block;border:0;border-radius:28px;width:56px;height:56px"></td>
<td valign="top" style="font-family:{FONT};font-size:18px;line-height:1.6;color:#FFFFFF">{esc(mail["closing"])}<br><strong>Thomas Spitz</strong><span style="color:#B9C6F2">, CEO et fondateur d'AI Partners</span></td></tr></table>
<div style="padding-top:26px">{_btn("Réserver un échange avec Thomas", "https://calendly.com/", BLUE)}</div></td></tr></table></td></tr>
<tr><td height="40" style="font-size:0;line-height:0">&nbsp;</td></tr>
</table></td></tr></table></body></html>"""
    (out / "email.html").write_text(page, encoding="utf-8")
    return out


def _render_title(out: Path, text: str, px: int) -> str:
    from PIL import Image, ImageChops
    f = out / "images" / "titre.png"
    page = (f"<html><head><style>{_fonts()}</style></head><body style='margin:0;background:#fff'><div style=\"width:1240px;padding:20px;font-family:M;"
            f"font-weight:800;font-size:{px}px;line-height:1.08;letter-spacing:-.025em;color:{NAVY};text-wrap:balance\">{text}</div></body></html>")
    _render(page, 1280, 700, f)
    im = Image.open(f).convert("RGB")
    b = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    im = im.crop((20, max(0, b[1] - 8), 1280, b[3] + 8))
    im.save(f)
    return (f'<h1 style="margin:0;font-size:0;line-height:0"><img src="images/titre.png" width="630" height="{im.size[1] // 2}" alt="{esc(text)}" '
            f'style="display:block;width:100%;max-width:630px;height:auto;border:0"></h1>')


def preview(out: Path, h: int) -> Path:
    import subprocess
    import tempfile

    from ..thumbnail import _browser
    png = out / "apercu.png"
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        subprocess.run([_browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                        f"--user-data-dir={Path(td) / 'prof'}", "--virtual-time-budget=4000", "--force-device-scale-factor=1",
                        f"--window-size=700,{h}", f"--screenshot={png}", (out / "email.html").as_uri()],
                       capture_output=True, timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return png


def main(episode: str = "E23") -> None:
    tr = _tr(episode)
    mail = json.loads((tr / "newsletter" / "contenu.json").read_text(encoding="utf-8"))
    yt = mail["youtube_url"]
    base = tr / "newsletter_lab" / "nouveau"
    a = verbatim(tr, mail, yt, base)
    b = affiche(tr, mail, yt, base)
    print(preview(a, 2330))
    print(preview(b, 2150))


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--episode") + 1] if "--episode" in sys.argv else "E23")
