"""Trois concepts « wahou » du labo newsletter (10/11/2026). Palette imposée par Arthur : NOIR, BLEU FONCÉ, BLANC (plus de bleu vif).

Nouvelles images faites à partir des vraies caméras du tournage (images extraites des rushs, traitées en BICHROMIE noir -> bleu nuit -> blanc,
grain fin) :
- « verbatim » : mail noir ouvert sur UNE phrase exacte de l'invité (transcription, source 315,3 s = 4:09 dans l'épisode monté) ; portrait en
  bichromie, mots en contour puis le mot fort en plein ; une onde sonore ANIMÉE (GIF, la première image suffit dans Outlook) ; moments à
  écouter avec lien YouTube horodaté.
- « cinema » : une série de plans de cinéma plein cadre, un par moment fort (images des rushs aux instants des chapitres), horodatage géant,
  chaque plan est un lien qui ouvre YouTube à cet instant.
- « face_a_face » : Thomas et Nicolas face à face en bichromie, un point d'interrogation géant en contour entre eux, la question en dessous.

Source -> instant dans l'épisode monté : montage = source - 65,8 s avant les coupes (chapitres de episode_plan.json : 637,8 s source = 9:32).
EXPLORATION : non branchée sur la production. Sortie : travail/newsletter_lab/wahou/<concept>/.
Lancer : python -m clipper.newsletter_lab.piste_wahou
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from ..newsletter_templates import FONT, NAVY, PILL_CLOSE, esc, pill_open
from .piste_nouveau import _fonts, _render, _tr, _uri, preview

BLACK = "#05070F"
WHITE = "#FFFFFF"
SOFT = "#B8C1E0"          # blanc atténué pour le texte secondaire sur noir (teinte du bleu nuit)
LINE = "#1D2550"
OFFSET = 65.8             # source -> montage (avant les coupes)


def _mmss(s: float) -> str:
    return f"{int(s) // 60}:{int(s) % 60:02d}"


def _frame(cam: Path, t: float, out: Path) -> Path:
    if not out.exists():
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(cam), "-frames:v", "1", "-q:v", "2", str(out)],
                       check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return out


def duotone(src: Path, out: Path, crop: tuple | None = None, size: tuple | None = None, grain: float = 7.0) -> Path:
    """Noir -> bleu nuit -> blanc, contraste étiré, grain fin. Conserve la transparence d'un PNG détouré."""
    import numpy as np
    from PIL import Image, ImageOps
    im = Image.open(src)
    alpha = im.getchannel("A") if im.mode == "RGBA" else None
    im = im.convert("RGB")
    if crop:
        im = im.crop(crop)
    if size:
        im = im.resize(size, Image.Resampling.LANCZOS)
        alpha = alpha.resize(size) if alpha is not None else None
    g = ImageOps.autocontrast(ImageOps.grayscale(im), cutoff=1)
    d = ImageOps.colorize(g, black=(5, 7, 15), mid=(40, 56, 140), white=(255, 255, 255), midpoint=120)
    if grain:
        a = np.asarray(d).astype("float32")
        a += np.random.default_rng(7).normal(0, grain, a.shape[:2])[..., None]
        d = Image.fromarray(np.clip(a, 0, 255).astype("uint8"))
    if alpha is not None:
        d = d.convert("RGBA")
        d.putalpha(alpha)
    d.save(out)
    return out


def waveform_gif(out: Path, frames: int = 10) -> None:
    """Onde sonore animée (barres blanches sur noir), 640 x 90 affiché, tournée en boucle ; sobre pour rester léger."""
    import math
    from PIL import Image, ImageDraw
    W, H, n = 1280, 180, 64
    ims = []
    for f in range(frames):
        im = Image.new("RGB", (W, H), (5, 7, 15))
        d = ImageDraw.Draw(im)
        for i in range(n):
            env = math.sin(math.pi * i / (n - 1)) ** 0.8
            h = 14 + 150 * env * abs(math.sin(i * 0.55 + f * 0.63) * math.cos(i * 0.21 - f * 0.4))
            x = 20 + i * (W - 40) / n
            d.rounded_rectangle([x, H / 2 - h / 2, x + 10, H / 2 + h / 2], 5, fill=(255, 255, 255) if h > 40 else (110, 122, 190))
        ims.append(im.quantize(colors=32))
    ims[0].save(out, save_all=True, append_images=ims[1:], duration=110, loop=0, optimize=True)


def _btn(label: str, href: str, bg: str, fg: str) -> str:
    return (pill_open(bg, "0") + f'<a href="{esc(href)}" style="display:inline-block;padding:16px 34px;font-family:{FONT};font-size:16px;'
            f'font-weight:bold;letter-spacing:.03em;color:{fg};text-decoration:none">{esc(label)}</a>' + PILL_CLOSE)


def _shell(mail: dict, bg: str, inner: str) -> str:
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark"><title>{esc(mail["subject"])}</title></head>
<body style="margin:0;padding:0;background:{bg}">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{esc(mail["preheader"])}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="{bg}"><tr><td align="center" style="padding:0">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" bgcolor="{bg}" style="width:100%;max-width:640px;text-align:left">
{inner}
</table></td></tr></table></body></html>"""


def _thomas_close(mail: dict, base: Path) -> str:
    return (f'<tr><td style="padding:34px 28px 0 28px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid {LINE}"><tr>'
            f'<td valign="top" width="64" style="width:64px;padding:28px 16px 0 0"><img src="images/thomas_rond.jpg" width="56" height="56" alt="Thomas Spitz" style="display:block;border:0;border-radius:28px;width:56px;height:56px"></td>'
            f'<td valign="top" style="padding-top:28px;font-family:{FONT};font-size:18px;line-height:1.6;color:#E6EBFB">{esc(mail["closing"])}<br>'
            f'<strong style="color:{WHITE}">Thomas Spitz</strong><span style="color:{SOFT}">, CEO et fondateur d\'AI Partners</span></td></tr></table></td></tr>'
            f'<tr><td style="padding:34px 28px 8px 28px;font-family:{FONT};font-size:24px;line-height:1.25;font-weight:bold;color:{WHITE}">Vos équipes testent l\'IA. Et après ?</td></tr>'
            f'<tr><td style="padding:0 28px 18px 28px;font-family:{FONT};font-size:16px;line-height:1.6;color:{SOFT}">Passons de l\'expérimentation à l\'impact : 30 minutes avec moi pour en parler.</td></tr>'
            f'<tr><td style="padding:0 28px 54px 28px">{_btn("Réserver un échange avec Thomas", "https://calendly.com/", WHITE, NAVY)}</td></tr>')


def build(episode: str = "E23") -> list[Path]:
    tr = _tr(episode)
    mail = json.loads((tr / "newsletter" / "contenu.json").read_text(encoding="utf-8"))
    yt = mail["youtube_url"]
    base_yt = yt.split("?")[0]
    root = tr / "newsletter_lab" / "wahou"
    cams = tr.parent / "rushs" / "cameras"
    work = root / "_images"
    work.mkdir(parents=True, exist_ok=True)
    outs = []
    plan = json.loads((tr / "episode_plan.json").read_text(encoding="utf-8"))
    src_t = {c["title"]: c["t"] for c in plan["chapters"]}
    moments = [("Le programme SuperCharge AI", mail["program"][0]), ("Pourquoi Microsoft Copilot", mail["program"][1]),
               ("Structurer l'organisation Data & AI (Hub & Spoke)", mail["program"][2]), ("Gouvernance et AI Board", mail["program"][3])]
    # --- images des rushs (caméra de Nicolas aux instants des chapitres, +6 s dans la réponse) puis bichromie
    stills = []
    for title, p in moments:
        t = src_t[title] + 6
        f = _frame(cams / "cam1_nicolas.mp4", t, work / f"nicolas_{int(t)}.jpg")
        stills.append((p, duotone(f, work / f"duo_{int(t)}.png", crop=(0, 120, 1920, 1000), size=(1280, 587)), p["chapter"]))
    # --- portraits détourés en bichromie
    guest = duotone(tr / "carrousel" / "assets" / "guest.png", work / "guest_duo.png", grain=5)
    host = duotone(tr / "carrousel" / "assets" / "host.png", work / "host_duo.png", grain=5)
    mont = _uri(Path(__file__).resolve().parents[2] / "MARQUES" / "ai-corner" / "assets" / "outro_bg.png")
    import shutil
    thumb = tr / "newsletter" / "images" / "thomas_rond.jpg"

    def mk(name: str) -> Path:
        d = root / name
        (d / "images").mkdir(parents=True, exist_ok=True)
        shutil.copy2(thumb, d / "images" / "thomas_rond.jpg")
        return d

    question = mail["hook"].split(" Vos équipes")[0]
    paras = "".join(f'<p style="margin:0 0 14px 0">{esc(x)}</p>' for x in mail["intro"].split("\n") if x.strip())

    # ============ 1. VERBATIM
    d = mk("verbatim")
    waveform_gif(d / "images" / "onde.gif")
    hero = (f"<html><head><style>{_fonts()}body{{margin:0}}</style></head><body><div style=\"position:relative;width:1280px;height:1400px;"
            f"background:{BLACK};overflow:hidden;font-family:M\">"
            f"<img src='{mont}' style='position:absolute;right:-300px;top:-60px;width:1500px;mix-blend-mode:screen;opacity:.8'>"
            f"<img src='{_uri(guest)}' style='position:absolute;right:-300px;bottom:0;height:1040px'>"
            f"<div style='position:absolute;left:0;right:0;bottom:0;height:260px;background:linear-gradient(to bottom,rgba(5,7,15,0),{BLACK})'></div>"
            f"<div style='position:absolute;left:72px;top:70px;color:{WHITE};font-weight:800;font-size:44px;letter-spacing:.02em'>AI Corner"
            f"<span style='margin-left:22px;border:3px solid {WHITE};border-radius:999px;padding:6px 24px;font-size:28px;letter-spacing:.08em'>ÉPISODE 23</span></div>"
            f"<div style='position:absolute;left:72px;top:300px;width:780px;font-weight:800;font-size:140px;line-height:1.03;letter-spacing:-.03em;color:{WHITE}'>"
            f"<span style='color:transparent;-webkit-text-stroke:3px {WHITE}'>«&nbsp;C'est un</span><br>marché de vendeurs.</div></div></body></html>")
    _render(hero, 1280, 1400, d / "images" / "hero.png")
    t_quote = int(315.3 - OFFSET)
    rows = ""
    for p in [m[1] for m in moments]:
        s = int(src_t[[k for k, v in zip(src_t, src_t.values())][0]] * 0)  # placeholder (non utilisé)
    for (title, p), (_, _, ch) in zip(moments, stills):
        m, sec = ch.split(":")
        href = f"{base_yt}?t={int(m) * 60 + int(sec)}"
        rows += (f'<tr><td style="padding:22px 0;border-top:1px solid {LINE}"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
                 f'<td valign="top" width="96" style="width:96px;padding:2px 16px 0 0"><a href="{esc(href)}" style="display:inline-block;border:2px solid {WHITE};'
                 f'border-radius:999px;padding:5px 13px;font-family:{FONT};font-size:15px;font-weight:bold;color:{WHITE};text-decoration:none">&#9654; {esc(ch)}</a></td>'
                 f'<td valign="top" style="font-family:{FONT};font-size:16px;line-height:1.6;color:{SOFT}"><a href="{esc(href)}" style="color:{WHITE};font-size:20px;'
                 f'font-weight:bold;line-height:1.3;text-decoration:none">{esc(p["title"])}</a><br>{esc(p["text"])}</td></tr></table></td></tr>')
    inner = (f'<tr><td><a href="{esc(base_yt)}?t={t_quote}"><img src="images/hero.png" width="640" alt="« C\'est un marché de vendeurs. » Nicolas Comestaz, VP Global Data &amp; AI Center of Excellence chez Coty, invité d\'AI Corner, épisode 23" style="display:block;width:100%;max-width:640px;height:auto;border:0"></a></td></tr>'
             f'<tr><td><img src="images/onde.gif" width="640" alt="" style="display:block;width:100%;max-width:640px;height:auto;border:0"></td></tr>'
             f'<tr><td style="padding:10px 28px 26px 28px;font-family:{FONT};font-size:16px;line-height:1.5;color:{SOFT}"><strong style="color:{WHITE};font-size:18px">Nicolas Comestaz</strong><br>VP Global Data &amp; AI Center of Excellence, Coty · <a href="{esc(base_yt)}?t={t_quote}" style="color:{WHITE}">&#9654; écouter cette phrase ({_mmss(t_quote)})</a></td></tr>'
             f'<tr><td style="padding:0 28px 6px 28px;font-family:{FONT};font-size:20px;line-height:1.5;font-weight:bold;color:{WHITE}">{esc(question)}</td></tr>'
             f'<tr><td style="padding:14px 28px 8px 28px">{_btn("Regarder l\'épisode", yt, WHITE, NAVY)}</td></tr>'
             f'<tr><td style="padding:36px 28px 6px 28px;font-family:{FONT};font-size:14px;font-weight:bold;letter-spacing:.14em;color:{SOFT}">4 MOMENTS À ÉCOUTER</td></tr>'
             f'<tr><td style="padding:0 28px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}</table></td></tr>'
             + _thomas_close(mail, d))
    (d / "email.html").write_text(_shell(mail, BLACK, inner), encoding="utf-8")
    outs.append(d)

    # ============ 2. CINÉMA
    d = mk("cinema")
    cine = ""
    for i, ((title, p), (_, duo, ch)) in enumerate(zip(moments, stills)):
        m, sec = ch.split(":")
        href = f"{base_yt}?t={int(m) * 60 + int(sec)}"
        page = (f"<html><head><style>{_fonts()}body{{margin:0}}</style></head><body><div style=\"position:relative;width:1280px;height:640px;background:{BLACK};"
                f"overflow:hidden;font-family:M\"><img src='{_uri(duo)}' style='position:absolute;left:0;top:0;width:1280px'>"
                f"<div style='position:absolute;inset:0;background:linear-gradient(to top,rgba(5,7,15,.92) 0%,rgba(5,7,15,0) 55%)'></div>"
                f"<div style='position:absolute;left:50px;bottom:34px;color:{WHITE};font-weight:800;font-size:230px;line-height:.9;letter-spacing:-.04em'>{ch}</div>"
                f"<div style='position:absolute;right:50px;bottom:56px;width:128px;height:128px;border-radius:64px;border:5px solid {WHITE};display:flex;align-items:center;justify-content:center'>"
                f"<div style='width:0;height:0;border-left:44px solid {WHITE};border-top:28px solid transparent;border-bottom:28px solid transparent;margin-left:12px'></div></div></div></body></html>")
        _render(page, 1280, 640, d / "images" / f"plan_{i + 1}.png")
        cine += (f'<tr><td style="padding:0 0 0 0"><a href="{esc(href)}"><img src="images/plan_{i + 1}.png" width="640" alt="Écouter à {esc(ch)} : {esc(p["title"])}" style="display:block;width:100%;max-width:640px;height:auto;border:0"></a></td></tr>'
                 f'<tr><td style="padding:18px 28px 40px 28px;font-family:{FONT};font-size:16px;line-height:1.6;color:{SOFT}"><a href="{esc(href)}" style="color:{WHITE};font-size:22px;font-weight:bold;line-height:1.3;text-decoration:none">{esc(p["title"])}</a><br>{esc(p["text"])}</td></tr>')
    title_img = (f"<html><head><style>{_fonts()}body{{margin:0}}</style></head><body><div style=\"position:relative;width:1280px;height:560px;background:{BLACK};"
                 f"font-family:M;color:{WHITE}\"><div style='position:absolute;left:72px;top:64px;font-weight:800;font-size:40px;letter-spacing:.04em'>AI CORNER · ÉPISODE 23</div>"
                 f"<div style='position:absolute;left:72px;top:170px;width:1100px;font-weight:800;font-size:112px;line-height:1.04;letter-spacing:-.03em'>"
                 f"Ce que Coty a <span style='color:transparent;-webkit-text-stroke:3px {WHITE}'>vraiment</span> mis en place pour l'IA.</div></div></body></html>")
    _render(title_img, 1280, 560, d / "images" / "titre.png")
    inner = (f'<tr><td><img src="images/titre.png" width="640" alt="AI Corner, épisode 23. Ce que Coty a vraiment mis en place pour l\'IA, avec Nicolas Comestaz, VP Global Data &amp; AI Center of Excellence" style="display:block;width:100%;max-width:640px;height:auto;border:0"></td></tr>'
             f'<tr><td style="padding:0 28px 34px 28px;font-family:{FONT};font-size:18px;line-height:1.6;color:{SOFT}">{esc(mail["intro_court"])}<br><br>{_btn("Regarder l\'épisode", yt, WHITE, NAVY)}</td></tr>'
             f'<tr><td style="padding:0 28px 18px 28px;font-family:{FONT};font-size:14px;font-weight:bold;letter-spacing:.14em;color:{SOFT}">QUATRE MOMENTS, QUATRE PLANS</td></tr>'
             + cine + _thomas_close(mail, d))
    (d / "email.html").write_text(_shell(mail, BLACK, inner), encoding="utf-8")
    outs.append(d)

    # ============ 3. FACE À FACE
    d = mk("face_a_face")
    hero = (f"<html><head><style>{_fonts()}body{{margin:0}}</style></head><body><div style=\"position:relative;width:1280px;height:1300px;"
            f"background:{BLACK};overflow:hidden;font-family:M\">"
            f"<div style='position:absolute;left:0;right:0;top:-40px;text-align:center;font-weight:800;font-size:1500px;line-height:1;color:transparent;"
            f"-webkit-text-stroke:6px #3A4796'>?</div>"
            f"<img src='{_uri(host)}' style='position:absolute;left:-300px;bottom:0;height:1000px'>"
            f"<img src='{_uri(guest)}' style='position:absolute;right:-330px;bottom:0;height:1060px'>"
            f"<div style='position:absolute;left:0;right:0;bottom:0;height:300px;background:linear-gradient(to bottom,rgba(5,7,15,0),{BLACK})'></div>"
            f"<div style='position:absolute;left:72px;top:64px;color:{WHITE};font-weight:800;font-size:40px;letter-spacing:.04em'>AI CORNER · ÉPISODE 23</div>"
            f"<div style='position:absolute;left:72px;bottom:70px;color:{WHITE};font-weight:800;font-size:48px'>Thomas Spitz</div>"
            f"<div style='position:absolute;right:72px;bottom:70px;color:{WHITE};font-weight:800;font-size:48px;text-align:right'>Nicolas Comestaz</div></div></body></html>")
    _render(hero, 1280, 1300, d / "images" / "hero.png")
    qimg = (f"<html><head><style>{_fonts()}body{{margin:0;background:{BLACK}}}</style></head><body><div style=\"width:1180px;padding:30px 50px;background:{BLACK};font-family:M;"
            f"font-weight:800;font-size:84px;line-height:1.08;letter-spacing:-.025em;color:{WHITE};text-wrap:balance\">Comment passer de l'expérimentation à l'impact ?</div></body></html>")
    _render(qimg, 1280, 380, d / "images" / "question.png")
    from PIL import Image, ImageChops
    qi = Image.open(d / "images" / "question.png").convert("RGB")
    bb = ImageChops.difference(qi, Image.new("RGB", qi.size, (5, 7, 15))).getbbox()
    qi.crop((0, max(0, bb[1] - 20), 1280, bb[3] + 20)).save(d / "images" / "question.png")
    qh = (bb[3] - bb[1] + 40) // 2
    inner = (f'<tr><td><a href="{esc(yt)}"><img src="images/hero.png" width="640" alt="Thomas Spitz et Nicolas Comestaz (VP Global Data &amp; AI Center of Excellence, Coty), face à face dans AI Corner, épisode 23" style="display:block;width:100%;max-width:640px;height:auto;border:0"></a></td></tr>'
             f'<tr><td style="padding:0 0 6px 0"><h1 style="margin:0;font-size:0;line-height:0"><img src="images/question.png" width="640" height="{qh}" alt="{esc(question)}" style="display:block;width:100%;max-width:640px;height:auto;border:0"></h1></td></tr>'
             f'<tr><td style="padding:10px 28px 8px 28px;font-family:{FONT};font-size:16px;line-height:1.65;color:{SOFT}">{paras}</td></tr>'
             f'<tr><td style="padding:10px 28px 8px 28px">{_btn("Regarder l\'épisode", yt, WHITE, NAVY)}</td></tr>'
             + _thomas_close(mail, d))
    (d / "email.html").write_text(_shell(mail, BLACK, inner), encoding="utf-8")
    outs.append(d)
    return outs


if __name__ == "__main__":
    for o, h in zip(build(sys.argv[sys.argv.index("--episode") + 1] if "--episode" in sys.argv else "E23"), (2500, 3700, 2600)):
        print(preview(o, h))
