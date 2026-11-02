"""Gabarit « mosaïque » : mail tout en noir et blanc, une seule forme blanche à coins arrondis qui court sur tout le mail
(Arthur, 02/11/2026 : référence = site « Technology that connects », cartes arrondies qui s'emboîtent, « vraiment tech, web3, clean »).

Un mail ne sait pas dessiner une forme à coins CONCAVES : le haut du mail (titre + accroche + programme en escalier) et le mot de la fin
sont donc des IMAGES rendues par Chrome (2x, fond noir opaque, texte alternatif complet, lien vers l'épisode) ; le reste est du vrai
texte (pied de page). Textes raccourcis : `hook_court`, `intro_court`, `closing_court`, `program[i].court`, `stat` de contenu.json, à défaut
le début du texte long. Icônes : Lucide (ISC), `MARQUES/<marque>/assets/icons/` ; pictogramme d'un point = `program[i].glyph`.
"""
from __future__ import annotations

import math
import re
from pathlib import Path

from PIL import Image

from .newsletter_templates import FONT, PLATFORM_LABELS, esc, shell

W = 680                  # largeur de la carte du mail (px CSS) ; images rendues à 2x
SW = 600                 # largeur de la forme blanche
R_OUT, R_IN = 40, 14     # coins convexes bien arrondis ; coins des cases noires (concaves pour la forme blanche)
OV = 6                   # recouvrement vertical de deux carrés blancs voisins = épaisseur de la jonction (fine, comme sur la référence)
HEAD = 96                # haut de la forme : barre « AI Corner by … » (20 px de marge, 56 px) puis 20 px
TW = 560                 # largeur de la miniature, posée DANS le blanc (20 px de marge de chaque côté)
TH = round(TW * 9 / 16)  # hauteur de la miniature
TXT = HEAD + TH + 30     # début du titre, de l'accroche et du bouton
H0 = TXT + 430           # fin du grand rectangle (titre, accroche, intro, bouton)
TITLE_H = 84             # titre du bandeau des plateformes, dans la même forme blanche
STEP = 830               # hauteur de l'escalier du programme
H1 = 330                 # hauteur du rectangle final (mot de Thomas + réservation)
DEFAULT_GLYPHS = ["git-compare", "zap", "network", "users"]
INK = "#000000"


def rounded_path(pts: list, r_out: float, r_in: float) -> str:
    """Contour rectiligne à coins arrondis : rayon `r_out` aux coins convexes, `r_in` (plus fin) aux coins concaves."""
    d = []
    for i in range(len(pts)):
        p, v, q = pts[i - 1], pts[i], pts[(i + 1) % len(pts)]
        a, b = (v[0] - p[0], v[1] - p[1]), (q[0] - v[0], q[1] - v[1])
        la, lb = math.hypot(*a), math.hypot(*b)
        a, b = (a[0] / la, a[1] / la), (b[0] / lb, b[1] / lb)
        convex = a[0] * b[1] - a[1] * b[0] > 0
        r = r_out if convex else r_in
        s, e = (v[0] - a[0] * r, v[1] - a[1] * r), (v[0] + b[0] * r, v[1] + b[1] * r)
        d.append(("M" if i == 0 else "L") + f"{s[0]:.1f},{s[1]:.1f} A{r},{r} 0 0 {1 if convex else 0} {e[0]:.1f},{e[1]:.1f}")
    return " ".join(d) + " Z"


def stair(o: int) -> dict:
    """Ordonnées de l'escalier : chaque carré blanc commence `OV` px AVANT la fin du précédent (jonction fine)."""
    r1s, r1e = o + 200, o + 420
    l2s = r1e - OV
    l2e = l2s + 230
    return {"l1e": r1s + OV, "r1s": r1s, "r1e": r1e, "l2s": l2s, "l2e": l2e, "r2s": l2e - OV}


def ribbon(o: int, end: int | None = None) -> list:
    """Forme blanche : grand rectangle (0..o), puis 4 carrés en escalier reliés par un cou fin, puis rectangle final."""
    end, y = end or o + STEP + H1, stair(o)
    return [(0, 0), (SW, 0), (SW, o), (300, o), (300, y["r1s"]), (SW, y["r1s"]), (SW, y["r1e"]), (300, y["r1e"]), (300, y["r2s"]),
            (SW, y["r2s"]), (SW, end), (0, end), (0, o + STEP), (300, o + STEP), (300, y["l2e"]), (0, y["l2e"]), (0, y["l2s"]),
            (300, y["l2s"]), (300, y["l1e"]), (0, y["l1e"])]


def sentences(text: str, max_chars: int, max_sentences: int = 2) -> str:
    """Début d'un texte long, coupé à une fin de phrase (jamais au milieu d'un mot) : repli quand le texte court manque."""
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    out = ""
    for s in parts[:max_sentences]:
        if out and len(out) + len(s) + 1 > max_chars:
            break
        out = (out + " " + s).strip()
    if len(out) > max_chars:
        out = out[:max_chars].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    return out


def short_texts(mail: dict, title: str) -> dict:
    prog = []
    for i, p in enumerate(mail.get("program") or []):
        prog.append({"time": _tc(p.get("chapter")), "title": p.get("title", ""), "text": p.get("court") or sentences(p.get("text", ""), 95, 1),
                     "glyph": p.get("glyph") or DEFAULT_GLYPHS[i % len(DEFAULT_GLYPHS)]})
    return {"title": re.sub(r"^\s*AI Corner E\d+\s*\|\s*", "", title or mail.get("theme", "")),
            "hook": mail.get("hook_court") or sentences(mail.get("hook", ""), 150, 2),
            "intro": mail.get("intro_court") or sentences(mail.get("intro", ""), 230, 2),
            "closing": mail.get("closing_court") or sentences(mail.get("closing", ""), 170, 1),
            "stat": mail.get("stat"), "program": prog}


def _tc(v) -> str:
    m = re.match(r"(\d+):(\d{2})", str(v or ""))
    return f"{int(m.group(1)):02d}:{m.group(2)}" if m else ""


def icon(brand, name: str, size: int = 34, color: str = INK, sw: float = 1.3) -> str:
    p = brand.asset(f"icons/lucide_{name}.svg")
    if not p:
        return ""
    svg = re.sub(r"<!--.*?-->", "", p.read_text(encoding="utf-8"), flags=re.S)
    svg = re.sub(r'\swidth="[^"]*"', "", svg, count=1)
    svg = re.sub(r'\sheight="[^"]*"', "", svg, count=1)
    svg = svg.replace("<svg", f'<svg width="{size}" height="{size}" style="color:{color}"', 1)
    return svg.replace('stroke-width="2"', f'stroke-width="{sw}"')


def sphere(cx: float, cy: float, rad: float, n: int = 520) -> str:
    """Sphère de points (la touche « tech » de la référence) : points de Fibonacci, taille et opacité selon la profondeur."""
    out, g, tilt = [], math.pi * (3 - math.sqrt(5)), 0.45
    for i in range(n):
        y = 1 - 2 * (i + 0.5) / n
        rr = math.sqrt(1 - y * y)
        x, z = math.cos(g * i) * rr, math.sin(g * i) * rr
        y, z = y * math.cos(tilt) - z * math.sin(tilt), y * math.sin(tilt) + z * math.cos(tilt)
        if z < -0.15:
            continue
        out.append(f'<circle cx="{cx + x * rad:.1f}" cy="{cy + y * rad:.1f}" r="{0.6 + 0.9 * (z + 0.15):.2f}" fill="#fff" '
                   f'opacity="{0.35 + 0.65 * max(z, 0):.2f}"/>')
    return "".join(out)


PLUS = '<svg width="16" height="16" viewBox="0 0 16 16"><path d="M8 0v16M0 8h16" stroke="{c}" stroke-width="1.5"/></svg>'
ARROW = '<svg width="{s}" height="{s}" viewBox="0 0 64 64"><path d="M14 50 50 14M22 14h28v28" stroke="{c}" stroke-width="3.2" fill="none"/></svg>'


def _css(fonts_css: str) -> str:
    return (fonts_css + "*{box-sizing:border-box;margin:0}body{background:#000;color:#fff;font-family:M,Arial,sans-serif;zoom:2;overflow:hidden}"
            ".m{font:13px/1 Consolas,'Courier New',monospace;letter-spacing:.02em}.bt{font:700 20px/1.15 M;color:#000;margin-top:16px;letter-spacing:-.01em}"
            ".bx{font:14px/1.5 Arial;color:#4A4A4A;margin-top:8px}.hw{font:800 26px/1.08 M;color:#fff;letter-spacing:-.02em}"
            ".big{font:800 46px/1 M;color:#fff;letter-spacing:-.03em}"
            ".btn{display:inline-block;background:#000;color:#fff;font:700 15px/1 M;padding:17px 26px;border-radius:40px;white-space:nowrap}"
            ".lg{display:block;line-height:0}.lg svg{height:14px;width:auto;display:block}")


def _lab(text: str, color: str) -> str:
    return f'<div style="display:flex;align-items:center;gap:10px">{PLUS.format(c=color)}<span class=m style="color:{color}">{esc(text)}</span></div>'


def _item(x: int, y: int, it: dict) -> str:
    """Carré blanc d'un point du programme : le thème et son petit texte (l'icône est dans la case noire voisine)."""
    return (f'<div style="position:absolute;left:{x}px;top:{y}px;width:240px"><div class=bt style="margin-top:0">{esc(it["title"])}</div>'
            f'<div class=bx>{esc(it["text"])}</div></div>')


def _icon_cell(brand, cx: int, cy: int, it: dict) -> str:
    """Case noire : l'icône du point voisin, en blanc, centrée."""
    return (f'<div style="position:absolute;left:{cx - 45}px;top:{cy - 45}px;width:90px;height:90px">'
            f'{icon(brand, it["glyph"], 90, "#fff", 1.1)}</div>')


def make_mosaic(brand, d: Path, mail: dict, shot, fonts_css: str, uri, thumb: Path | None, logo_svg: str, platforms: list,
                title: str, cfg: dict) -> dict:
    """Images du gabarit : en-tête, miniature arrondie, forme blanche (haut puis mot de la fin), titre et tuiles des plateformes."""
    t = short_texts(mail, title)
    o = H0
    fin = o + STEP + H1 + TITLE_H                  # fin de ce qui est rendu ; le blanc continue ensuite (logos, puis pied arrondi)
    end = fin + 160                                # la forme dépasse la coupe : le bas arrondi est une image à part
    y = stair(o)
    prog = t["program"] + [{"time": "", "title": "", "text": "", "glyph": DEFAULT_GLYPHS[0]}] * (4 - len(t["program"]))
    ox = (W - SW) // 2
    host = cfg.get("from_name") or "Thomas Spitz"
    b = cfg.get("booking") or {}
    style = _css(fonts_css)
    out = {}
    labels = " · ".join(PLATFORM_LABELS.get((p.get("name") or "").lower(), p.get("name", "")) for p in platforms)

    # --- UNE seule forme blanche du haut (barre du titre) au bas (plateformes) : rendue d'un bloc puis coupée en tranches
    shape = rounded_path(ribbon(o, end), R_OUT, R_IN)
    book = (f'<div style="display:flex;justify-content:space-between;align-items:center"><div style="font:800 22px/1.15 M;color:#000">'
            f'{esc(b.get("title") or "")}</div><span class=btn style="font-size:14px;padding:15px 22px">Réserver un échange&nbsp;↗</span></div>'
            ) if b.get("url") else ""
    thumb_html = (f'<img src="{uri(thumb)}" style="position:absolute;left:{(SW - TW) // 2}px;top:{HEAD}px;width:{TW}px;height:{TH}px;'
                  f'border-radius:{R_OUT - 14}px">') if thumb else ""
    page = f"""<html><head><meta charset="utf-8"><style>{style}body{{width:{W}px;height:{end}px}}.lg svg{{filter:brightness(0);height:30px}}</style></head><body>
<div style="position:relative;width:{SW}px;height:{end}px;margin:0 {ox}px">
<svg width="{SW}" height="{end}" style="position:absolute;left:0;top:0"><path d="{shape}" fill="#fff"/></svg>
<div style="position:absolute;left:30px;top:16px;width:540px;height:64px;display:flex;justify-content:space-between;align-items:center">
 <div><span class=lg>{logo_svg}</span><div style="font:800 15px/1 M;color:#000;margin-top:9px;letter-spacing:.01em">AI Corner</div></div>
 <span class=m style="background:#fff;color:#000;border:1.5px solid #000;border-radius:20px;padding:10px 15px">EP.{re.sub(r"\D", "", str(mail.get("episode", "")))}&nbsp; ↗</span></div>
{thumb_html}
<div style="position:absolute;left:40px;top:{TXT}px;width:520px">
 <div class=m style="color:#6B6B6B">{esc(host)} × {esc(mail.get("guest", ""))} · {esc(mail.get("company", ""))}</div>
 <div style="font:800 36px/1.06 M;letter-spacing:-.025em;color:#000;margin-top:16px">{esc(t["title"])}</div>
 <div style="font:17px/1.5 Arial;color:#000;margin-top:20px">{esc(t["hook"])}</div>
 <div style="font:14.5px/1.6 Arial;color:#5A5A5A;margin-top:12px">{esc(t["intro"])}</div>
 <div style="margin-top:26px"><span class=btn>{esc((cfg.get("button") or "Regarder l'épisode").capitalize())} &nbsp;↗</span></div></div>
{_item(30, o + 44, prog[0])}{_item(330, y["r1s"] + 50, prog[1])}{_item(30, y["l2s"] + 54, prog[2])}{_item(330, y["r2s"] + 50, prog[3])}
{_icon_cell(brand, 450, o + 100, prog[0])}{_icon_cell(brand, 150, (y["l1e"] + y["l2s"]) // 2, prog[1])}{_icon_cell(brand, 450, (y["r1e"] + y["r2s"]) // 2, prog[2])}{_icon_cell(brand, 150, (y["l2e"] + o + STEP) // 2, prog[3])}
<div style="position:absolute;left:40px;top:{o + STEP + 40}px;width:520px">
 <div style="font:17px/1.55 Arial;color:#000">{esc(t["closing"])}</div>
 <div style="margin-top:18px;font:700 15px/1.4 M;color:#000">{esc(host)}</div><div class=m style="color:#6B6B6B;margin-top:6px">CEO · AI Partners</div>
 <div style="height:1px;background:#E2E2E2;margin:26px 0"></div>{book}</div>
<div style="position:absolute;left:40px;top:{o + STEP + H1 - 14}px;width:520px;height:1px;background:#E2E2E2"></div>
<div style="position:absolute;left:0;top:{o + STEP + H1 + 14}px;width:{SW}px;text-align:center"><div style="font:800 24px/1.1 M;color:#000">Écoutez AI Corner partout</div>
 <div class=m style="color:#6B6B6B;margin-top:12px">{labels}</div></div>
</div></body></html>"""
    full = shot(page, W * 2, end * 2, d / "_mosaique_complet.png")
    im = Image.open(full).convert("RGB")
    t_cut = (HEAD + TH + 16) * 2
    pal = lambda r: r.convert("P", palette=Image.Palette.ADAPTIVE, colors=256)       # noqa: E731
    # tranches de texte : 256 couleurs (noir, blanc, gris et anticrénelage) ; la miniature (photo) reste en JPEG
    pal(im.crop((0, 0, W * 2, HEAD * 2))).save(d / "mosaique_entete.png", optimize=True)
    im.crop((0, HEAD * 2, W * 2, t_cut)).save(d / "mosaique_miniature.jpg", quality=90)
    pal(im.crop((0, t_cut, W * 2, (o + STEP) * 2))).save(d / "mosaique_haut.png", optimize=True)
    pal(im.crop((0, (o + STEP) * 2, W * 2, fin * 2))).save(d / "mosaique_fin.png", optimize=True)
    full.unlink(missing_ok=True)
    out.update(mz_header=d / "mosaique_entete.png", mz_thumb=d / "mosaique_miniature.jpg", mz_main=d / "mosaique_haut.png",
               mz_close=d / "mosaique_fin.png")

    # --- bas de la forme : rangée de logos cliquables (EN COULEUR) puis pied arrondi
    cap = (f'<html><head><meta charset="utf-8"><style>{style}body{{width:{W}px;height:70px}}</style></head><body>'
           f'<div style="margin:0 40px;height:30px;background:#fff;border-radius:0 0 {R_OUT}px {R_OUT}px"></div></body></html>')
    out["mz_plat_cap"] = shot(cap, W * 2, 70 * 2, d / "mosaique_plateformes_bas.png")
    for p in platforms:
        key = (p.get("name") or "").lower()
        src = brand.asset(f"platforms/{key}.svg")
        if not src:
            continue
        glyph = src.read_text(encoding="utf-8")
        color = {"youtube": "#FF0000", "spotify": "#1DB954"}.get(key)       # couleurs officielles ; Ausha garde son violet
        if color:
            glyph = glyph.replace("<svg ", f"<svg fill='{color}' ", 1)
        pg = (f'<html><head><meta charset="utf-8"><style>{style.replace("background:#000", "background:#fff")}body{{width:100px;height:100px;zoom:2}}</style></head><body>'
              f'<div style="margin:14px;width:72px;height:72px;border-radius:22px;border:1px solid #D9D9D9;display:flex;align-items:center;justify-content:center">'
              f'<div style="width:34px;height:34px">{glyph.replace("<svg", "<svg width=34 height=34", 1)}</div></div></body></html>')
        out[f"mz_plat_{key}"] = shot(pg, 200, 200, d / f"mosaique_{key}.png")
    return out


def _slice(c: dict, key: str, alt: str, href: str) -> str:
    return (f'<tr><td bgcolor="#000000" style="font-size:0;line-height:0"><a href="{esc(href)}" style="text-decoration:none"><img src="{c["rel"](key)}" '
            f'width="{W}" alt="{esc(alt)}" style="display:block;width:100%;max-width:{W}px;border:0"></a></td></tr>')


def mosaique(c: dict) -> str:
    """Gabarit mosaïque : noir et blanc, une forme blanche continue (voir l'en-tête du module)."""
    t = short_texts({"program": c["program"], "hook": c["hook"], "intro": c["intro"], "closing": c["closing"], "theme": c["theme"]}, c["title"])
    b = c.get("booking") or {}
    alt_main = " ".join([t["title"], t["hook"], t["intro"], "Regarder l'épisode."] +
                        [f'{p["time"]} {p["title"]} : {p["text"]}' for p in t["program"]])
    alt_close = " ".join([t["closing"], c["host_name"], b.get("title") or "", b.get("button") or ""])
    plats = [p for p in c.get("platforms") or [] if p.get("url") and c["img"].get("mz_plat_" + (p.get("name") or "").lower())]

    def cell(p):
        key = (p["name"] or "").lower()
        return (f'<td align="center" valign="middle" width="100" style="padding:0 4px;font-size:0;line-height:0"><a href="{esc(p["url"])}" style="text-decoration:none">'
                f'<img src="{c["rel"]("mz_plat_" + key)}" width="100" height="100" alt="{esc(p["name"].capitalize())}" '
                f'style="display:block;width:100px;height:100px;border:0"></a></td>')
    body = '<tr><td bgcolor="#000000" height="24" style="font-size:0;line-height:0;height:24px">&nbsp;</td></tr>'
    if c["img"].get("mz_header"):
        body += _slice(c, "mz_header", f"AI Corner by AI Partners, épisode {c['episode']}", c["url"])
    if c["img"].get("mz_thumb"):
        body += _slice(c, "mz_thumb", c["title"], c["url"])
    body += _slice(c, "mz_main", alt_main, c["url"])
    body += _slice(c, "mz_close", alt_close, b.get("url") or c["url"])
    if plats:
        body += (f'<tr><td bgcolor="#000000" align="center" style="padding:0 40px"><table role="presentation" width="100%" bgcolor="#FFFFFF" cellpadding="0" cellspacing="0">'
                 f'<tr><td align="center" bgcolor="#FFFFFF" style="padding:0 0 4px"><table role="presentation" align="center" cellpadding="0" cellspacing="0">'
                 f'<tr>{"".join(cell(p) for p in plats)}</tr></table></td></tr></table></td></tr>')
        if c["img"].get("mz_plat_cap"):
            body += (f'<tr><td bgcolor="#000000" style="font-size:0;line-height:0"><img src="{c["rel"]("mz_plat_cap")}" width="{W}" alt="" '
                     f'style="display:block;width:100%;max-width:{W}px;border:0"></td></tr>')
    return shell(c, "#000000", body, "#000000", "#8A8A8A", card_bg="#000000")
