"""Piste « Nostra » v2 du labo newsletter (10/11/2026), après la critique Impeccable (relecteur indépendant, 15/24, « Acceptable »).

Décisions prises sur ses 5 problèmes (3 P1, 2 P2) :
- P1 hiérarchie du haut : UN seul titre fort = la question d'accroche (un dirigeant qui ne connaît pas l'invité lit d'abord la promesse) ;
  l'invité passe en ligne de légende. Un seul mot du titre en bleu primaire (charte), plus de ponctuation colorée.
- P1 miniature : elle monte juste sous le titre, avec le bouton « Regarder l'épisode » collé dessous (un seul grand appel, en haut).
- P1 titrage centré : tout est aligné à gauche sur un seul axe (charte : paragraphes jamais centrés). Seul le bandeau d'image reste plein cadre.
- P2 trois fins : le mot de Thomas devient la fin (photo, texte plus grand, signature), suivi d'UN bloc de réservation bleu nuit puis d'une
  ligne de plateformes ; « Rejoignez l'aventure » et le pied en encart sont supprimés.
- P2 logos : trois pastilles identiques (fond blanc, trait bleu nuit, logo bleu nuit), plus de rouge ni de vert (charte).
- Arthur (10/11/2026) : plus aucun aplat bleu très clair (#F1F6FD / #EEF3FB), le bleu clair n'est plus utilisé.
Non retenu : copier le texte posé sans grille des cabinets de conseil (idée du relecteur) : Arthur a demandé la construction d'On Train.

EXPLORATION : non branchée sur `python -m clipper newsletter`. Sortie : travail/newsletter_lab/nostra_v2/.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from ..newsletter_templates import BLUE, FONT, NAVY, PILL_CLOSE, esc, pill_open

ROOT = Path(__file__).resolve().parents[2]
INK, MUTED, RULE = "#1B2559", "#4A5683", "#DDE3F2"


def _tr(episode: str) -> Path:
    return next((ROOT / "EPISODES" / "ai-corner").glob(f"{episode}_*")) / "travail"


def platform_pills(out: Path) -> None:
    """Trois pastilles identiques : fond blanc, trait bleu nuit, logo bleu nuit (la charte exclut le rouge et le vert)."""
    from ..config import Brand
    from ..newsletter import _shot, _uri
    from ..newsletter_templates import _glyph
    brand = Brand("ai-corner")
    for key in ("youtube", "spotify", "ausha"):
        page = (f"<html><body style='margin:0;background:#fff'><div style='width:240px;height:240px;display:flex;align-items:center;"
                f"justify-content:center'><div style='width:204px;height:204px;border-radius:56px;background:#fff;box-sizing:border-box;"
                f"border:7px solid {NAVY};display:flex;align-items:center;justify-content:center'><div style='width:108px;height:108px'>"
                f"{_glyph(brand, key, NAVY, _uri)}</div></div></div><style>svg *{{fill:{NAVY} !important}}</style></body></html>")
        _shot(page, 240, 240, out / "images" / f"pastille_{key}.png")


def build(episode: str = "E23") -> Path:
    tr = _tr(episode)
    src = tr / "newsletter"
    mail = json.loads((src / "contenu.json").read_text(encoding="utf-8"))
    out = tr / "newsletter_lab" / "nostra_v2"
    (out / "images").mkdir(parents=True, exist_ok=True)
    for n in ["entete.png", "episode_youtube.jpg", "thomas_rond.jpg", "bouton_play.png"]:
        shutil.copy2(src / "images" / n, out / "images" / n)
    platform_pills(out)

    url = mail["youtube_url"] or "{{lien_youtube}}"
    body = f"font-family:{FONT};color:{INK};font-size:16px;line-height:1.65;text-wrap:pretty"

    def btn(label: str, href: str, bg: str = NAVY, play: bool = False) -> str:
        ico = (f'<td valign="middle" width="24" style="padding:0 28px 0 0;line-height:0;font-size:0"><a href="{esc(href)}"><img src="images/bouton_play.png" '
               f'width="22" height="22" alt="" style="display:block;border:0;width:22px;height:22px"></a></td>') if play else ""
        pad = "16px 12px 16px 34px" if play else "16px 34px"
        return (pill_open(bg, "0") + '<table role="presentation" cellpadding="0" cellspacing="0"><tr>'
                f'<td valign="middle" style="padding:{pad};line-height:1"><a href="{esc(href)}" style="font-family:{FONT};font-size:16px;'
                f'font-weight:bold;letter-spacing:.03em;color:#FFFFFF;text-decoration:none">{esc(label)}</a></td>{ico}</tr></table>' + PILL_CLOSE)

    question = mail["hook"].split(" Vos équipes")[0]
    q = esc(question).replace("à l&#x27;impact", f'à <span style="color:{BLUE}">l&#x27;impact</span>')
    legende = f'Avec {esc(mail["guest"])}, {esc(mail["role"])}'
    paras = "".join(f'<p style="{body};margin:0 0 14px 0">{esc(x)}</p>' for x in mail["intro"].split("\n") if x.strip())
    bullets = "".join(
        f'<tr><td valign="top" style="{body};padding:0 12px 14px 0;color:{BLUE};font-size:20px;line-height:1.3">&bull;</td>'
        f'<td style="{body};padding:0 0 14px 0"><strong style="color:{NAVY}">{esc(p["title"])} :</strong> {esc(p["text"])}</td></tr>'
        for p in mail["program"])
    plats = "".join(
        f'<td style="padding:0 10px 0 0"><img src="images/pastille_{n}.png" width="52" height="52" alt="{n.capitalize()}" '
        f'style="display:block;border:0;width:52px;height:52px"></td>' for n in ("youtube", "spotify", "ausha"))

    page = f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light"><title>{esc(mail["subject"])}</title></head>
<body style="margin:0;padding:0;background:#FFFFFF">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{esc(mail["preheader"])}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#FFFFFF"><tr><td align="center" style="padding:0 16px">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="width:100%;max-width:640px;text-align:left">

<tr><td style="padding:18px 0 0 0"><img src="images/entete.png" width="640" alt="AI Corner by AI Partners · {esc(mail["episode"])}" style="display:block;width:100%;max-width:640px;border:0;border-radius:14px"></td></tr>

<tr><td style="padding:34px 0 12px 0"><h1 style="font-family:{FONT};font-size:30px;line-height:1.2;font-weight:bold;letter-spacing:-.015em;color:{NAVY};margin:0;text-wrap:balance">{q}</h1></td></tr>
<tr><td style="font-family:{FONT};font-size:16px;line-height:1.5;color:{MUTED};padding:0 0 24px 0">{legende}</td></tr>

<tr><td style="padding:0 0 20px 0"><a href="{esc(url)}"><img src="images/episode_youtube.jpg" width="640" alt="Regarder l'épisode : {esc(mail["guest"])} ({esc(mail["company"])}), comment déployer l'IA à grande échelle" style="display:block;width:100%;max-width:640px;border:0;border-radius:14px"></a></td></tr>
<tr><td style="padding:0 0 38px 0">{btn("Regarder l'épisode", url, play=True)}</td></tr>

<tr><td>{paras}</td></tr>

<tr><td style="padding:30px 0 16px 0;border-top:1px solid {RULE}"><h2 style="font-family:{FONT};font-size:24px;line-height:1.25;font-weight:bold;letter-spacing:-.01em;color:{NAVY};margin:0;text-wrap:balance">Au programme de cet épisode</h2></td></tr>
<tr><td><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{bullets}</table></td></tr>

<tr><td style="padding:26px 0 0 0;border-top:1px solid {RULE}"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td valign="top" width="64" style="width:64px;padding:0 16px 0 0"><img src="images/thomas_rond.jpg" width="56" height="56" alt="Thomas Spitz" style="display:block;border:0;border-radius:28px;width:56px;height:56px"></td>
<td valign="top" style="{body};font-size:18px;line-height:1.6">{esc(mail["closing"])}<br>
<strong style="color:{NAVY}">Thomas Spitz</strong><span style="color:{MUTED}">, CEO et fondateur d'AI Partners</span></td>
</tr></table></td></tr>

<tr><td height="30" style="font-size:0;line-height:0">&nbsp;</td></tr>
<tr><td bgcolor="{NAVY}" style="background-color:{NAVY};border-radius:16px;padding:32px 30px 34px 30px">
<div style="font-family:{FONT};font-size:25px;line-height:1.25;font-weight:bold;letter-spacing:-.01em;color:#FFFFFF;padding-bottom:10px;text-wrap:balance">Vos équipes testent l'IA. Et après ?</div>
<div style="font-family:{FONT};font-size:16px;line-height:1.6;color:#D3DBF5;padding-bottom:22px">Passons de l'expérimentation à l'impact : 30 minutes avec moi pour en parler.</div>
{btn("Réserver un échange avec Thomas", "https://calendly.com/", bg=BLUE)}
</td></tr>

<tr><td style="padding:30px 0 12px 0;font-family:{FONT};font-size:16px;line-height:1.5;color:{MUTED}">Écoutez AI Corner sur votre plateforme préférée</td></tr>
<tr><td style="padding:0 0 26px 0"><table role="presentation" cellpadding="0" cellspacing="0"><tr>{plats}</tr></table></td></tr>
<tr><td height="24" style="font-size:0;line-height:0">&nbsp;</td></tr>
</table></td></tr></table></body></html>"""
    (out / "email.html").write_text(page, encoding="utf-8")
    return out


def preview(out: Path, height: int = 2300) -> Path:
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
