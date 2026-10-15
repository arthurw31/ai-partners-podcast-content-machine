"""Relecture critique par un Claude SANS le contexte de la conversation, juste avant de montrer un livrable à l'équipe.

Demande d'Arthur (12/10/2026) : « est-ce que tu fais spawn un sous-agent qui n'a pas le contexte de la conversation
principale ? Ça permettrait d'avoir un regard neuf et plus critique ; il faudrait un modèle assez performant » puis
« vas-y, attention à la consommation de tokens ».

- Le contrôle `qa` (code) MESURE (coupes, volume, sous-titres réécoutés) ; ce relecteur JUGE ce qui demande un œil : sens,
  cadrage, lisibilité, fidélité à l'épisode, respect des règles validées. Il ne voit pas la vidéo et ne l'entend pas :
  il reçoit la planche d'images, le texte « ce qu'on entend » (‖ = raccords), le rapport `qa` et la checklist du type
  de livrable (`config/review_checklist.md`). Rien de la conversation ni de « ce que l'on voulait faire ».
- Il cherche des défauts : chaque défaut doit citer un instant, une slide ou un passage ET la règle enfreinte, sinon il
  est écarté. Défaut prouvé -> boucle « à corriger » ; remarque de goût -> remontée telle quelle à l'équipe.
- Tokens : un seul appel par livrable, entrées compactes (planche réduite en JPEG, rapport `qa` et section de checklist
  seulement), réponse courte (8 défauts max) ; un livrable inchangé n'est jamais relu deux fois (empreinte des entrées).
  Modèle fort par défaut (`review.model`, Opus) : c'est le travail où la finesse compte.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path

from PIL import Image
from rich.console import Console

console = Console()
ROOT = Path(__file__).resolve().parent.parent
CHECKLIST = ROOT / "config" / "review_checklist.md"
MAX_SIDE = 1600                     # images réduites : assez pour juger le cadrage et la lisibilité, peu de tokens

PROMPT = """Tu es le RELECTEUR CRITIQUE indépendant d'une équipe de montage. Tu n'as pas participé au travail et tu ne
connais pas les intentions de l'auteur : tu juges uniquement le livrable, avec un regard neuf et exigeant, avant qu'il
soit montré à l'équipe marketing. Ton rôle est de TROUVER les défauts, pas de valider.

Règles validées par l'équipe, à faire respecter :
{rules}

Ce que tu reçois : {inputs}. Les lignes [OK] du rapport de contrôle automatique sont des mesures fiables : ne les
conteste que si ce que tu vois ou lis les contredit clairement. Les passages d'épisode fournis sont des extraits exacts :
un fait ou une citation présent dans N'IMPORTE LEQUEL de ces extraits est prouvé, même s'il est rattaché à une autre
slide ; « inventé » = absent de tous les extraits, ou qui les contredit.

Ne signale QUE ce que tu peux prouver avec ces éléments : chaque défaut cite OÙ (instant m:ss, n° de slide, n° d'image de
la planche ou passage exact) et QUELLE règle il enfreint. 8 défauts au plus, du plus grave au moins grave. Une remarque
de goût sans règle enfreinte va dans "taste" (3 au plus). Pas de compliments.

Réponds UNIQUEMENT en JSON :
{{"verdict": "OK" ou "A_CORRIGER", "issues": [{{"severity": "ÉCHEC" ou "ATTENTION", "where": "…", "rule": "…",
  "problem": "…", "fix": "correction concrète"}}], "taste": ["…"]}}"""


def checklist(kind: str) -> str:
    """Sections « commun » + celle du type de livrable seulement (économie de tokens)."""
    txt = CHECKLIST.read_text(encoding="utf-8") if CHECKLIST.exists() else ""
    secs = dict(re.findall(r"(?ms)^## (\w+)\n(.*?)(?=^## |\Z)", txt))
    return (secs.get("commun", "") + secs.get(kind, "")).strip()


def _small(src: Path, dst: Path) -> Path:
    im = Image.open(src).convert("RGB")
    im.thumbnail((MAX_SIDE, MAX_SIDE * 3), Image.Resampling.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, quality=80)
    return dst


def _non_ok(md: str) -> str:
    """Rapport qa compact : titre, lignes non OK, et le texte « ce qu'on entend » (les lignes OK sont résumées)."""
    keep, n_ok = [], 0
    for line in md.splitlines():
        if line.startswith("- [OK]"):
            n_ok += 1
        elif line.strip():
            keep.append(line)
    return "\n".join(keep) + f"\n({n_ok} contrôle(s) automatique(s) OK, non détaillés)"


def _passages(ep: Path, items: list[tuple[str, str, float | None]]) -> str:
    """Extraits EXACTS de la transcription autour de chaque preuve / citation (1 phrase avant, 2 après) : sans eux, le
    relecteur prenait une citation vérifiée ou un fait dit ailleurs pour une invention (test du 12/10/2026, carrousel E22)."""
    from .titles import find_evidence
    tf = ep / "transcript.json"
    if not tf.exists():
        return ""
    segs = json.loads(tf.read_text(encoding="utf-8"))["segments"]
    from .titles import _digits, norm
    out, seen = [], set()
    for label, quote, t in items:
        if quote.startswith("#"):                  # chiffre affiché : le passage où il est dit
            num = quote[1:]
            hit = next((s for s in segs if num in re.sub(r"[  .,]", "", _digits(norm(s["text"])))), None)
            if hit is None:
                out.append(f"[{label}] (chiffre {num} introuvable dans la transcription)")
                continue
            start, score = float(hit["start"]), 1.0
        elif not quote or len(quote) < 12:
            continue
        else:
            start, score = find_evidence(segs, quote, t)
        if start is None or score < 0.5:
            out.append(f"[{label}] (passage introuvable dans la transcription) « {quote[:120]} »")
            continue
        i = next(k for k, s in enumerate(segs) if float(s["start"]) == start)
        lo, hi = max(0, i - 1), min(len(segs), i + 3)
        if (lo, hi) in seen:
            continue
        seen.add((lo, hi))
        t0 = float(segs[lo]["start"])
        out.append(f"[{label}] {int(t0) // 60}:{int(t0) % 60:02d} " + " ".join(s["text"].strip() for s in segs[lo:hi]))
    return ("\n\nPASSAGES EXACTS DE L'ÉPISODE (transcription, autour de chaque preuve et de chaque citation) :\n"
            + "\n".join(out)) if out else ""


def _claims(label: str, obj) -> list[tuple[str, str, None]]:
    """Chiffres (≥ 2 chiffres) et expressions entre « » d'un texte affiché : on fournit au relecteur le passage où l'épisode
    les dit, sinon il les croit inventés quand ils viennent d'un autre moment que la preuve de la slide."""
    from .titles import _digits
    txt = re.sub(r"\[\[(.+?)\]\]", r"\1", json.dumps(obj, ensure_ascii=False) if not isinstance(obj, str) else obj)
    txt = re.sub(r'"(evidence|quote|t|chapter)": [^,}]*', "", txt)
    out = [(f"{label}, chiffre {n}", "#" + re.sub(r"[  .,]", "", n), None)
           for n in dict.fromkeys(re.findall(r"\d[\d  .,]*\d", _digits(txt)))]
    out += [(f"{label}, « {q[:30]} »", q, None) for q in re.findall(r"«\s*([^»]{12,})\s*»", txt)]
    return out


def short_video(ep: Path, n: int) -> Path | None:
    """La vidéo la plus récente du short (rendu final ou aperçu), sans l'outro."""
    cands = [p for d in ("renders", "apercus") if (ep / d).exists() for p in (ep / d).glob(f"clip_{n:02d}_*.mp4")
             if "avec_outro" not in p.name]
    return max(cands, key=lambda p: p.stat().st_mtime) if cands else None


def dense_sheets(video: Path, work: Path, name: str, fps: float = 2.0, cols: int = 8, tw: int = 200,
                 per_sheet: int = 64) -> list[Path]:
    """Planches SERRÉES de tout le short (Arthur, 15/10/2026 : « une couche agent qui juge avec bon sens la vidéo
    entière ») : une image toutes les 0,5 s + la DERNIÈRE image (figée pendant le fondu vers l'outro), chacune avec son
    instant ; + un gros plan de la bulle-titre (vérifier qu'elle ne touche pas le visage)."""
    import subprocess
    import tempfile

    from PIL import ImageDraw

    from .media import FFMPEG, probe
    d = float(probe(video)["duration"])
    times = [round(i / fps, 2) for i in range(int(d * fps) + 1) if i / fps < d - 0.05] + [round(d - 0.04, 2)]
    tmp = Path(tempfile.mkdtemp(prefix="review_"))
    frames = []
    for i, t in enumerate(times):
        f = tmp / f"f{i:03d}.png"   # PNG : le JPEG de FFmpeg refuse certaines images (plage YUV limitée)
        subprocess.run([FFMPEG, "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                        "-vf", f"scale={tw}:-2", str(f)], check=False)
        if f.exists():
            frames.append((t, Image.open(f).convert("RGB")))
    out = []
    work.mkdir(parents=True, exist_ok=True)
    for s in range(0, len(frames), per_sheet):
        chunk = frames[s:s + per_sheet]
        th = chunk[0][1].height
        sheet = Image.new("RGB", (cols * tw, ((len(chunk) + cols - 1) // cols) * th), "black")
        dr = ImageDraw.Draw(sheet)
        for k, (t, im) in enumerate(chunk):
            x, y = (k % cols) * tw, (k // cols) * th
            sheet.paste(im, (x, y))
            last = s + k == len(frames) - 1
            label = f"{int(t // 60)}:{t % 60:04.1f}" + (" FIN" if last else "")
            dr.rectangle([x, y, x + 74 + (30 if last else 0), y + 16], fill="black")
            dr.text((x + 3, y + 2), label, fill="yellow" if not last else "red")
        p = work / f"{name}_planche_{s // per_sheet + 1}.jpg"
        sheet.save(p, quality=82)
        out.append(p)
    big = work / f"{name}_accroche.jpg"
    subprocess.run([FFMPEG, "-v", "error", "-y", "-ss", "2.0", "-i", str(video), "-frames:v", "1", "-vf", "scale=540:-2",
                    str(big)], check=False)
    if big.exists():
        out.append(big)
    return out


def _short_context(ep: Path, c: dict) -> str:
    """Qui dit quoi (voix reconnues) dans le short, et ce que l'épisode dit JUSTE AVANT le début et JUSTE APRÈS la fin :
    pour juger si l'extrait commence sur une idée complète et s'arrête sur sa chute."""
    tf = ep / "transcript.json"
    dw = ep / "work" / "diarized_words.json"
    segs = c.get("segments") or []
    if not segs or not tf.exists():
        return ""
    names = {"host": "Thomas (animateur)", "guest": f"{c.get('guest') or 'invité'} (invité)"}
    out = []
    if dw.exists():
        ws = json.loads(dw.read_text(encoding="utf-8"))
        lines, cur, buf = [], None, []
        for sg in segs:
            for w in ws:
                if float(sg["start"]) - 0.05 <= w["s"] <= float(sg["end"]):
                    if w.get("spk") != cur and buf:
                        lines.append(f"{names.get(cur, '?')} : {' '.join(buf)}")
                        buf = []
                    cur = w.get("spk")
                    buf.append(w["w"])
        if buf:
            lines.append(f"{names.get(cur, '?')} : {' '.join(buf)}")
        out.append("QUI PARLE DANS LE SHORT (voix reconnues) :\n" + "\n".join(lines))
    tr = json.loads(tf.read_text(encoding="utf-8"))["segments"]
    a, b = float(segs[0]["start"]), float(segs[-1]["end"])
    before = " ".join(s["text"].strip() for s in tr if a - 12 <= float(s["start"]) < a - 0.2)
    after = " ".join(s["text"].strip() for s in tr if b + 0.1 <= float(s["start"]) < b + 12)
    out.append(f"DANS L'ÉPISODE, JUSTE AVANT LE DÉBUT : « …{before[-300:]} »\nJUSTE APRÈS LA FIN : « {after[:300]}… »")
    return "\n\n".join(out)


def gather(ep: Path, kind: str, only: int | None = None) -> tuple[str, str, list[Path], str]:
    """(nom, texte, images, description des entrées) pour un livrable."""
    work = ep / "work" / "review"
    if kind == "short":
        md = ep / "qa" / f"clip_{only:02d}.md"
        sheet = ep / "qa" / f"qa_images_{only:02d}.png"
        if not md.exists():
            raise SystemExit(f"Pas de rapport qa pour le short {only} : lancer d'abord `polish --only {only}` / `qa --only {only} --render`")
        clips = json.loads((ep / "clips.json").read_text(encoding="utf-8")).get("clips", [])
        c = next((x for x in clips if x.get("index") == only), {})
        text = (f"SHORT {only} — bulle-titre (accroche) : « {c.get('hook_title', '')} »\n"
                f"Mots-clés en italique : {', '.join(c.get('keywords') or []) or '(aucun)'}\n\n"
                f"RAPPORT DU CONTRÔLE AUTOMATIQUE :\n{_non_ok(md.read_text(encoding='utf-8'))}\n\n{_short_context(ep, c)}")
        vid = short_video(ep, only)
        imgs = dense_sheets(vid, work, f"short_{only:02d}") if vid else (
            [_small(sheet, work / f"short_{only:02d}.jpg")] if sheet.exists() else [])
        return f"short_{only:02d}", text, imgs, (
            "le rapport du contrôle automatique avec le texte exact de ce qu'on entend (‖ = raccords de montage), qui parle, "
            "ce que l'épisode dit juste avant et juste après l'extrait, l'accroche, des planches d'images de TOUT le short "
            "(une toutes les 0,5 s, instant en jaune, dernière image marquée FIN en rouge : elle reste figée pendant le fondu "
            "vers la carte de fin) et un gros plan de l'image à 2 s (bulle-titre)")
    if kind == "episode":
        md = next((p for p in (ep / "qa" / "episode_apercu.md", ep / "qa" / "episode.md") if p.exists()), None)
        if not md:
            raise SystemExit("Pas de rapport qa de l'épisode : lancer d'abord `episode-render --proxy`")
        sheet = ep / "work" / "qa_episode_images.png"
        audit = ep / "teaser_audit.txt"
        text = f"RAPPORT DU CONTRÔLE AUTOMATIQUE ({md.name}) :\n{md.read_text(encoding='utf-8')}"
        if audit.exists():
            text += f"\n\nTEASER, ce qu'on entend (‖ = raccords) :\n{audit.read_text(encoding='utf-8')[:3000]}"
        imgs = [_small(sheet, work / "episode.jpg")] if sheet.exists() else []
        return "episode", text, imgs, "le rapport du contrôle de l'épisode (raccords réécoutés), le texte du teaser et une planche d'images"
    if kind == "carousel":
        md = ep / "carrousel" / "contenu.md"
        if not md.exists():
            raise SystemExit("Pas de carrousel : lancer d'abord `carousel --pick N`")
        style = next((d for d in ("mix", "usecase", "lignes", "portrait") if (ep / "carrousel" / d / "slide_01.png").exists()), None)
        imgs = []
        if style:                                   # planche des slides du style rendu (une seule image)
            pngs = sorted((ep / "carrousel" / style).glob("slide_*.png"))
            tw, th = 360, 450
            sheet = Image.new("RGB", (tw * min(5, len(pngs)), th * ((len(pngs) + 4) // 5)), "white")
            for k, p in enumerate(pngs):
                sheet.paste(Image.open(p).convert("RGB").resize((tw, th)), ((k % 5) * tw, (k // 5) * th))
            work.mkdir(parents=True, exist_ok=True)
            sheet.save(work / "carousel.jpg", quality=80)
            imgs = [work / "carousel.jpg"]
        content = json.loads((ep / "carrousel" / "contenu.json").read_text(encoding="utf-8"))
        items = []
        for k, s in enumerate(content.get("slides", []), 1):
            ev = s.get("evidence") or {}
            items.append((f"slide {k}, preuve", ev.get("quote", ""), ev.get("t")))
            for q in (s.get("quote"), s.get("text") if s.get("kind") == "quote" else None):
                for part in re.split(r"\[…\]|\[\.\.\.\]|…", q or ""):
                    items.append((f"slide {k}, citation", part.strip(" .,;:«»\""), None))
            items += _claims(f"slide {k}", s)
        text = md.read_text(encoding="utf-8") + _passages(ep, items)
        return "carousel", text, imgs, ("le texte de chaque slide avec sa preuve, les passages exacts de l'épisode autour de "
                                        "chaque preuve et citation, le post LinkedIn, et la planche des slides dans l'ordre")
    if kind == "newsletter":
        f = ep / "newsletter" / "contenu.json"
        if not f.exists():
            raise SystemExit("Pas de mail : lancer d'abord `newsletter`")
        m = json.loads(f.read_text(encoding="utf-8"))
        keys = ("subject", "preheader", "theme", "hook", "intro", "program", "closing", "evidence", "checks")
        text = json.dumps({k: m.get(k) for k in keys}, ensure_ascii=False, indent=1)
        text += _passages(ep, [(f"fait « {e.get('claim', '')[:40]} »", e.get("quote", ""), e.get("t"))
                               for e in m.get("evidence") or []]
                          + _claims("mail", {k: m.get(k) for k in ("subject", "preheader", "theme", "hook", "intro", "program", "closing")}))
        ap = ep / "newsletter" / "apercu.png"
        imgs = [_small(ap, work / "newsletter.jpg")] if ap.exists() else []
        return "newsletter", text, imgs, "le texte du mail avec les preuves de chaque fait, les contrôles automatiques et l'aperçu du mail"
    raise SystemExit(f"Type de livrable inconnu : {kind}")


def review(brand, ep: Path, kind: str, only: int | None = None, force: bool = False, model: str | None = None) -> dict:
    from .llm import ask_json
    name, text, imgs, inputs = gather(ep, kind, only)
    rules = checklist(kind)
    model = model or str((brand.cfg.get("review") or {}).get("model") or "claude-opus-5")
    h = hashlib.sha256((rules + text + model).encode("utf-8"))
    for p in imgs:
        h.update(p.read_bytes())
    key = h.hexdigest()[:16]
    out = ep / "qa" / f"review_{name}.json"
    if out.exists() and not force:
        old = json.loads(out.read_text(encoding="utf-8"))
        if old.get("key") == key:
            console.print(f"[dim]Relecture déjà faite sur ce livrable inchangé ({out.name}) : aucun appel.[/dim]")
            return old
    console.print(f"Relecture critique ({model}, sans contexte) : {name}…")
    data = ask_json(PROMPT.format(rules=rules, inputs=inputs), text, model=model,
                    backend=brand.cfg.selection.llm_backend, max_tokens=2000, images=imgs or None)
    issues = [i for i in data.get("issues") or [] if isinstance(i, dict) and i.get("where") and i.get("rule")][:8]
    for i in issues:
        i["severity"] = "ÉCHEC" if str(i.get("severity", "")).upper().startswith("É") or "ECHEC" in str(i.get("severity", "")).upper() else "ATTENTION"
    verdict = "A_CORRIGER" if any(i["severity"] == "ÉCHEC" for i in issues) else ("ATTENTION" if issues else "OK")
    res = {"deliverable": name, "kind": kind, "model": model, "key": key, "date": date.today().isoformat(),
           "verdict": verdict, "issues": issues, "taste": [t for t in data.get("taste") or [] if t][:3]}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    md = [f"# Relecture critique — {name} — {verdict}", "", f"Relecteur : {model}, sans le contexte du montage.", ""]
    md += [f"- **{i['severity']}** · {i['where']} · {i['problem']} (règle : {i['rule']}) → {i.get('fix', '')}" for i in issues] or ["- Aucun défaut prouvé."]
    if res["taste"]:
        md += ["", "Remarques de goût (à trancher par l'équipe) :"] + [f"- {t}" for t in res["taste"]]
    out.with_suffix(".md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return res
