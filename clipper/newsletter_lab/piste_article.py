"""Piste « Article » du labo newsletter (10/11/2026) : le mail se lit comme un article de blog pro, sur le modèle de la page
On Train (« Éric Hazan : l'Europe doit choisir… ») : fond blanc, repère de rubrique, très gros titre bleu nuit, chapô, signature
(photo ronde, auteur, date, temps d'écoute), grande image, intertitres numérotés, chiffre-clé, citation, signature, bouton, pied discret.

EXPLORATION : rien ici n'est branché sur `python -m clipper newsletter`. Sortie : travail/newsletter_lab/article/.
Lancer : python -m clipper.newsletter_lab.piste_article [--episode E23]
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import date
from pathlib import Path

from ..newsletter_templates import BLUE, FONT, NAVY, PILL_CLOSE, esc, pill_open

ROOT = Path(__file__).resolve().parents[2]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
INK, MUTED, RULE, SOFT = "#1B2559", "#55618F", "#E3E8F4", "#F4F7FD"


def _dir(episode: str) -> Path:
    return next((ROOT / "EPISODES" / "ai-corner").glob(f"{episode}_*")) / "travail"


def build(episode: str = "E23", title: str = "", duree: str = "47 min") -> Path:
    tr = _dir(episode)
    src = tr / "newsletter"
    mail = json.loads((src / "contenu.json").read_text(encoding="utf-8"))
    out = tr / "newsletter_lab" / "article"
    (out / "images").mkdir(parents=True, exist_ok=True)
    need = ["episode_youtube.jpg", "thomas_rond.jpg", "plateforme_youtube.png", "plateforme_spotify.png", "plateforme_ausha.png",
            "bouton_play.png"] + [f"icone_{p['icon']}.png" for p in mail["program"] if p.get("icon")]
    for n in need:
        if (src / "images" / n).exists():
            shutil.copy2(src / "images" / n, out / "images" / n)
    logo = ROOT / "MARQUES" / "ai-corner" / "assets" / "aip_logo_black.png"
    shutil.copy2(logo, out / "images" / "logo.png")

    url = mail["youtube_url"] or "{{lien_youtube}}"
    h1 = title or "Comment Coty déploie l'IA à grande échelle avec Microsoft Copilot"
    d = date.today()
    quand = f"{d.day} {MOIS[d.month - 1]} {d.year}"
    P = f"font-family:{FONT};color:{INK};font-size:17px;line-height:1.65;margin:0 0 18px 0"

    def section(i: int, p: dict) -> str:
        ico = (f'<img src="images/icone_{p["icon"]}.png" width="26" height="26" alt="" style="display:block;border:0">'
               if p.get("icon") else "")
        return (f'<tr><td style="padding:24px 0 0 0;border-top:1px solid {RULE}">'
                f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
                f'<td style="font-family:{FONT};font-size:14px;font-weight:bold;letter-spacing:.12em;color:{BLUE};padding-bottom:10px">'
                f'{i:02d}</td><td align="right" valign="top" style="padding-bottom:10px">{ico}</td></tr></table>'
                f'<h2 style="font-family:{FONT};font-size:24px;line-height:1.25;font-weight:bold;color:{NAVY};margin:0 0 12px 0">'
                f'{esc(p["title"])}</h2>'
                f'<p style="{P}">{esc(p["text"])}</p></td></tr>'
                '<tr><td height="14" style="font-size:0;line-height:0">&nbsp;</td></tr>')

    sections = "".join(section(i + 1, p) for i, p in enumerate(mail["program"]))
    intro = "".join(f'<p style="{P}">{esc(x)}</p>' for x in mail["intro"].split("\n") if x.strip())
    stat = mail.get("stat") or {}
    stat_html = ""
    if stat:
        stat_html = (f'<tr><td style="padding:6px 0 34px 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
                     f'<tr><td bgcolor="{SOFT}" style="background-color:{SOFT};border-radius:16px;padding:26px 28px">'
                     f'<div style="font-family:{FONT};font-size:56px;line-height:1;font-weight:bold;color:{BLUE}">{esc(stat["value"])}</div>'
                     f'<div style="font-family:{FONT};font-size:17px;line-height:1.4;color:{INK};padding-top:8px">'
                     f'{esc(stat["label"])}, dit Nicolas Comestaz dans l\'épisode.</div></td></tr></table></td></tr>')
    plats = "".join(
        f'<td style="padding:0 6px"><img src="images/plateforme_{n}.png" width="44" height="44" alt="{n.capitalize()}" '
        f'style="display:block;border:0;width:44px;height:44px"></td>' for n in ("youtube", "spotify", "ausha"))

    page = f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light"><title>{esc(mail["subject"])}</title></head>
<body style="margin:0;padding:0;background:#FFFFFF">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{esc(mail["preheader"])}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#FFFFFF"><tr><td align="center" style="padding:0 20px">
<table role="presentation" width="680" cellpadding="0" cellspacing="0" style="width:100%;max-width:680px">

<tr><td style="padding:26px 0 22px 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td><img src="images/logo.png" height="26" alt="AI Partners" style="display:block;border:0;height:26px;width:auto"></td>
<td align="right" style="font-family:{FONT};font-size:13px;font-weight:bold;letter-spacing:.14em;color:{BLUE}">AI CORNER · {esc(mail["episode"])}</td>
</tr></table></td></tr>

<tr><td style="font-family:{FONT};font-size:14px;font-weight:bold;letter-spacing:.14em;color:{BLUE};padding:14px 0 14px 0;border-top:1px solid {RULE}">PODCAST</td></tr>
<tr><td><h1 style="font-family:{FONT};font-size:38px;line-height:1.14;font-weight:bold;color:{NAVY};margin:0 0 20px 0">{esc(h1)}</h1></td></tr>
<tr><td style="font-family:{FONT};font-size:19px;line-height:1.55;color:{MUTED};padding-bottom:26px">{esc(mail["intro_court"])}</td></tr>

<tr><td style="padding-bottom:26px"><table role="presentation" cellpadding="0" cellspacing="0"><tr>
<td valign="middle" style="padding-right:14px"><img src="images/thomas_rond.jpg" width="46" height="46" alt="Thomas Spitz" style="display:block;border:0;border-radius:23px;width:46px;height:46px"></td>
<td valign="middle" style="font-family:{FONT};font-size:15px;line-height:1.45;color:{MUTED}"><strong style="color:{NAVY}">Thomas Spitz</strong>, CEO d'AI Partners<br>{quand} · {duree} d'écoute</td>
</tr></table></td></tr>

<tr><td style="padding-bottom:34px"><a href="{esc(url)}"><img src="images/episode_youtube.jpg" width="680" alt="{esc(h1)}" style="display:block;width:100%;max-width:680px;border:0;border-radius:14px"></a></td></tr>

<tr><td style="font-family:{FONT};font-size:22px;line-height:1.45;font-weight:bold;color:{NAVY};padding-bottom:22px">{esc(mail["hook"].split(" Vos équipes")[0])}</td></tr>
<tr><td>{intro}</td></tr>
<tr><td height="12" style="font-size:0;line-height:0">&nbsp;</td></tr>
{stat_html}
<tr><td style="font-family:{FONT};font-size:14px;font-weight:bold;letter-spacing:.14em;color:{BLUE};padding-bottom:18px">AU PROGRAMME DE CET ÉPISODE</td></tr>
{sections}

<tr><td style="padding:10px 0 34px 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td bgcolor="{NAVY}" style="background-color:{NAVY};border-radius:16px;padding:30px 30px 32px 30px">
<div style="font-family:{FONT};font-size:46px;line-height:.7;font-weight:bold;color:{BLUE}">&ldquo;</div>
<div style="font-family:{FONT};font-size:21px;line-height:1.5;font-weight:bold;color:#FFFFFF;padding-top:10px">{esc(mail["closing_court"])}</div>
<div style="font-family:{FONT};font-size:14px;line-height:1.4;color:#B9C6F2;padding-top:14px">Thomas Spitz, à propos de la conversation avec Nicolas Comestaz</div>
</td></tr></table></td></tr>

<tr><td style="font-family:{FONT};font-size:17px;line-height:1.65;color:{INK};padding-bottom:6px">{esc(mail["closing"])}</td></tr>
<tr><td align="center" style="padding:14px 0 6px 0">{pill_open(NAVY, "0 auto")}
<a href="{esc(url)}" style="display:inline-block;padding:16px 38px;font-family:{FONT};font-size:16px;font-weight:bold;letter-spacing:.04em;color:#FFFFFF;text-decoration:none">REGARDER L'ÉPISODE</a>
{PILL_CLOSE}</td></tr>

<tr><td style="padding:34px 0 0 0;border-top:1px solid {RULE}"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="{SOFT}" style="background-color:{SOFT};border-radius:16px"><tr><td align="center" style="padding:28px 24px">
<div style="font-family:{FONT};font-size:21px;line-height:1.3;font-weight:bold;color:{NAVY}">Vos équipes testent l'IA. Et après ?</div>
<div style="font-family:{FONT};font-size:16px;line-height:1.5;color:{MUTED};padding:8px 0 4px 0">Passons de l'expérimentation à l'impact : 30 minutes avec moi pour en parler.</div>
<a href="https://calendly.com/" style="font-family:{FONT};font-size:16px;font-weight:bold;color:{BLUE};text-decoration:underline">Réserver un échange avec Thomas</a>
</td></tr></table></td></tr>

<tr><td align="center" style="padding:34px 0 10px 0;font-family:{FONT};font-size:14px;color:{MUTED}">Écoutez AI Corner partout</td></tr>
<tr><td align="center" style="padding-bottom:30px"><table role="presentation" cellpadding="0" cellspacing="0"><tr>{plats}</tr></table></td></tr>
</table></td></tr></table></body></html>"""
    (out / "email.html").write_text(page, encoding="utf-8")
    return out


def preview(out: Path) -> Path:
    """Aperçu PNG (Chrome) : la page est écrite DANS le dossier pour que les images relatives se chargent."""
    import subprocess
    import tempfile

    from ..thumbnail import _browser
    png = out / "apercu.png"
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        subprocess.run([_browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                        f"--user-data-dir={Path(td) / 'prof'}", "--virtual-time-budget=4000", "--force-device-scale-factor=1",
                        "--window-size=760,3050", f"--screenshot={png}", (out / "email.html").as_uri()],
                       capture_output=True, timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return png


if __name__ == "__main__":
    ep = sys.argv[sys.argv.index("--episode") + 1] if "--episode" in sys.argv else "E23"
    o = build(ep)
    print(preview(o))
