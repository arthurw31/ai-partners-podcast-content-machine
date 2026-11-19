"""Miniatures de shorts : planche d'essai (Arthur, 19/11/2026 : « par défaut la plateforme prend la première image du short comme
miniature, c'est mauvais des fois ; un visuel très simple : une image du short floutée en fond, le thème du short écrit dessus, le logo
AI Partners et un "extrait du podcast AI Corner" ; propose-moi une planche avec plusieurs designs »).

Cinq designs, 1080 x 1920, rendus par Chrome (Metropolis) sur une image du short floutée. Texte et logo gardés dans la ZONE SÛRE centrale
(la grille de profil Instagram recadre au centre en 3:4 ; TikTok met ses boutons en bas à droite).
EXPLORATION : non branché sur le pipeline. Sortie : EPISODES/<marque>/<épisode>/travail/miniatures_shorts/.
Lancer : python -m clipper.lab_miniatures_shorts [--episode E23]
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "MARQUES" / "ai-corner"
NAVY, BLUE, YELLOW = "#151D53", "#258AF3", "#F2E86D"
W, H = 1080, 1920

# mot-clé de chaque short (style des sous-titres « variante B » pour le design E)
MOTS_CLES = {1: "humaine", 2: "gouverner", 3: "Copilot", 5: "charte IA"}


def _uri(p: Path) -> str:
    return p.resolve().as_uri()


def _fonts() -> str:
    f = BRAND / "assets" / "fonts"
    return "".join(f'@font-face{{font-family:{n};src:url("{_uri(f / fn)}");font-weight:{w}}}' for n, fn, w in [
        ("M", "Metropolis-Regular.ttf", 400), ("M", "Metropolis-Bold.ttf", 700), ("M", "Metropolis-ExtraBold.ttf", 800),
        ("L", "Lora-Italic-VF.ttf", 600)])


def _shot(html: str, out: Path) -> Path:
    import tempfile

    from .thumbnail import _browser
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        page = Path(td) / "p.html"
        page.write_text(html, encoding="utf-8")
        subprocess.run([_browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                        f"--user-data-dir={Path(td) / 'prof'}", "--virtual-time-budget=5000", "--force-device-scale-factor=1",
                        f"--window-size={W},{H}", f"--screenshot={out}", page.as_uri()],
                       capture_output=True, timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return out


def _frame(mp4: Path, t: float, out: Path) -> Path:
    if not out.exists():
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(mp4), "-frames:v", "1", "-q:v", "2", str(out)],
                       check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return out


def _fr(t: str) -> str:
    """Typographie française : espace insécable dans les nombres (« 1 000 ») et avant « : ? ! »."""
    import re
    nbsp = " "
    t = re.sub(r"(\d) (\d{3})", lambda m: m.group(1) + nbsp + m.group(2), t)
    return re.sub(r" ([:?!])", lambda m: nbsp + m.group(1), t)


def _accent(titre: str, mot: str, style: str) -> str:
    from html import escape
    t = escape(titre)
    m = escape(mot)
    return t.replace(m, f"<span style='{style}'>{m}</span>", 1) if m in t else t


def design(lettre: str, fond: Path, titre: str, mot: str) -> str:
    logo = _uri(BRAND / "assets" / "logo.png")
    bg = (f"<img src='{_uri(fond)}' style='position:absolute;inset:-60px;width:{W + 120}px;height:{H + 120}px;object-fit:cover;"
          f"filter:blur(26px) saturate(1.05)'>")
    label = "EXTRAIT DU PODCAST AI CORNER"
    base = f"<html><head><meta charset='utf-8'><style>{_fonts()}body{{margin:0}}.c{{position:relative;width:{W}px;height:{H}px;overflow:hidden;font-family:M}}</style></head><body><div class='c'>{bg}"
    from html import escape
    t = escape(titre)
    if lettre == "A":      # centré, voile sombre, pastille « extrait », logo en bas
        return base + (f"<div style='position:absolute;inset:0;background:rgba(8,12,40,.55)'></div>"
                       f"<div style='position:absolute;left:90px;right:90px;top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;gap:46px'>"
                       f"<div style='border:3px solid #fff;border-radius:999px;padding:14px 34px;color:#fff;font-weight:700;font-size:30px;letter-spacing:.12em'>{label}</div>"
                       f"<div style='color:#fff;font-weight:800;font-size:96px;line-height:1.08;letter-spacing:-.02em;text-wrap:balance'>{t}</div>"
                       f"<img src='{logo}' style='height:58px;margin-top:20px'></div></div></body></html>")
    if lettre == "B":      # titre sur bandeaux bleus (code de la miniature YouTube), logo en haut
        return base + (f"<div style='position:absolute;inset:0;background:linear-gradient(to bottom,rgba(8,12,40,.55),rgba(8,12,40,.25) 40%,rgba(8,12,40,.6))'></div>"
                       f"<img src='{logo}' style='position:absolute;left:50%;top:300px;transform:translateX(-50%);height:62px'>"
                       f"<div style='position:absolute;left:80px;right:80px;top:640px;text-align:center'>"
                       f"<span style='background:{BLUE};color:#fff;font-weight:800;font-size:88px;line-height:1.32;letter-spacing:-.015em;padding:4px 22px;"
                       f"-webkit-box-decoration-break:clone;box-decoration-break:clone;border-radius:14px'>{t}</span></div>"
                       f"<div style='position:absolute;left:0;right:0;bottom:330px;text-align:center;color:#fff;font-weight:700;font-size:32px;letter-spacing:.14em'>{label}</div>"
                       f"</div></body></html>")
    if lettre == "C":      # carte blanche au centre, titre bleu nuit
        return base + (f"<div style='position:absolute;inset:0;background:rgba(8,12,40,.35)'></div>"
                       f"<div style='position:absolute;left:90px;right:90px;top:50%;transform:translateY(-50%);background:#fff;border-radius:44px;padding:70px 64px 64px 64px;"
                       f"box-shadow:0 30px 80px rgba(5,8,40,.45)'>"
                       f"<div style='color:{BLUE};font-weight:700;font-size:28px;letter-spacing:.14em;margin-bottom:30px'>{label}</div>"
                       f"<div style='color:{NAVY};font-weight:800;font-size:84px;line-height:1.08;letter-spacing:-.02em'>{t}</div>"
                       f"<div style='height:4px;width:90px;background:{NAVY};margin:46px 0 40px 0'></div>"
                       f"<img src='{_uri(BRAND / 'assets' / 'aip_logo_black.png')}' style='height:52px'></div></div></body></html>")
    if lettre == "D":      # bas d'écran : dégradé bleu nuit, titre aligné à gauche, logo + mention en haut
        return base + (f"<div style='position:absolute;inset:0;background:linear-gradient(to bottom,rgba(8,12,40,.45) 0%,rgba(8,12,40,0) 30%,rgba(16,24,80,.88) 62%,{NAVY} 100%)'></div>"
                       f"<img src='{logo}' style='position:absolute;left:90px;top:300px;height:56px'>"
                       f"<div style='position:absolute;left:90px;right:90px;top:1000px'>"
                       f"<div style='color:{BLUE};font-weight:700;font-size:30px;letter-spacing:.14em;margin-bottom:30px'>{label}</div>"
                       f"<div style='height:6px;width:110px;background:#fff;margin-bottom:38px'></div>"
                       f"<div style='color:#fff;font-weight:800;font-size:92px;line-height:1.08;letter-spacing:-.02em'>{t}</div></div></div></body></html>")
    # E : style des sous-titres (capitales Metropolis Bold, mot-clé Lora italique jaune), ombre douce
    acc = _accent(titre, mot, f"font-family:L;font-style:italic;font-weight:600;text-transform:none;color:{YELLOW};font-size:1.14em")
    return base + (f"<div style='position:absolute;inset:0;background:rgba(8,12,40,.42)'></div>"
                   f"<img src='{logo}' style='position:absolute;left:50%;top:300px;transform:translateX(-50%);height:58px'>"
                   f"<div style='position:absolute;left:80px;right:80px;top:0;bottom:0;display:flex;align-items:center;justify-content:center;text-align:center'>"
                   f"<div style='color:#fff;font-weight:700;font-size:92px;line-height:1.12;text-transform:uppercase;letter-spacing:.02em;"
                   f"text-shadow:0 4px 30px rgba(0,0,0,.55),0 2px 8px rgba(0,0,0,.4);text-wrap:balance'>{acc}</div></div>"
                   f"<div style='position:absolute;left:0;right:0;bottom:330px;text-align:center;color:#fff;font-weight:700;font-size:30px;letter-spacing:.14em;"
                   f"text-shadow:0 2px 12px rgba(0,0,0,.5)'>{label}</div></div></body></html>")


def main(episode: str = "E23") -> Path:
    from PIL import Image, ImageDraw, ImageFont
    ep = next((ROOT / "EPISODES" / "ai-corner").glob(f"{episode}_*"))
    out = ep / "travail" / "miniatures_shorts"
    out.mkdir(parents=True, exist_ok=True)
    clips = json.loads((ep / "travail" / "clips.json").read_text(encoding="utf-8"))["clips"]
    shorts = []
    dossiers = sorted((ep / "LIVRABLES" / "2_shorts").glob("short_*"), key=lambda d: int(d.name.split("_")[1]))
    for i, d in enumerate(dossiers):          # LIVRABLES suit l'ordre de clips.json (short_5 = 4e clip)
        n = int(d.name.split("_")[1])
        mp4 = next(d.glob("*.mp4"))
        titre = _fr(clips[i]["title"]) if i < len(clips) else d.name
        shorts.append((n, _frame(mp4, 14.0, out / f"fond_short_{n}.jpg"), titre))
    lettres = "ABCDE"
    files = {}
    for n, fond, titre in shorts:
        for l in lettres:
            files[(n, l)] = _shot(design(l, fond, titre, MOTS_CLES.get(n, "")), out / f"short_{n}_design_{l}.png")
    # planche : une ligne par short, une colonne par design
    tw, th = 270, 480
    sheet = Image.new("RGB", (60 + tw * len(lettres) + 20 * (len(lettres) - 1) + 40, 90 + (th + 30) * len(shorts)), "white")
    dr = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype(str(BRAND / "assets" / "fonts" / "Metropolis-Bold.ttf"), 34)
    except OSError:
        font = None
    for j, l in enumerate(lettres):
        dr.text((60 + j * (tw + 20) + tw // 2 - 12, 30), l, fill=NAVY, font=font)
    for i, (n, _, _) in enumerate(shorts):
        dr.text((12, 90 + i * (th + 30) + th // 2 - 20), str(n), fill=NAVY, font=font)
        for j, l in enumerate(lettres):
            sheet.paste(Image.open(files[(n, l)]).convert("RGB").resize((tw, th), Image.Resampling.LANCZOS), (60 + j * (tw + 20), 90 + i * (th + 30)))
    p = out / "planche_designs.jpg"
    sheet.save(p, quality=90)
    return p


if __name__ == "__main__":
    print(main(sys.argv[sys.argv.index("--episode") + 1] if "--episode" in sys.argv else "E23"))
