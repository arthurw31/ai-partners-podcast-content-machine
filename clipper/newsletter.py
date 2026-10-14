"""Mail podcast de Thomas : le mail de l'épisode, écrit à la 1re personne par le fondateur, mis en page et prêt à envoyer.

Idée de Thomas Spitz (08/10/2026), demande d'Arthur (12/10/2026) : « un 5e workflow, une newsletter dans ce style-là
(mail « Nostra » d'On Train) : un mail qui part directement de la part du founder ». Choix d'Arthur : mail mis en page
(comme la référence), vouvoiement, contenu de base (invité + « Au programme » + YouTube), outil d'envoi pas encore choisi
-> HTML d'e-mail compatible avec tous les outils (tableaux, styles en ligne, 600 px) + images à téléverser + version texte.

1. `write` : Claude Opus lit la transcription (qui parle), les chapitres et le titre validé, et écrit le mail (brief
   `MARQUES/<m>/newsletter.md`) ; chaque fait sur l'invité est adossé à un passage de l'épisode ;
2. `check` : faits retrouvés, chiffres présents dans l'épisode, longueurs (objet, aperçu, programme) ;
3. `render` : images (bandeau, photo de l'invité, miniature YouTube avec bouton lecture) + `email.html` + `email.txt` +
   `objet.txt` + aperçu PNG ; le titre et la miniature viennent de `titles --pick` / `thumbnail --pick` (provisoires sinon) ;
4. `finalize` (`--final`) : l'équipe a validé -> `newsletter/final/` ; refuse sans lien YouTube.
"""
from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import tempfile
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw
from rich.console import Console

from .carousel import _logo_svg, _num, _plain, _status, _uri, speaker_text
from .titles import _digits, find_evidence, norm

console = Console()

LIMITS = {"subject": 70, "preheader": 90, "theme_words": 9, "item_title_words": 6, "items": 4}
NAVY, BLUE, LIGHT = "#151D53", "#258AF3", "#F1F6FD"


def brief(brand) -> str:
    p = brand.dir / "newsletter.md"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def _cfg(brand) -> dict:
    return dict(brand.cfg.get("newsletter") or {})


def chapters(ep: Path) -> list[str]:
    """Chapitres de la description YouTube de l'épisode monté (`0:00 Titre`)."""
    f = ep / "episode" / "description_youtube.md"
    if not f.exists():
        return []
    return [l.strip() for l in f.read_text(encoding="utf-8").splitlines() if re.match(r"^\d+:\d\d", l.strip())]


def episode_title(ep: Path) -> tuple[str, bool]:
    """(titre, validé ?) : le titre validé par l'équipe, sinon la 1re proposition (provisoire)."""
    from .titles import load_validated
    val = load_validated(ep)
    if val:
        return " ".join(val["lines"]), True
    f = ep / "titres" / "propositions.json"
    if f.exists():
        props = json.loads(f.read_text(encoding="utf-8")).get("proposals") or []
        if props:
            return " ".join(props[0]["lines"]), False
    return "", False


def thumbnail_image(ep: Path) -> tuple[Path | None, bool]:
    """(miniature, choisie ?) : la miniature choisie par l'équipe, sinon la variante 1 (provisoire)."""
    m = ep / "miniatures"
    if (m / "miniature_finale.jpg").exists():
        return m / "miniature_finale.jpg", True
    for f in sorted(m.glob("variante_*.jpg")):
        return f, False
    return None, False


# ---------------------------------------------------------------------------------------------------------------
# 1. Rédaction
# ---------------------------------------------------------------------------------------------------------------

PROMPT = """Tu écris, au nom de Thomas Spitz (CEO et fondateur d'AI Partners, animateur du podcast AI Corner), le mail qu'il
envoie personnellement à ses contacts pour un nouvel épisode. Brief, à suivre à la lettre :

{brief}

Réponds UNIQUEMENT en JSON :
{{"subject": "🎙️ AI Corner E22 : …", "preheader": "…", "theme": "phrase-thème de 4 à 9 mots",
  "hook": "la question que pose l'épisode (1 à 2 phrases)",
  "intro": "Pour ce nouvel épisode d'AI Corner, j'ai le plaisir de recevoir … (qui est l'invité, 2 à 3 phrases, puis l'angle de la conversation)",
  "program": [{{"title": "titre court", "text": "1 phrase concrète", "chapter": "4:53"}}],
  "closing": "mot de fin de Thomas, 1 à 2 phrases",
  "evidence": [{{"claim": "fait sur l'invité ou chiffre cité", "t": 123.4, "quote": "passage EXACT de la transcription"}}]}}"""


def write(brand, transcript: dict, ep: Path, meta: dict, note: str = "") -> dict:
    from .llm import ask_json
    console.print("Claude écrit le mail de Thomas (≈ 3 min)…")
    title, _ = episode_title(ep)
    user = (f"Épisode {meta['number']}. Invité : {meta['guest']}, {meta['role']} ({meta['company']}).\n"
            f"Titre de l'épisode : {title or '(pas encore validé)'}\n"
            "Chapitres de l'épisode monté :\n" + "\n".join(chapters(ep) or ["(pas encore de chapitres)"])
            + (f"\nPRÉCISION DE L'ÉQUIPE : {note}\n" if note else "")
            + f"\n\nTRANSCRIPTION (une phrase par ligne, [début en s] orateur : texte) :\n{speaker_text(transcript, ep, meta['guest'])}")
    model = str(_cfg(brand).get("model") or "claude-opus-5")
    data = ask_json(PROMPT.format(brief=brief(brand)), user, model=model, backend=brand.cfg.selection.llm_backend,
                    max_tokens=6000)
    return {"episode": meta["number"], "guest": meta["guest"], "company": meta["company"], "role": meta["role"],
            "generated": date.today().isoformat(), "note": note, "youtube_url": "", **data}


def check(mail: dict, segments: list[dict]) -> list[dict]:
    out: list[dict] = []

    def add(level, msg):
        out.append({"level": level, "msg": msg})
    full = re.sub(r"[  .,]", "", _digits(norm(" ".join(s["text"] for s in segments))))
    if len(mail.get("subject", "")) > LIMITS["subject"]:
        add("ATTENTION", f"objet long ({len(mail['subject'])} caractères, ≤ {LIMITS['subject']} : coupé sur mobile)")
    if len(mail.get("preheader", "")) > LIMITS["preheader"]:
        add("ATTENTION", f"texte d'aperçu long ({len(mail['preheader'])} caractères)")
    if len((mail.get("theme") or "").split()) > LIMITS["theme_words"]:
        add("ATTENTION", "phrase-thème longue")
    prog = mail.get("program") or []
    if len(prog) != LIMITS["items"]:
        add("ATTENTION", f"{len(prog)} points au programme (4 attendus)")
    for p in prog:
        if len(p.get("title", "").split()) > LIMITS["item_title_words"]:
            add("ATTENTION", f"titre du programme long : « {p['title']} »")
    sizes = [len(p.get("text", "")) for p in prog]
    if sizes and (max(sizes) > 175 or max(sizes) - min(sizes) > 30):
        add("ATTENTION", f"textes du programme de longueurs trop différentes ({min(sizes)} à {max(sizes)} car., visé 150-170) : "
                         "les 4 cartes ont la même taille, la plus longue impose sa hauteur")
    for ev in mail.get("evidence") or []:
        _, score = find_evidence(segments, ev.get("quote", ""), _num(ev.get("t")))
        if score < 0.6:
            add("ÉCHEC", f"fait non retrouvé dans l'épisode : « {ev.get('claim', '')} »")
        elif score < 0.85:
            add("ATTENTION", f"fait approximatif ({score:.0%}) : « {ev.get('claim', '')} »")
    shown = " ".join(str(mail.get(k, "")) for k in ("subject", "preheader", "theme", "hook", "intro", "closing"))
    shown += " " + " ".join(f"{p.get('title', '')} {p.get('text', '')}" for p in prog)
    shown = re.sub(r"\bE\d+\b|\d+:\d\d", "", shown)                 # numéro d'épisode et chapitres : pas des faits
    for num in re.findall(r"\d[\d  .,]*\d|\d", _digits(shown)):
        d = re.sub(r"[  .,]", "", num)
        if len(d) >= 2 and d not in full:
            add("ÉCHEC", f"chiffre « {num} » absent de la transcription")
    return out


# ---------------------------------------------------------------------------------------------------------------
# 2. Rendu
# ---------------------------------------------------------------------------------------------------------------

def _shot(page: str, w: int, h: int, out: Path) -> Path:
    from .thumbnail import _browser
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        f = Path(td) / "p.html"
        f.write_text(page, encoding="utf-8")
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)                    # aucune fenêtre chez l'utilisateur
        subprocess.run([_browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                        f"--user-data-dir={Path(td) / 'prof'}", "--virtual-time-budget=6000", "--force-device-scale-factor=1",
                        f"--window-size={w},{h}", f"--screenshot={out}", f.as_uri()], capture_output=True, timeout=120,
                       creationflags=flags)
    if not out.exists():
        raise SystemExit(f"Rendu Chrome échoué : {out.name}")
    return out


def _fonts_css(brand) -> str:
    f = brand.assets_dir / "fonts"
    return (f'@font-face{{font-family:M;src:url("{_uri(f / "Metropolis-Regular.ttf")}");font-weight:400}}'
            f'@font-face{{font-family:M;src:url("{_uri(f / "Metropolis-Bold.ttf")}");font-weight:700}}'
            f'@font-face{{font-family:M;src:url("{_uri(f / "Metropolis-ExtraBold.ttf")}");font-weight:800}}')


def make_images(brand, ep: Path, mail: dict, portraits_: dict, thumb: Path | None) -> dict:
    """Images du mail (à téléverser dans l'outil d'envoi) : bandeau, photo de l'invité, miniature YouTube + bouton lecture."""
    d = ep / "newsletter" / "images"
    d.mkdir(parents=True, exist_ok=True)
    logo = _logo_svg(brand.asset("logo_horizontal.svg"), "#FFFFFF")
    banner = (f"<html><head><meta charset='utf-8'><style>{_fonts_css(brand)}*{{margin:0}}body{{width:1200px;height:300px;"
              f"background:{NAVY};font-family:M,Arial;overflow:hidden;position:relative}}"
              f".l{{position:absolute;right:-260px;top:-120px;width:1100px;opacity:.95;mix-blend-mode:screen}}.k{{position:absolute;left:72px;top:92px;"
              f"color:#fff;font-weight:800;font-size:76px;letter-spacing:-.01em}}.k b{{color:{BLUE}}}"
              f".s{{position:absolute;left:76px;top:190px;color:#C9D3F5;font-size:28px;letter-spacing:.14em;text-transform:uppercase}}"
              f".g{{position:absolute;right:72px;bottom:56px;height:34px}}.g svg{{height:100%;width:auto}}</style></head><body>"
              f"<img class='l' src='{_uri(brand.asset('outro_bg.png'))}'><div class='k'>AI <b>Corner</b></div>"
              f"<div class='s'>Le podcast d'AI Partners · {html.escape(mail['episode'])}</div><div class='g'>{logo}</div></body></html>")
    out = {"banner": _shot(banner, 1200, 300, d / "bandeau.png")}
    g = portraits_.get("guest")
    from .newsletter_templates import make_duo, make_hero, square_photo
    hero = make_hero(brand, d, mail, g, _shot, _fonts_css(brand), _uri)
    if hero:
        out["hero"] = hero
    duo = make_duo(d, mail, portraits_.get("host"), g, _shot, _fonts_css(brand), _uri)
    if duo:
        out["duo"] = duo
    from .newsletter_templates import make_chrome
    out.update(make_chrome(brand, d, mail, _shot, _fonts_css(brand), _uri, logo, _cfg(brand).get("platforms") or []))
    host = square_photo(portraits_.get("host"), d / "thomas.jpg")
    if host:
        out["host"] = host
    if g:
        size = 640
        bg = Image.new("RGB", (size, size))
        dr = ImageDraw.Draw(bg)
        for y in range(size):                                   # dégradé bleu de la charte (comme la couverture du carrousel)
            k = y / size
            c = tuple(int(a + (b - a) * k) for a, b in zip((37, 138, 243), (10, 71, 182)))
            dr.line([(0, y), (size, y)], fill=c)
        im = Image.open(g).convert("RGBA")
        sc = size * 1.05 / im.width
        im = im.resize((int(im.width * sc), int(im.height * sc)), Image.Resampling.LANCZOS)
        bg.paste(im, ((size - im.width) // 2, int(size * 0.06)), im)
        m = Image.new("L", (size, size), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, size - 1, size - 1], 48, fill=255)
        rgba = Image.new("RGBA", (size, size), (255, 255, 255, 0))
        rgba.paste(bg, (0, 0), m)
        flat = Image.new("RGB", (size, size), (255, 255, 255))   # fond blanc : les e-mails gèrent mal la transparence
        flat.paste(rgba, (0, 0), rgba)
        out["guest"] = d / "invite.jpg"
        flat.save(out["guest"], quality=90)
    if thumb:
        im = Image.open(thumb).convert("RGB").resize((1200, 675), Image.Resampling.LANCZOS)
        out["thumb_plain"] = d / "miniature_sans_play.jpg"                 # en-tête du gabarit « duo » : la même miniature, sans le bouton
        im.save(out["thumb_plain"], quality=90)
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
        dr = ImageDraw.Draw(ov)
        cx, cy, r = 600, 338, 74
        dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(21, 29, 83, 215))
        dr.polygon([(cx - 24, cy - 38), (cx - 24, cy + 38), (cx + 42, cy)], fill=(255, 255, 255, 255))
        im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
        out["youtube"] = d / "episode_youtube.jpg"
        im.save(out["youtube"], quality=88)
    return out


def _p(text: str) -> str:
    return html.escape(text or "").replace("\n", "<br>")


def email_html(brand, mail: dict, imgs: dict, title: str, template: str = "classique") -> str:
    """HTML d'e-mail (tableaux, styles en ligne, 600 px) : images en chemins relatifs `images/…`, à téléverser dans l'outil.
    `template` : classique | nuit | heros | editorial | vedette (voir newsletter_templates.py)."""
    from .newsletter_templates import BUILDERS, context
    if template in BUILDERS:
        return BUILDERS[template](context(_cfg(brand), mail, imgs, title))
    cfg = _cfg(brand)
    from .newsletter_templates import default_url
    url = default_url(cfg, mail)
    font = "Helvetica, Arial, sans-serif"
    sig = cfg.get("signature") or "Thomas Spitz<br>CEO et fondateur d'AI Partners"
    rel = lambda k: f"images/{imgs[k].name}" if imgs.get(k) else ""       # noqa: E731
    btn = (f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin:28px auto"><tr><td bgcolor="{BLUE}" '
           f'style="border-radius:999px"><a href="{html.escape(url)}" style="display:inline-block;padding:16px 34px;'
           f'font-family:{font};font-size:16px;font-weight:bold;color:#ffffff;text-decoration:none;letter-spacing:.04em">'
           f'{html.escape(cfg.get("button") or "REGARDER L’ÉPISODE")} 🎙️</a></td></tr></table>')
    prog = "".join(
        f'<tr><td style="padding:0 0 18px 0;font-family:{font};font-size:16px;line-height:1.55;color:{NAVY}">'
        f'<span style="color:{BLUE};font-weight:bold">{k:02d}</span>&nbsp; <strong>{html.escape(p.get("title", ""))}</strong> : '
        f'{html.escape(p.get("text", ""))}</td></tr>' for k, p in enumerate(mail.get("program") or [], 1))
    guest_img = (f'<img src="{rel("guest")}" width="150" height="150" alt="{html.escape(mail["guest"])}" '
                 f'style="display:block;border-radius:24px;width:150px;height:150px">' if imgs.get("guest") else "")
    yt = (f'<a href="{html.escape(url)}"><img src="{rel("youtube")}" width="552" alt="{html.escape(title)}" '
          f'style="display:block;width:100%;max-width:552px;border-radius:14px"></a>' if imgs.get("youtube") else "")
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(mail.get("subject", ""))}</title></head>
<body style="margin:0;padding:0;background:#EEF2FA">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{html.escape(mail.get("preheader", ""))}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#EEF2FA"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" bgcolor="#ffffff" style="width:100%;max-width:600px;border-radius:16px;overflow:hidden">
<tr><td><img src="{rel("banner")}" width="600" alt="AI Corner, le podcast d'AI Partners" style="display:block;width:100%;max-width:600px"></td></tr>
<tr><td style="padding:36px 40px 8px 40px">
 <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
  <td width="150" valign="top">{guest_img}</td>
  <td valign="middle" style="padding-left:24px;font-family:{font}">
   <div style="font-size:20px;font-weight:bold;color:{NAVY}">{html.escape(mail["guest"])}</div>
   <div style="font-size:14px;color:#5A6488;padding-top:4px">{html.escape(mail.get("role") or "")}</div>
   <div style="font-size:22px;font-weight:bold;color:{BLUE};line-height:1.25;padding-top:14px">{html.escape(mail.get("theme", ""))}</div>
  </td></tr></table>
</td></tr>
<tr><td style="padding:24px 40px 0 40px;font-family:{font};font-size:17px;line-height:1.6;color:{NAVY}">
 <!--HELLO--><p style="margin:0 0 18px 0;font-weight:bold">{_p(mail.get("hook"))}</p>
 <p style="margin:0">{_p(mail.get("intro"))}</p>
</td></tr>
<tr><td align="center">{btn}</td></tr>
<tr><td style="padding:8px 40px 10px 40px;font-family:{font}">
 <div style="font-size:20px;font-weight:bold;color:{NAVY};padding-bottom:18px;border-top:1px solid #E1E7F5;padding-top:26px">Au programme de cet épisode</div>
 <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{prog}</table>
</td></tr>
<tr><td style="padding:6px 24px 0 24px;font-family:{font};font-size:16px;color:{NAVY}" align="center">
 <p style="margin:0 0 14px 0;font-weight:bold">Retrouvez l'épisode complet sur YouTube 👇</p>{yt}
</td></tr>
<tr><td style="padding:30px 40px 36px 40px;font-family:{font};font-size:17px;line-height:1.6;color:{NAVY}">
 <p style="margin:0 0 18px 0">{_p(mail.get("closing"))}</p>
 <p style="margin:0;font-weight:bold">{sig}</p>
</td></tr>
</table>
<p style="font-family:{font};font-size:12px;color:#8A93B2;padding-top:16px">AI Corner, le podcast d'AI Partners.<!--FOOT--></p>
</td></tr></table></body></html>"""


def email_text(brand, mail: dict) -> str:
    cfg = _cfg(brand)
    sig = (cfg.get("signature") or "Thomas Spitz<br>CEO et fondateur d'AI Partners").replace("<br>", "\n")
    from .newsletter_templates import default_url
    url = default_url(cfg, mail)
    prog = "\n".join(f"- {p.get('title', '')} : {p.get('text', '')}" for p in mail.get("program") or [])
    return (f"{mail['guest']} ({mail.get('role', '')})\n{mail.get('theme', '')}\n\n{mail.get('hook', '')}\n\n"
            f"{mail.get('intro', '')}\n\nRegarder l'épisode : {url}\n\nAu programme de cet épisode\n{prog}\n\n"
            f"{mail.get('closing', '')}\n\n{sig}\n")


def _preview(d: Path, page: str, out: Path) -> Path:
    """Aperçu PNG du mail (images locales), recadré sur le contenu."""
    shot = _shot(page.replace('src="images/', f'src="{_uri(d / "images")}/'), 760, 3000, d / "_apercu.png")
    im = Image.open(shot).convert("RGB")
    px = im.load()
    bottom = im.height - 1                                               # recadre le fond vide sous le mail
    while bottom > 0 and px[im.width // 2, bottom] == px[im.width // 2, im.height - 1]:
        bottom -= 1
    im.crop((0, 0, im.width, min(im.height, bottom + 40))).save(out)
    shot.unlink()
    return out


def templates_sheet(brand, d: Path, names: list[str], name: str = "planche_gabarits.png") -> Path:
    """Planche : les aperçus de tous les gabarits côte à côte (choix de l'équipe)."""
    from .canva_template import font
    from .newsletter_templates import TEMPLATES
    w, pad, head = 440, 28, 74
    ims = [Image.open(d / f"apercu_{n}.png").convert("RGB") for n in names]
    ims = [i.resize((w, int(i.height * w / i.width)), Image.Resampling.LANCZOS) for i in ims]
    sheet = Image.new("RGB", (pad + len(ims) * (w + pad), head + max(i.height for i in ims) + pad), (244, 246, 251))
    dr = ImageDraw.Draw(sheet)
    f = font(brand.assets_dir, "Montserrat", "Bold", 20)
    for k, (n, im) in enumerate(zip(names, ims)):
        x = pad + k * (w + pad)
        dr.text((x, 24), TEMPLATES[n].split(" : ")[0], font=f, fill=(21, 29, 83))
        sheet.paste(im, (x, head))
    out = d / name
    sheet.save(out)
    return out


def render(brand, ep: Path, mail: dict, portraits_: dict, template: str | None = None) -> dict:
    """Rend le mail. `template` : un gabarit, ou « all » (tous, comparés sur `planche_gabarits.png`, sans toucher à
    `email.html`). Sans valeur : `newsletter.template` de brand.yaml (« classique » par défaut)."""
    from .newsletter_templates import TEMPLATES
    d = ep / "newsletter"
    d.mkdir(parents=True, exist_ok=True)
    title, title_ok = episode_title(ep)
    thumb, thumb_ok = thumbnail_image(ep)
    imgs = make_images(brand, ep, mail, portraits_, thumb)
    template = template or str(_cfg(brand).get("template") or "classique")
    if template in ("all", "variantes"):
        from .newsletter_templates import VARIANTES
        names = list(TEMPLATES) if template == "all" else list(VARIANTES)
        for n in names:
            page = email_html(brand, mail, imgs, title, n)
            (d / f"email_{n}.html").write_text(page, encoding="utf-8")
            _preview(d, page, d / f"apercu_{n}.png")
        sheet = templates_sheet(brand, d, names, "planche_gabarits.png" if template == "all" else "planche_variantes.png")
        return {"preview": sheet, "html": d / "email_nuit.html", "images": imgs, "templates": names,
                "notes": ["gabarits à comparer : choisir puis `newsletter --template <nom> --render`"]}
    if template not in TEMPLATES:
        raise SystemExit(f"Gabarit inconnu « {template} » : {', '.join(TEMPLATES)} ou all")
    page = email_html(brand, mail, imgs, title, template)
    (d / "email.html").write_text(page, encoding="utf-8")
    (d / "email.txt").write_text(email_text(brand, mail), encoding="utf-8")
    (d / "objet.txt").write_text(f"Objet : {mail.get('subject', '')}\nTexte d'aperçu : {mail.get('preheader', '')}\n"
                                 f"Expéditeur : {_cfg(brand).get('from_name') or 'Thomas Spitz'}\n", encoding="utf-8")
    _preview(d, page, d / "apercu.png")
    notes = []
    if not title_ok:
        notes.append("titre de l'épisode PROVISOIRE (pas encore validé : titles --pick)")
    if not thumb_ok:
        notes.append("miniature PROVISOIRE (pas encore choisie : thumbnail --pick)")
    return {"preview": d / "apercu.png", "html": d / "email.html", "images": imgs, "notes": notes}


def save(ep: Path, mail: dict, segments: list[dict]) -> Path:
    mail["checks"] = check(mail, segments)
    mail["status"] = _status(mail["checks"])
    d = ep / "newsletter"
    d.mkdir(parents=True, exist_ok=True)
    (d / "contenu.json").write_text(json.dumps(mail, ensure_ascii=False, indent=1), encoding="utf-8")
    return d / "contenu.json"


def finalize(ep: Path, mail: dict, by: str = "", note: str = "") -> Path:
    title_ok, thumb_ok = episode_title(ep)[1], thumbnail_image(ep)[1]
    if not (title_ok and thumb_ok):
        raise SystemExit("Titre ou miniature encore provisoires : `titles --pick` et `thumbnail --pick` d'abord, puis --render")
    src, final = ep / "newsletter", ep / "newsletter" / "final"
    if final.exists():
        shutil.rmtree(final)
    final.mkdir(parents=True)
    for name in ("email.html", "email.txt", "objet.txt", "apercu.png"):
        shutil.copy2(src / name, final / name)
    shutil.copytree(src / "images", final / "images")
    rec = {"episode": mail["episode"], "validated_by": by, "validated_on": date.today().isoformat(), "note": note}
    (src / "newsletter_validee.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    return final


# ------------------------------------------------------------------------------------------------ version prête à l'envoi

PAGES_BASE = "https://arthurw31.github.io/ai-partners-podcast-content-machine/newsletters"


def send_ready(brand, ep: Path, mail: dict) -> dict:
    """Version prête pour l'envoi par n8n depuis la boîte de Thomas (Arthur, 13/10/2026 : « on fait juste avec n8n et le mail
    de Thomas » ; « que le destinataire voie le vrai rendu avec les images »).

    - images copiées dans `docs/newsletters/<E>/` (publiées par GitHub Pages au prochain push) et liens ABSOLUS `https://`
      dans le HTML : la boîte du destinataire les charge toute seule, il ne clique sur rien. Ne jamais supprimer le dossier
      d'une newsletter envoyée (un vieux mail rouvert va rechercher ses images) ;
    - « Bonjour {{prenom}}, » en tête et un lien « Se désinscrire » ({{lien_desinscription}}) en pied : remplacés par n8n ;
    - le HTML est aussi publié (`docs/newsletters/<E>/email.html`) : n8n le lit à cette adresse, rien à copier à la main.
    """
    from .config import ROOT
    d = ep / "newsletter"
    src = d / "final" if (d / "final" / "email.html").exists() else d
    e = str(mail.get("episode") or "E")
    base = str(_cfg(brand).get("public_base_url") or PAGES_BASE).rstrip("/") + f"/{e}"
    pub = ROOT / "docs" / "newsletters" / e
    pub.mkdir(parents=True, exist_ok=True)
    h = (src / "email.html").read_text(encoding="utf-8")
    for name in sorted(set(re.findall(r'src="images/([^"]+)"', h))):          # seulement les images du gabarit choisi
        if (src / "images" / name).exists():
            shutil.copy2(src / "images" / name, pub / name)
    h = h.replace('src="images/', f'src="{base}/')
    hello = '<p style="margin:0 0 14px 0;font-weight:bold">Bonjour {{prenom}},</p>'
    unsub = ('<br>Vous recevez ce mail car vous êtes en contact avec AI Partners. '
             '<a href="{{lien_desinscription}}" style="color:#8A93B2">Se désinscrire</a>')
    if "<!--HELLO-->" in h:                       # tous les gabarits : marqueurs (newsletter_templates.py)
        h = h.replace("<!--HELLO-->", hello, 1).replace("<!--FOOT-->", unsub, 1)
    else:                                         # ancien HTML sans marqueurs
        hook = '<p style="margin:0 0 18px 0;font-weight:bold">'
        h = h.replace(hook, '<p style="margin:0 0 14px 0">Bonjour {{prenom}},</p>\n ' + hook, 1)
        h = h.replace("AI Corner, le podcast d'AI Partners.</p>", "AI Corner, le podcast d'AI Partners." + unsub + "</p>", 1)
    out = d / "email_a_envoyer.html"
    out.write_text(h, encoding="utf-8")
    (pub / "email.html").write_text(h, encoding="utf-8")
    subject = (src / "objet.txt").read_text(encoding="utf-8") if (src / "objet.txt").exists() else ""
    m = re.search(r"Objet\s*:\s*(.+)", subject)
    (pub / "objet.txt").write_text((m.group(1).strip() if m else mail.get("subject", "")) + "\n", encoding="utf-8")
    return {"html": out, "public_html": f"{base}/email.html", "public_dir": pub, "images": sorted(p.name for p in pub.glob("*"))}
