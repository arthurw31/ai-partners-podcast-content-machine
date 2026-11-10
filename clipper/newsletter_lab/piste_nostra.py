"""Piste « Nostra » du labo newsletter (10/11/2026) : même construction que le mail « Nostra #3 » d'On Train (Mailjet), en couleurs AI Partners.

Structure copiée du mail de référence (relevée le 10/11/2026) : bandeau d'en-tête, bloc titre (invité en gras + thème), question d'accroche,
présentation avec la PHOTO de l'invité à côté du texte, bouton foncé, « Au programme de cet épisode. » (point final de couleur), puces avec
début en gras, « Retrouvez l'épisode complet sur YouTube », grande miniature, bouton, titre centré « Rejoignez l'aventure… ! » (ponctuation
de couleur), rangée de logos des plateformes, bouton « Un avis ? », pied gris-bleu clair.

EXPLORATION : non branchée sur `python -m clipper newsletter`. Sortie : travail/newsletter_lab/nostra/.
Lancer : python -m clipper.newsletter_lab.piste_nostra [--episode E23]
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from ..newsletter_templates import BLUE, FONT, NAVY, PILL_CLOSE, esc, pill_open

ROOT = Path(__file__).resolve().parents[2]
INK, SOFT = "#1B2559", "#EEF3FB"


def _tr(episode: str) -> Path:
    return next((ROOT / "EPISODES" / "ai-corner").glob(f"{episode}_*")) / "travail"


def build(episode: str = "E23") -> Path:
    tr = _tr(episode)
    src = tr / "newsletter"
    mail = json.loads((src / "contenu.json").read_text(encoding="utf-8"))
    out = tr / "newsletter_lab" / "nostra"
    (out / "images").mkdir(parents=True, exist_ok=True)
    for n in ["entete.png", "invite.jpg", "episode_youtube.jpg", "plateforme_youtube.png", "plateforme_spotify.png",
              "plateforme_ausha.png", "bouton_play.png"]:
        shutil.copy2(src / "images" / n, out / "images" / n)

    url = mail["youtube_url"] or "{{lien_youtube}}"
    cell = f"font-family:{FONT};color:{INK};font-size:16px;line-height:1.6"
    pt = lambda x: f'<span style="color:{BLUE}">{x}</span>'                       # noqa: E731  point final coloré (comme le point jaune d'On Train)

    def btn(label: str, href: str, play: bool = False) -> str:
        ico = (f'<td valign="middle" width="24" style="padding:0 28px 0 0;line-height:0;font-size:0"><a href="{esc(href)}"><img src="images/bouton_play.png" '
               f'width="22" height="22" alt="" style="display:block;border:0;width:22px;height:22px"></a></td>') if play else ""
        pad = "16px 12px 16px 34px" if play else "16px 34px"
        return (pill_open(NAVY, "0 auto") + '<table role="presentation" cellpadding="0" cellspacing="0"><tr>'
                f'<td valign="middle" style="padding:{pad};line-height:1"><a href="{esc(href)}" style="font-family:{FONT};font-size:16px;'
                f'font-weight:bold;letter-spacing:.03em;color:#FFFFFF;text-decoration:none">{esc(label)}</a></td>{ico}</tr></table>' + PILL_CLOSE)

    bullets = "".join(
        f'<tr><td valign="top" style="{cell};padding:0 10px 12px 0;color:{BLUE};font-size:20px;line-height:1.35">&bull;</td>'
        f'<td style="{cell};padding:0 0 12px 0"><strong style="color:{NAVY}">{esc(p["title"])} :</strong> {esc(p["text"])}</td></tr>'
        for p in mail["program"])
    paras = [x for x in mail["intro"].split("\n") if x.strip()]
    first = esc(paras[0])
    rest = "".join(f'<p style="{cell};margin:0 0 14px 0">{esc(x)}</p>' for x in paras[1:])
    plats = "".join(
        f'<td style="padding:0 7px"><img src="images/plateforme_{n}.png" width="52" height="52" alt="{n.capitalize()}" '
        f'style="display:block;border:0;width:52px;height:52px"></td>' for n in ("youtube", "spotify", "ausha"))
    hook = mail["hook"].split(" Vos équipes")[0]

    page = f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light"><title>{esc(mail["subject"])}</title></head>
<body style="margin:0;padding:0;background:#FFFFFF">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{esc(mail["preheader"])}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#FFFFFF"><tr><td align="center" style="padding:0 16px">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="width:100%;max-width:640px">

<tr><td style="padding:18px 0 0 0"><img src="images/entete.png" width="640" alt="AI Corner by AI Partners · {esc(mail["episode"])}" style="display:block;width:100%;max-width:640px;border:0;border-radius:14px"></td></tr>

<tr><td align="center" style="padding:34px 12px 8px 12px;font-family:{FONT};font-size:25px;line-height:1.3;font-weight:bold;color:{NAVY}">{esc(mail["guest"])} ({esc(mail["company"])})</td></tr>
<tr><td align="center" style="padding:0 12px 26px 12px;font-family:{FONT};font-size:20px;line-height:1.35;color:{BLUE};font-weight:bold">{esc(mail["theme"])}{pt(".")}</td></tr>

<tr><td style="{cell};padding:0 0 22px 0;font-weight:bold;color:{NAVY};font-size:18px;line-height:1.5">{esc(hook)}</td></tr>

<tr><td style="padding:0 0 8px 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td valign="top" style="padding:0 20px 0 0"><p style="{cell};margin:0 0 14px 0">{first}</p>{rest}</td>
<td valign="top" width="170" style="width:170px"><img src="images/invite.jpg" width="170" alt="{esc(mail["guest"])}" style="display:block;width:170px;height:auto;border:0;border-radius:14px"></td>
</tr></table></td></tr>

<tr><td align="center" style="padding:14px 0 30px 0">{btn("Regarder l'épisode", url, play=True)}</td></tr>

<tr><td align="center" style="padding:6px 0 18px 0;font-family:{FONT};font-size:25px;line-height:1.3;font-weight:bold;color:{NAVY}">Au programme de cet épisode{pt(".")}</td></tr>
<tr><td><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{bullets}</table></td></tr>

<tr><td style="{cell};padding:10px 0 12px 0">Retrouvez l'épisode complet sur YouTube</td></tr>
<tr><td style="padding:0 0 22px 0"><a href="{esc(url)}"><img src="images/episode_youtube.jpg" width="640" alt="{esc(mail["guest"])} : l'épisode complet" style="display:block;width:100%;max-width:640px;border:0;border-radius:14px"></a></td></tr>

<tr><td style="{cell};padding:0 0 26px 0">{esc(mail["closing"])}</td></tr>

<tr><td bgcolor="{SOFT}" align="center" style="background-color:{SOFT};border-radius:16px;padding:30px 26px 32px 26px">
<div style="font-family:{FONT};font-size:25px;line-height:1.3;font-weight:bold;color:{NAVY};padding-bottom:12px">Vos équipes testent l'IA. Et après{pt("&nbsp;?")}</div>
<div style="{cell};padding-bottom:20px">Passons de l'expérimentation à l'impact : 30 minutes avec moi pour en parler.</div>
{btn("Réserver un échange avec Thomas", "https://calendly.com/")}
</td></tr>

<tr><td align="center" style="padding:34px 0 8px 0;font-family:{FONT};font-size:25px;line-height:1.3;font-weight:bold;color:{NAVY}">Rejoignez l'aventure AI Corner{pt("&nbsp;!")}</td></tr>
<tr><td align="center" style="{cell};padding:0 10px 20px 10px">Ce podcast s'adresse aux dirigeants et aux équipes qui déploient l'IA dans leur entreprise.<br>Pour ne manquer aucun épisode, retrouvez-nous sur votre plateforme préférée.</td></tr>
<tr><td align="center" style="padding:0 0 26px 0"><table role="presentation" cellpadding="0" cellspacing="0"><tr>{plats}</tr></table></td></tr>

<tr><td bgcolor="{SOFT}" align="center" style="background-color:{SOFT};border-radius:16px;padding:26px 20px">
<div style="font-family:{FONT};font-size:18px;font-weight:bold;color:{NAVY}">AI Partners</div>
<div style="font-family:{FONT};font-size:13px;line-height:1.5;color:#55618F;padding-top:6px">AI Corner, le podcast d'AI Partners<br>Se désinscrire (pied de page standard HubSpot)</div>
</td></tr>
<tr><td height="28" style="font-size:0;line-height:0">&nbsp;</td></tr>
</table></td></tr></table></body></html>"""
    (out / "email.html").write_text(page, encoding="utf-8")
    return out


def preview(out: Path, height: int = 2400) -> Path:
    import subprocess
    import tempfile

    from ..thumbnail import _browser
    png = out / "apercu.png"
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        subprocess.run([_browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                        f"--user-data-dir={Path(td) / 'prof'}", "--virtual-time-budget=4000", "--force-device-scale-factor=1",
                        f"--window-size=700,{height}", f"--screenshot={png}", (out / "email.html").as_uri()],
                       capture_output=True, timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return png


if __name__ == "__main__":
    ep = sys.argv[sys.argv.index("--episode") + 1] if "--episode" in sys.argv else "E23"
    print(preview(build(ep)))
