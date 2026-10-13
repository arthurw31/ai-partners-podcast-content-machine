"""Dossier LIVRABLES d'un épisode : les versions finales de chaque livrable, rangées et nommées clairement, prêtes à être
copiées telles quelles sur le Drive (Arthur, 13/10/2026 : « une fois tout fait, un dossier qui ait toutes les versions
finales de chaque livrable, pour qu'on n'ait plus qu'à le copier dans le Drive »).

`python -m clipper livraison --brand <m> --input <E>.mp4` -> EPISODES/<marque>/<épisode>/LIVRABLES/ :
    LISEZMOI.md              quoi publier où, titre, état des contrôles, ce qui manque
    1_episode_youtube/       épisode .mp4 · miniature.jpg / _HD.png · titre_et_description.md
    2_shorts/                short_N_<titre>.mp4 + short_N_post_linkedin.md
    3_carrousel_linkedin/    carrousel.pdf · slides/ · post_linkedin.md
    4_newsletter/            email.html · email.txt · objet.txt · apercu.png · images/
    5_teaser/                teaser .mp4

Le pipeline n'écrit JAMAIS dans LIVRABLES : seule cette commande le fait, à partir de travail/. Chaque élément est contrôlé
(QA OK, miniature et titre validés par l'équipe, carrousel / newsletter / posts plus récents que les choix dont ils
dépendent) ; ce qui n'est pas prêt est copié quand même s'il existe, mais signalé « À REVOIR » dans LISEZMOI.md.
On relance la commande après chaque retouche : LIVRABLES est refait (ce ne sont que des copies).
"""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path

from .config import episode_home

OK, WARN, MISSING = "OK", "À REVOIR", "MANQUANT"


def _qa_status(f: Path) -> str:
    if not f.exists():
        return ""
    m = re.search(r"—\s*(OK|ATTENTION|ÉCHEC)\s*$", f.read_text(encoding="utf-8").splitlines()[0])
    return m.group(1) if m else ""


def _copy(src: Path, dst: Path, done: list) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists() or dst.stat().st_size != src.stat().st_size or dst.stat().st_mtime < src.stat().st_mtime:
        shutil.copy2(src, dst)
    done.append(dst)


def _slug(s: str, n: int = 50) -> str:
    from .compose import slugify
    return slugify(s, n)


def build(brand, video: Path, work: Path) -> tuple[Path, list[tuple[str, str, str]]]:
    """Construit LIVRABLES/ ; renvoie (dossier, lignes [(statut, livrable, détail)])."""
    home = episode_home(work)
    out = home / "LIVRABLES"
    out.mkdir(exist_ok=True)
    rows: list[tuple[str, str, str]] = []
    done: list[Path] = []
    stem = video.stem
    clips = json.loads((work / "clips.json").read_text(encoding="utf-8")) if (work / "clips.json").exists() else {"clips": []}

    # ---- titre et miniature (validations de l'équipe)
    tv = work / "titres" / "titre_valide.json"
    title = json.loads(tv.read_text(encoding="utf-8")) if tv.exists() else {}
    rows.append((OK if title else WARN, "titre YouTube", title.get("youtube", "pas encore validé (`titles --pick N`)")))
    mc = work / "miniatures" / "miniature_choisie.json"
    thumb = work / "miniatures" / "miniature_finale.jpg"
    thumb_t = thumb.stat().st_mtime if thumb.exists() else 0

    # ---- 1. épisode YouTube
    d1 = out / "1_episode_youtube"
    epi = work / "episode" / f"{stem}_episode.mp4"
    if epi.exists():
        _copy(epi, d1 / epi.name, done)
        st = _qa_status(work / "qa" / "episode.md")
        rows.append((OK if st == "OK" else WARN, "épisode complet", f"{epi.name} — contrôle qualité : {st or 'pas fait'}"))
    else:
        rows.append((MISSING, "épisode complet", "pas encore rendu en 1080p (`episode-render`)"))
    if thumb.exists() and mc.exists():
        _copy(thumb, d1 / "miniature.jpg", done)
        hd = thumb.with_name("miniature_finale_HD.png")
        if hd.exists():
            _copy(hd, d1 / "miniature_HD.png", done)
        rows.append((OK, "miniature", "choisie par l'équipe"))
    else:
        rows.append((MISSING, "miniature", "pas encore choisie (`thumbnail --pick N`)"))
    desc = work / "episode" / "description_youtube.md"
    if desc.exists():
        txt = desc.read_text(encoding="utf-8")
        ok_t = bool(title) and title.get("youtube", "") in txt
        (d1 / "titre_et_description.md").write_text(txt, encoding="utf-8")
        done.append(d1 / "titre_et_description.md")
        rows.append((OK if ok_t else WARN, "titre + description YouTube",
                     "titre validé repris" if ok_t else "la description n'a pas le titre validé : relancer `episode-plan`"))

    # ---- 2. shorts (avec outro) + posts
    d2 = out / "2_shorts"
    for c in clips.get("clips", []):
        n = int(c["index"])
        found = sorted((work / "livrables").glob(f"clip_{n:02d}_*_9x16.mp4")) if (work / "livrables").exists() else []
        mp4 = found[0] if found else work / "livrables" / f"clip_{n:02d}_9x16.mp4"
        label = c.get("hook_title") or c.get("title", "")
        if not mp4.exists():
            rows.append((MISSING, f"short {n}", f"« {label} » : pas encore livré (`render` puis `outro`)"))
            continue
        dst = d2 / f"short_{n}_{_slug(label, 45)}.mp4"
        _copy(mp4, dst, done)
        st = _qa_status(work / "qa" / f"clip_{n:02d}.md")
        problems = []
        if st == "ÉCHEC":
            problems.append("contrôle qualité en ÉCHEC")
        if mp4.stat().st_mtime < thumb_t:
            problems.append("outro faite AVANT le choix de la miniature (`outro --only N`)")
        rows.append((WARN if problems else OK, f"short {n}", f"« {label} » ({st or 'qa ?'})" + (" — " + "; ".join(problems) if problems else "")))
        post = next(iter(sorted((work / "posts").glob(f"clip_{n:02d}_*.md"))), None) if (work / "posts").exists() else None
        if post:
            _copy(post, d2 / f"short_{n}_post_linkedin.md", done)
            stale = post.stat().st_mtime < mp4.stat().st_mtime - 6 * 3600
            rows.append((WARN if stale else OK, f"post LinkedIn short {n}",
                         "écrit avant le dernier montage du short : à relire (`posts --only N --force`)" if stale else "à jour"))
        else:
            rows.append((MISSING, f"post LinkedIn short {n}", "pas encore rédigé (`posts`)"))

    # ---- 3. carrousel LinkedIn
    d3 = out / "3_carrousel_linkedin"
    car = work / "carrousel"
    final = car / "final"
    style = ((brand.cfg.get("carousel") or {}).get("style") or "")
    src = final if final.exists() and any(final.glob("*.pdf")) else (car / style if style and (car / style).exists() else None)
    if src:
        pdf = next(iter(sorted(src.glob("*.pdf"))))
        _copy(pdf, d3 / "carrousel.pdf", done)
        for p in sorted(src.glob("slide_*.png")):
            _copy(p, d3 / "slides" / p.name, done)
        post = src / "post_linkedin.md" if (src / "post_linkedin.md").exists() else car / "post_linkedin.md"
        if post.exists():
            _copy(post, d3 / "post_linkedin.md", done)
        validated = src == final
        rows.append((OK if validated else WARN, "carrousel LinkedIn",
                     f"style {style or '?'}" + ("" if validated else " — pas encore validé par l'équipe (`carousel --final STYLE`)")))
    else:
        rows.append((MISSING, "carrousel LinkedIn", "pas encore fait (`carousel`)"))

    # ---- 4. newsletter
    d4 = out / "4_newsletter"
    nl = work / "newsletter"
    src = nl / "final" if (nl / "final").exists() else nl
    if (src / "email.html").exists():
        for f in ("email.html", "email.txt", "objet.txt", "apercu.png", "email_a_envoyer.html"):
            g = src / f if (src / f).exists() else nl / f
            if g.exists():
                _copy(g, d4 / f, done)
        for p in sorted((src / "images").glob("*")) if (src / "images").exists() else []:
            _copy(p, d4 / "images" / p.name, done)
        problems = []
        if src != nl / "final":
            problems.append("pas encore validée (`newsletter --final`, après la mise en ligne YouTube)")
        yt = src / "images" / "episode_youtube.jpg"
        if thumb.exists() and yt.exists() and (src / "email.html").stat().st_mtime < thumb_t:
            problems.append("faite AVANT le choix de la miniature : image à refaire (`newsletter --render`, ou `newsletter --force` pour réécrire le texte)")
        rows.append((WARN if problems else OK, "newsletter", "; ".join(problems) or "à jour"))
    else:
        rows.append((MISSING, "newsletter", "pas encore faite (`newsletter`)"))

    # ---- 5. teaser
    t = work / "episode" / f"{stem.split('_')[0]}_teaser_final.mp4"
    if t.exists():
        _copy(t, out / "5_teaser" / "teaser.mp4", done)
        rows.append((OK, "teaser", "inclus au début de l'épisode ; ici à part si besoin"))

    # ---- ménage : ce qui n'est plus un livrable actuel (copies seulement)
    keep = {p.resolve() for p in done}
    for f in sorted(out.rglob("*"), reverse=True):
        if f.is_file() and f.resolve() not in keep and f.name != "LISEZMOI.md":
            f.unlink()
        elif f.is_dir() and not any(f.iterdir()):
            f.rmdir()

    # ---- LISEZMOI
    icon = {OK: "✅", WARN: "⚠️", MISSING: "❌"}
    lines = [f"# {title.get('youtube') or stem} — livrables", "",
             f"Généré le {datetime.now():%d/%m/%Y à %H:%M} par `python -m clipper livraison`. Ce dossier ne contient que des",
             "copies des versions finales : on peut le copier tel quel sur le Drive. À relancer après chaque retouche.", "",
             "| | Livrable | État |", "|---|---|---|"]
    lines += [f"| {icon[s]} | {what} | {detail.replace('|', '¦')} |" for s, what, detail in rows]
    lines += ["", "## Où publier", "",
              "- `1_episode_youtube/` : la vidéo, la miniature et le titre + la description (avec les chapitres) sur YouTube.",
              "- `2_shorts/` : chaque short sur LinkedIn / Instagram / TikTok / YouTube Shorts, avec son post.",
              "- `3_carrousel_linkedin/` : le PDF en document LinkedIn, avec `post_linkedin.md` (le lien est dans le post).",
              "- `4_newsletter/` : le mail de Thomas (`email.html`, objet dans `objet.txt`) — à envoyer après la mise en ligne.",
              "- `5_teaser/` : le teaser seul (il est déjà au début de l'épisode)."]
    (out / "LISEZMOI.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out, rows
