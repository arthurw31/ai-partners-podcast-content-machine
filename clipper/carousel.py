"""Carrousels LinkedIn tirés d'un épisode : 3 angles -> choix de l'équipe -> slides rédigées et contrôlées -> rendu -> validation.

Demande d'Arthur (12/10/2026) : « créer des carrousels LinkedIn à partir des podcasts, pour donner de la valeur à la
communauté qui nous suit, et sur la dernière slide un call to action pour inciter les gens à bosser avec nous », dans la
charte AI Partners (modèles Canva de l'équipe marketing : carrousels « Use case » et « GEO », 1080 × 1350).
Réponses d'Arthur : Claude propose l'angle (3 propositions, l'équipe en choisit un), en français, CTA « réserver un
échange », 3 styles visuels testés sur E22 puis l'équipe garde le sien (`carousel.style` dans brand.yaml).

1. `propose_angles` : Claude Opus lit la transcription (qui parle, d'après la diarisation) et propose 3 angles de types
   différents, chacun adossé à des passages réels (horodatage + citation exacte, retrouvée dans la transcription) ;
2. `write_slides` (après `--pick N`) : Claude rédige 6 à 8 slides + le post qui accompagne le carrousel ; la slide CTA est
   ajoutée par le framework depuis `carousel.cta` (jamais inventée) ;
3. `check_slides` : longueurs, citations retrouvées mot pour mot, chiffres présents dans l'épisode -> OK / ATTENTION / ÉCHEC ;
4. `render` : HTML (polices et logos de la charte) -> Chrome sans fenêtre -> une PNG par slide + le PDF à téléverser sur
   LinkedIn (format « document ») + une planche de comparaison des styles.
Retouche : modifier `carrousel/contenu.json` puis `carousel --render` (pas de nouvel appel à Claude).
"""
from __future__ import annotations

import html
import json
import re
import subprocess
import tempfile
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw
from rich.console import Console

from .titles import _digits, find_evidence, norm

console = Console()

W, H = 1080, 1350
TYPES = ("lecons", "methode", "idees_recues", "cas", "erreurs", "chiffres")
STYLES = {"usecase": "A · Cas client (modèle « Use case » de l'équipe)",
          "lignes": "B · Lignes (typographique, motif montagne)",
          "portrait": "C · Portrait (photo de l'invité, slides claires)",
          "mix": "Couverture portrait + slides cas client (choix d'Arthur, 12/10/2026)"}
RULES = {"title": 60, "title_hard": 80, "words": 35, "words_hard": 50, "min_slides": 6, "max_slides": 9}
CTA_DEFAULT = {"title": "Vous voulez [[la même chose]] dans votre entreprise ?",
               "text": "De l'ambition IA à l'exécution réelle : réservez 30 minutes avec l'équipe AI Partners.",
               "button": "Réserver un échange", "note": "Lien dans le post 👇", "booking_url": "",
               "post_line": "📅 Réserver un échange avec nous : {url}",
               "episode": "L'épisode complet : AI Corner {number}, sur YouTube"}


# ---------------------------------------------------------------------------------------------------------------
# Transcription pour Claude : qui parle
# ---------------------------------------------------------------------------------------------------------------

def speaker_text(transcript: dict, ep: Path, guest: str) -> str:
    """Une ligne par phrase `[début en s] Invité|Animateur : texte` ; l'orateur vient de work/diarized_words.json
    (épisode complet) quand il existe, sinon pas d'étiquette."""
    from .transcribe import sentences
    dw = ep / "work" / "diarized_words.json"
    words = json.loads(dw.read_text(encoding="utf-8")) if dw.exists() else []
    first = guest.split()[0] if guest else "Invité"
    out, k = [], 0
    for p in sentences(transcript):
        while k < len(words) and words[k]["e"] < p["start"]:
            k += 1
        votes = {"host": 0.0, "guest": 0.0}
        j = k
        while j < len(words) and words[j]["s"] <= p["end"]:
            votes[words[j].get("spk", "guest")] = votes.get(words[j].get("spk", "guest"), 0.0) + 1
            j += 1
        who = ""
        if words and sum(votes.values()):
            who = (f"{first} (invité)" if votes["guest"] >= votes["host"] else "Thomas (animateur)") + " : "
        out.append(f"[{p['start']:.1f}] {who}{p['text']}")
    return "\n".join(out)


def brief(brand) -> str:
    p = brand.dir / "carousel.md"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def _cfg(brand) -> dict:
    return dict(brand.cfg.get("carousel") or {})


def _model(brand) -> str:
    return str(_cfg(brand).get("model") or "claude-opus-5")


# ---------------------------------------------------------------------------------------------------------------
# 1. Angles
# ---------------------------------------------------------------------------------------------------------------

ANGLES_PROMPT = """Tu prépares un carrousel LinkedIn (PDF de 7 à 9 slides) tiré d'un épisode du podcast AI Corner (AI Partners).
Voici le brief de la marque, à suivre à la lettre :

{brief}

Propose EXACTEMENT 3 angles de carrousel, de 3 types DIFFÉRENTS parmi : {types}. Chaque angle doit apporter une vraie
valeur à un dirigeant qui ne regardera pas l'épisode, et reposer sur ce que l'invité dit réellement (2 à 4 passages
cités mot pour mot, avec l'horodatage en secondes de la ligne où commence la citation).

Réponds UNIQUEMENT en JSON :
{{"angles": [{{"type": "lecons", "cover": "promesse de couverture ≤ 9 mots, mots clés entre [[ ]]",
  "promise": "ce que le lecteur retient, en 1 phrase", "outline": ["titre de la slide 2", "titre de la slide 3", "…"],
  "evidence": [{{"t": 1234.5, "quote": "citation EXACTE de la transcription"}}],
  "why": "pourquoi cet angle marche pour la communauté LinkedIn d'AI Partners (1 phrase pour l'équipe marketing)"}}]}}"""


def propose_angles(brand, transcript: dict, ep: Path, number: str, guest: str, company: str, role: str,
                   import_file: Path | None = None) -> dict:
    from .llm import ask_json
    out_dir = ep / "carrousel"
    out_dir.mkdir(parents=True, exist_ok=True)
    segs = transcript["segments"]
    if import_file:
        data = json.loads(import_file.read_text(encoding="utf-8"))
        source = "import"
    else:
        console.print("Claude lit l'épisode et propose 3 angles de carrousel (≈ 3 min)…")
        user = (f"Épisode {number}. Invité : {guest}, {role} ({company}). Animateur : Thomas Spitz (CEO d'AI Partners).\n\n"
                f"TRANSCRIPTION (une phrase par ligne, [début en s] orateur : texte) :\n{speaker_text(transcript, ep, guest)}")
        data = ask_json(ANGLES_PROMPT.format(brief=brief(brand), types=", ".join(TYPES)), user, model=_model(brand),
                        backend=brand.cfg.selection.llm_backend, max_tokens=6000)
        source = "claude"
    angles = [a for a in data.get("angles", []) if isinstance(a, dict)]
    for i, a in enumerate(angles, 1):
        a["rank"] = i
        a["checks"] = []
        for ev in a.get("evidence") or []:
            t, score = find_evidence(segs, ev.get("quote", ""), _num(ev.get("t")))
            ev["found_t"], ev["score"] = t, round(score, 2)
            if score < 0.6:
                a["checks"].append({"level": "ÉCHEC", "msg": f"citation introuvable : « {ev.get('quote', '')[:60]}… »"})
            elif score < 0.85:
                a["checks"].append({"level": "ATTENTION", "msg": f"citation approximative ({score:.0%}) : « {ev.get('quote', '')[:60]}… »"})
        a["status"] = _status(a["checks"])
    res = {"episode": number, "guest": guest, "company": company, "role": role, "generated": date.today().isoformat(),
           "source": source, "angles": angles}
    (out_dir / "angles.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


def write_angles_md(res: dict, out: Path, command: str) -> Path:
    md = [f"# Carrousel LinkedIn de l'épisode {res['episode']} : 3 angles à choisir", "",
          f"Invité : {res['guest']} ({res['company']}). L'équipe marketing choisit UN angle ; Claude rédige ensuite les slides.", ""]
    for a in res["angles"]:
        md += [f"## {a['rank']}. {_plain(a.get('cover', ''))}", "",
               f"- Type : {a.get('type', '?')}",
               f"- Ce que le lecteur retient : {a.get('promise', '')}",
               f"- Pourquoi : {a.get('why', '')}",
               "- Déroulé : " + " → ".join(a.get("outline") or [])]
        for ev in a.get("evidence") or []:
            if ev.get("found_t") is not None:
                md.append(f"- Tenu par l'épisode à {_ts(ev['found_t'])} : « {ev.get('quote', '')} »")
        md.append(f"- Contrôles : {a['status']}" + "".join(f"\n  - {c['level']} : {c['msg']}" for c in a["checks"]))
        md.append("")
    md += ["## Choisir", "", f"`{command} --pick N` (N = numéro de l'angle). Une précision pour la rédaction : "
           f"`{command} --pick N --note \"…\"`."]
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    return out


# ---------------------------------------------------------------------------------------------------------------
# 2. Slides
# ---------------------------------------------------------------------------------------------------------------

SLIDES_PROMPT = """Tu rédiges un carrousel LinkedIn (PDF) tiré d'un épisode du podcast AI Corner (AI Partners), en français.
Brief de la marque, à suivre à la lettre :

{brief}

ANGLE CHOISI PAR L'ÉQUIPE MARKETING :
{angle}
{note}
Rédige 6 à 8 slides (la slide CTA finale est ajoutée automatiquement : ne l'écris pas). Types de slide :
- "cover" (1re, obligatoire) : "title" = la promesse claire (≤ 10 mots, voir le brief), 1 à 3 mots clés entre [[ ]] ;
  "subtitle" facultatif (vide par défaut) ;
- "intro" : "title" + "body" (contexte, pourquoi c'est important) ;
- "point" : "n" (numéro), "title" (≤ 60 caractères, une action ou une idée) + "body" (≤ 35 mots) + "quote" facultative
  (citation COURTE de l'invité, mot pour mot, « […] » pour couper) ;
- "stat" : "value" (le chiffre tel que dit dans l'épisode), "label" (ce qu'il mesure, ≤ 8 mots) + "body" ;
- "quote" : "text" (citation de l'invité mot pour mot, ≤ 30 mots, « […] » pour couper) ;
- "recap" (avant-dernière, conseillée) : "title" + "items" (3 à 6 éléments de ≤ 8 mots).
Dans "title" et "body", 1 à 3 mots clés par slide peuvent être entre [[ ]] (mis en valeur en bleu).
Chaque slide sauf "cover" et "recap" porte "evidence" : {{"t": secondes, "quote": "passage EXACT de la transcription qui la prouve"}}.
Rien qui ne soit dans la transcription (chiffres, outils, noms). Citations : seulement les phrases de l'invité.

Réponds UNIQUEMENT en JSON :
{{"guest_line": "Prénom Nom · rôle en français, Entreprise", "slides": [{{"kind": "cover", "title": "…"}}, …],
  "post": "texte du post LinkedIn qui présente le carrousel, SANS lien (le lien de réservation est ajouté automatiquement)"}}"""


def write_slides(brand, transcript: dict, ep: Path, angle: dict, meta: dict, note: str = "") -> dict:
    from .llm import ask_json
    console.print("Claude rédige les slides (≈ 3 min)…")
    a = {k: angle.get(k) for k in ("type", "cover", "promise", "outline", "evidence")}
    user = (f"Épisode {meta['number']}. Invité : {meta['guest']}, {meta['role']} ({meta['company']}). "
            f"Animateur : Thomas Spitz.\n\nTRANSCRIPTION (une phrase par ligne, [début en s] orateur : texte) :\n"
            f"{speaker_text(transcript, ep, meta['guest'])}")
    system = SLIDES_PROMPT.format(brief=brief(brand), angle=json.dumps(a, ensure_ascii=False, indent=1),
                                  note=f"\nPRÉCISION DE L'ÉQUIPE : {note}\n" if note else "")
    data = ask_json(system, user, model=_model(brand), backend=brand.cfg.selection.llm_backend, max_tokens=8000)
    content = {"episode": meta["number"], "guest": meta["guest"], "company": meta["company"], "role": meta["role"],
               "angle": angle.get("rank"), "angle_type": angle.get("type"), "note": note,
               "generated": date.today().isoformat(), "guest_line": data.get("guest_line") or f"{meta['guest']} · {meta['company']}",
               "slides": [s for s in data.get("slides", []) if isinstance(s, dict) and s.get("kind") != "cta"],
               "post": data.get("post", "")}
    return content


def post_text(brand, content: dict) -> str:
    """Post LinkedIn final = texte de Claude + ligne de réservation (lien cliquable : le seul endroit où il l'est, LinkedIn
    affiche les pages d'un document comme des images ; Arthur, 12/10/2026 : « mets le lien dans le post »)."""
    cta = {**CTA_DEFAULT, **(_cfg(brand).get("cta") or {})}
    body = (content.get("post") or "").rstrip()
    if not cta.get("booking_url"):
        return body
    return f"{body}\n\n{cta['post_line'].format(url=cta['booking_url'])}"


def check_slides(content: dict, segments: list[dict]) -> list[dict]:
    """Contrôles par slide (texte affiché, citations, chiffres). Chaque entrée : {slide, level, msg}."""
    full = _digits(norm(" ".join(s["text"] for s in segments)))
    out: list[dict] = []

    def add(i, level, msg):
        out.append({"slide": i, "level": level, "msg": msg})
    slides = content["slides"]
    n = len(slides) + 1
    if not (RULES["min_slides"] <= n <= RULES["max_slides"] + 1):
        add(0, "ATTENTION", f"{n} slides avec le CTA (attendu : 7 à 9)")
    if not slides or slides[0].get("kind") != "cover":
        add(1, "ÉCHEC", "la 1re slide doit être la couverture")
    for i, s in enumerate(slides, 1):
        title = _plain(s.get("title", ""))
        if len(title) > RULES["title_hard"]:
            add(i, "ÉCHEC", f"titre trop long ({len(title)} caractères)")
        elif len(title) > RULES["title"]:
            add(i, "ATTENTION", f"titre long ({len(title)} caractères, ≤ {RULES['title']} conseillé)")
        words = len(_plain(s.get("body", "")).split())
        if words > RULES["words_hard"]:
            add(i, "ÉCHEC", f"texte trop long ({words} mots)")
        elif words > RULES["words"]:
            add(i, "ATTENTION", f"texte long ({words} mots, ≤ {RULES['words']} conseillé)")
        for key in ("text", "quote"):                          # citations affichées : mot pour mot, morceau par morceau
            q = s.get(key) if (key == "quote" or s.get("kind") == "quote") else None
            for part in (p.strip(" .,;:!?…«»\"") for p in re.split(r"\[…\]|\[\.\.\.\]|…", q or "")):
                if len(norm(part)) < 12:
                    continue
                _, score = find_evidence(segments, part)
                if score < 0.9:
                    add(i, "ÉCHEC" if score < 0.75 else "ATTENTION",
                        f"citation non retrouvée mot pour mot ({score:.0%}) : « {part[:70]} »")
        if s.get("kind") not in ("cover", "recap"):
            ev = s.get("evidence") or {}
            _, score = find_evidence(segments, ev.get("quote", ""), _num(ev.get("t")))
            if score < 0.6:
                add(i, "ÉCHEC", "aucun passage de l'épisode ne prouve cette slide (evidence introuvable)")
            elif score < 0.85:
                add(i, "ATTENTION", f"passage de preuve approximatif ({score:.0%})")
        shown = " ".join(_plain(str(s.get(k, ""))) for k in ("title", "body", "value", "label", "quote", "text"))
        shown += " " + " ".join(_plain(x) for x in s.get("items") or [])
        for num in re.findall(r"\d[\d  .,]*\d|\d", _digits(shown)):
            d = re.sub(r"[  .,]", "", num)
            if len(d) >= 2 and d not in re.sub(r"[  .,]", "", full):
                add(i, "ÉCHEC", f"chiffre « {num} » absent de la transcription")
    return out


def _status(checks: list[dict]) -> str:
    levels = {c["level"] for c in checks}
    return "ÉCHEC" if "ÉCHEC" in levels else "ATTENTION" if "ATTENTION" in levels else "OK"


def save_content(ep: Path, content: dict, segments: list[dict], command: str) -> Path:
    content["checks"] = check_slides(content, segments)
    if not content.get("post_final", "").strip():
        content["checks"].append({"slide": 0, "level": "ÉCHEC", "msg": "post LinkedIn vide"})
    elif "http" not in content["post_final"]:
        content["checks"].append({"slide": 0, "level": "ATTENTION", "msg": "post sans lien de réservation (carousel.cta.booking_url)"})
    content["status"] = _status(content["checks"])
    d = ep / "carrousel"
    d.mkdir(parents=True, exist_ok=True)
    (d / "contenu.json").write_text(json.dumps(content, ensure_ascii=False, indent=1), encoding="utf-8")
    md = [f"# Carrousel {content['episode']} — texte des slides", "",
          f"Angle {content.get('angle')} ({content.get('angle_type')}). Contrôles : {content['status']}. "
          f"Retouche : modifier `contenu.json` puis `{command} --render`.", ""]
    for i, s in enumerate(content["slides"], 1):
        md.append(f"## {i}. {s.get('kind')} — {_plain(s.get('title') or s.get('value') or s.get('text') or '')}")
        for k in ("label", "body", "quote", "text"):
            if s.get(k):
                md.append(f"- {k} : {_plain(s[k])}")
        for it in s.get("items") or []:
            md.append(f"- {_plain(it)}")
        ev = s.get("evidence") or {}
        if ev.get("quote"):
            md.append(f"- preuve ({_ts(_num(ev.get('t')) or 0)}) : « {ev['quote']} »")
        for c in content["checks"]:
            if c["slide"] == i:
                md.append(f"- **{c['level']}** : {c['msg']}")
        md.append("")
    md += [f"## {len(content['slides']) + 1}. cta — ajoutée par le framework (`carousel.cta` de brand.yaml)", "",
           "## Post LinkedIn qui accompagne le carrousel (à publier avec le PDF)", "",
           content.get("post_final") or content.get("post", ""), ""]
    (d / "post_linkedin.md").write_text((content.get("post_final") or content.get("post", "")) + "\n", encoding="utf-8")
    (d / "contenu.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return d / "contenu.md"


# ---------------------------------------------------------------------------------------------------------------
# 3. Rendu : HTML -> Chrome -> PNG + PDF
# ---------------------------------------------------------------------------------------------------------------

def _hl(text: str) -> str:
    """Échappe le HTML ; [[mots]] -> mis en valeur."""
    return re.sub(r"\[\[(.+?)\]\]", r'<span class="hl">\1</span>', html.escape(str(text or "")))


def _plain(text: str) -> str:
    return re.sub(r"\[\[(.+?)\]\]", r"\1", str(text or ""))


def _num(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _ts(t: float) -> str:
    return f"{int(t) // 60}:{int(t) % 60:02d}"


def _uri(p: Path | None) -> str:
    return p.resolve().as_uri() if p else ""


def _logo_svg(path: Path, color: str) -> str:
    """Logo SVG en ligne, recoloré (les logos de la charte sont monochromes)."""
    if not path or not path.exists():
        return ""
    svg = path.read_text(encoding="utf-8")
    svg = re.sub(r'fill="(?!none)[^"]*"', f'fill="{color}"', svg)
    return re.sub(r"<svg ", '<svg class="svg" ', svg, count=1)


def portraits(brand, ep: Path, video: Path, company: str) -> dict:
    """Photos détourées de l'invité et de l'animateur : les mêmes que pour les miniatures (sourire, regard), en cache."""
    out = {}
    try:
        from .multicam import load_spec
        from .thumbnail import _context, _cut_cached
        spec = load_spec(video)
        if not spec:
            return out
        ctx = _context(brand, spec, ep, company)
        cache = ep / "carrousel" / "assets"
        cache.mkdir(parents=True, exist_ok=True)
        for role in ("guest", "host"):
            f = cache / f"{role}.png"
            if not f.exists():
                im = _cut_cached(ctx["chosen"][role][0], ctx["work"])
                bbox = im.getchannel("A").getbbox()
                if bbox:
                    im = im.crop(bbox)
                im.save(f)
            out[role] = f
    except Exception as e:  # noqa: BLE001 — les carrousels se font aussi sans photo
        console.print(f"[yellow]Photos détourées indisponibles ({e}) : slides sans portrait.[/yellow]")
    return out


BASE_CSS = """
@font-face { font-family: "Metropolis"; src: url("{f_reg}"); font-weight: 400; }
@font-face { font-family: "Metropolis"; src: url("{f_bold}"); font-weight: 700; }
@font-face { font-family: "Metropolis"; src: url("{f_xb}"); font-weight: 800; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { width: 1080px; background: #000; font-family: "Metropolis", Arial, sans-serif; -webkit-font-smoothing: antialiased; }
.slide { position: relative; width: 1080px; height: 1350px; overflow: hidden; display: flex; flex-direction: column;
         padding: 96px 88px 150px; }
.fit { overflow: hidden; }
.svg { height: 100%; width: auto; display: block; }
.foot { position: absolute; left: 88px; right: 88px; bottom: 56px; height: 44px; display: flex; align-items: center;
        justify-content: space-between; }
.foot .logo { height: 30px; }
.foot .page { font-weight: 700; font-size: 26px; letter-spacing: .08em; }
.foot .next { font-weight: 700; font-size: 24px; letter-spacing: .06em; display: flex; gap: 14px; align-items: center; }
.kicker { font-weight: 700; font-size: 28px; letter-spacing: .16em; text-transform: uppercase; }
.overflow { outline: 6px solid #ff2d55; }
:where(.slide > *) { position: relative; z-index: 2; }
.foot { z-index: 3; }
"""

FIT_JS = """
<script>
document.fonts.ready.then(() => {
  document.querySelectorAll('.fit').forEach(el => {
    const h = () => el.children.length === 1 && el.children[0].tagName === 'SPAN'
      ? el.children[0].getBoundingClientRect().height : el.scrollHeight;
    let s = parseFloat(getComputedStyle(el).fontSize), min = s * 0.5;
    while ((h() > el.clientHeight + 1 || el.scrollWidth > el.clientWidth + 1) && s > min) {
      s -= 2; el.style.fontSize = s + 'px';
    }
    if (h() > el.clientHeight + 1) el.classList.add('overflow');
  });
});
</script>"""


MIX_COVER = """
.slide.cover { background: linear-gradient(170deg, #258AF3 0%, #0A47B6 70%, #151D53 100%); }
.person { position: absolute; right: -150px; bottom: 0; height: 800px; filter: drop-shadow(0 30px 60px rgba(5,15,60,.45)); }
.cover .kicker { color: #fff; background: rgba(255,255,255,.16); align-self: flex-start; padding: 12px 22px;
                 border-radius: 999px; font-size: 24px; }
.cover h1 { margin-top: 56px; font-size: 100px; line-height: 1.06; width: 680px; height: auto; max-height: 560px; justify-content: flex-start;
            text-shadow: 0 4px 30px rgba(5,15,60,.35); }
.cover .hl { background: #151D53; }
.cover .subt { font-size: 38px; font-weight: 700; line-height: 1.25; width: 560px; color: #E3EAFF; margin-top: 36px; }
.cover .who { position: absolute; left: 88px; bottom: 150px; margin: 0; background: #fff; color: #151D53; border-radius: 22px;
              padding: 20px 28px; font-size: 26px; font-weight: 700; max-width: 620px; z-index: 3; }
.cover .who .gl { height: 40px; padding: 0; border-radius: 0; }
"""


def _style_css(style: str) -> str:
    if style == "mix":
        return _style_css("usecase") + MIX_COVER
    if style == "usecase":
        return """
.slide { background: radial-gradient(120% 80% at 80% 0%, #24317F 0%, #151D53 55%, #0E1440 100%); color: #fff; }
.slide.cover, .slide.cta { background: linear-gradient(165deg, #4A6CF5 0%, #3458ED 45%, #1D2C76 100%); }
.glass { position: absolute; width: 900px; right: -170px; top: 230px; opacity: .22; filter: blur(1.5px)
         drop-shadow(0 40px 60px rgba(10,20,80,.55)); }
.glass2 { position: absolute; width: 900px; right: -150px; top: 214px; opacity: .14; filter: blur(9px); }
.hl { background: #5C86F7; box-decoration-break: clone; -webkit-box-decoration-break: clone; padding: 0 12px; margin: 0 -4px; }
.cover .kicker { color: #CFDBFF; }
.cover h1 { margin-top: auto; font-weight: 800; font-size: 104px; line-height: 1.08; height: 700px; display: flex;
            flex-direction: column; justify-content: flex-end; }
.cover .who { margin-top: 40px; font-size: 30px; color: #E3EAFF; display: flex; gap: 22px; align-items: center; }
.cover .who .gl { height: 54px; background: #fff; border-radius: 16px; padding: 10px 18px; }
h2 { font-weight: 800; font-size: 70px; line-height: 1.08; height: 240px; display: flex; flex-direction: column; justify-content: flex-end; }
h2 .hl, .card .hl { background: none; color: #258AF3; padding: 0; margin: 0; }
.sub { color: #258AF3; font-weight: 700; font-size: 30px; margin-top: 14px; letter-spacing: .02em; }
.card { background: #fff; color: #151D53; border-radius: 34px; padding: 52px 56px; margin-top: 48px; }
.card .body { font-size: 40px; line-height: 1.32; height: 310px; }
.num { width: 96px; height: 96px; border-radius: 26px; background: #E6EEFE; color: #258AF3; font-weight: 800; font-size: 50px;
       display: flex; align-items: center; justify-content: center; margin-bottom: 30px; }
.qt { margin-top: 34px; background: #F1F6FD; color: #1D2C76; border-radius: 34px; padding: 64px 50px 36px; font-size: 34px;
      line-height: 1.35; height: 330px; position: relative; }
.qt::before { content: "“"; position: absolute; left: 34px; top: -30px; font-size: 140px; font-weight: 800; color: #258AF3; }
.qt .by { display: block; margin-top: 18px; font-size: 26px; font-weight: 700; color: #258AF3; }
.statv { font-weight: 800; font-size: 210px; color: #258AF3; line-height: 1; margin-top: 30px; }
.statl { font-weight: 800; font-size: 54px; margin-top: 10px; color: #151D53; }
.bigq { margin-top: auto; margin-bottom: auto; font-weight: 800; font-size: 66px; line-height: 1.18; height: 760px;
        display: flex; flex-direction: column; justify-content: center; }
.bigq .mark { color: #258AF3; font-size: 200px; line-height: .6; }
.bigq .by { font-size: 32px; font-weight: 700; color: #9DB8FF; margin-top: 30px; }
.rlist { list-style: none; margin-top: 50px; display: flex; flex-direction: column; gap: 22px; height: 760px; }
.rlist li { background: #fff; color: #151D53; border-radius: 26px; padding: 30px 40px; font-size: 38px; font-weight: 700;
            display: flex; gap: 26px; align-items: center; }
.rlist li b { color: #258AF3; font-size: 40px; min-width: 44px; }
.cta h1 { font-weight: 800; font-size: 96px; line-height: 1.08; margin-top: 120px; height: 470px; display: flex;
          flex-direction: column; justify-content: flex-end; }
.cta p { font-size: 38px; line-height: 1.35; margin-top: 44px; color: #E3EAFF; height: 160px; }
.btn { margin-top: 50px; align-self: flex-start; background: #fff; color: #258AF3; font-weight: 800; font-size: 42px;
       border-radius: 999px; padding: 30px 56px; text-transform: uppercase; letter-spacing: .03em; }
.url { margin-top: 26px; font-size: 32px; font-weight: 700; color: #fff; }
.ep { margin-top: 60px; font-size: 28px; color: #CFDBFF; }
.foot { color: #fff; } .foot .logo { color: #fff; } .foot .page { color: #9DB8FF; }
"""
    if style == "lignes":
        return """
.slide { background: #000; color: #fff; }
.slide.cta { background: #151D53; }
.lines { position: absolute; right: -380px; bottom: -40px; width: 1700px; opacity: .9; }
.cover .lines { right: -520px; bottom: 120px; width: 2000px; opacity: 1; }
.hl { color: #258AF3; }
.cover .kicker { color: #258AF3; }
.cover h1 { margin-top: auto; font-weight: 800; font-size: 108px; line-height: 1.04; text-transform: uppercase; height: 760px;
            display: flex; flex-direction: column; justify-content: flex-end; letter-spacing: -.01em; }
.cover .who { margin-top: 40px; font-size: 30px; color: #C9D3F5; border-top: 1px solid #258AF3; padding-top: 28px;
              display: flex; justify-content: space-between; align-items: center; }
.cover .who .gl { height: 46px; filter: brightness(0) invert(1); }
.bignum { font-weight: 800; font-size: 200px; line-height: .9; color: transparent; -webkit-text-stroke: 3px #258AF3; }
h2 { font-weight: 800; font-size: 72px; line-height: 1.06; text-transform: uppercase; margin-top: 26px; height: 330px;
     display: flex; flex-direction: column; justify-content: flex-end; }
.sub { color: #258AF3; font-weight: 700; font-size: 30px; margin-top: 18px; letter-spacing: .14em; text-transform: uppercase; }
.rule { height: 1px; background: #258AF3; margin: 40px 0; width: 100%; }
.body { font-size: 42px; line-height: 1.36; color: #DCE3F7; height: 330px; }
.qt { margin-top: 20px; border-left: 4px solid #258AF3; padding: 6px 0 6px 34px; font-size: 34px; line-height: 1.35;
      color: #fff; height: 250px; }
.qt .by { display: block; margin-top: 14px; font-size: 24px; font-weight: 700; color: #258AF3; letter-spacing: .1em; text-transform: uppercase; }
.statv { font-weight: 800; font-size: 260px; color: #258AF3; line-height: 1; margin-top: 60px; }
.statl { font-weight: 800; font-size: 56px; text-transform: uppercase; margin-top: 10px; }
.bigq { margin: auto 0; font-weight: 700; font-size: 64px; line-height: 1.2; height: 800px; display: flex;
        flex-direction: column; justify-content: center; }
.bigq .mark { color: #258AF3; font-size: 220px; line-height: .6; font-weight: 800; }
.bigq .by { font-size: 28px; font-weight: 700; color: #258AF3; margin-top: 34px; letter-spacing: .12em; text-transform: uppercase; }
.rlist { list-style: none; margin-top: 40px; height: 820px; }
.rlist li { font-size: 40px; font-weight: 700; padding: 28px 0; border-bottom: 1px solid rgba(37,138,243,.5); display: flex; gap: 30px; }
.rlist li b { color: #258AF3; min-width: 64px; }
.cta h1 { font-weight: 800; font-size: 94px; line-height: 1.06; text-transform: uppercase; margin-top: 110px; height: 500px;
          display: flex; flex-direction: column; justify-content: flex-end; }
.cta p { font-size: 38px; line-height: 1.35; margin-top: 44px; color: #DCE3F7; height: 160px; }
.btn { margin-top: 44px; align-self: flex-start; background: #258AF3; color: #fff; font-weight: 800; font-size: 40px;
       border-radius: 999px; padding: 30px 56px; text-transform: uppercase; letter-spacing: .04em; }
.url { margin-top: 26px; font-size: 32px; font-weight: 700; }
.ep { margin-top: 56px; font-size: 28px; color: #9DB8FF; }
.foot { color: #fff; } .foot .page { color: #258AF3; }
"""
    # portrait
    return """
.slide { background: #fff; color: #151D53; }
.slide.cover, .slide.cta, .slide.quote { background: linear-gradient(170deg, #258AF3 0%, #0A47B6 70%, #151D53 100%); color: #fff; }
.person { position: absolute; right: -60px; bottom: 0; height: 900px; filter: drop-shadow(0 30px 60px rgba(5,15,60,.45)); }
.cover .person { height: 800px; right: -150px; }
.quote .person { height: 640px; right: -40px; }
.hl { color: #fff; background: #151D53; padding: 0 12px; box-decoration-break: clone; -webkit-box-decoration-break: clone; }
.slide:not(.cover):not(.cta):not(.quote) .hl { background: none; color: #258AF3; padding: 0; }
.cover .kicker { color: #fff; background: rgba(255,255,255,.16); align-self: flex-start; padding: 12px 22px; border-radius: 999px; font-size: 24px; }
.cover h1 { margin-top: 70px; font-weight: 800; font-size: 96px; line-height: 1.1; width: 600px; text-shadow: 0 4px 30px rgba(5,15,60,.35); height: 760px; position: relative; z-index: 2; }
.cover .who { position: absolute; left: 88px; bottom: 150px; z-index: 3; background: #fff; color: #151D53; border-radius: 22px;
              padding: 20px 28px; font-size: 26px; font-weight: 700; display: flex; gap: 18px; align-items: center; max-width: 620px; }
.cover .who .gl { height: 40px; }
.bar { position: absolute; left: 0; top: 0; bottom: 0; width: 18px; background: #258AF3; }
.num { font-weight: 800; font-size: 150px; color: #E6EEFE; line-height: 1; -webkit-text-stroke: 0; }
h2 { font-weight: 800; font-size: 70px; line-height: 1.08; margin-top: 10px; height: 300px; display: flex; flex-direction: column; justify-content: flex-end; }
.sub { color: #258AF3; font-weight: 700; font-size: 28px; letter-spacing: .14em; text-transform: uppercase; }
.body { font-size: 42px; line-height: 1.36; margin-top: 40px; color: #1D2C76; height: 330px; }
.qt { margin-top: 30px; background: #F1F6FD; border-radius: 30px; padding: 36px 44px; font-size: 34px; line-height: 1.35;
      height: 270px; color: #151D53; }
.qt .by { display: block; margin-top: 14px; font-size: 24px; font-weight: 700; color: #258AF3; }
.statv { font-weight: 800; font-size: 230px; color: #258AF3; line-height: 1; margin-top: 60px; }
.statl { font-weight: 800; font-size: 56px; margin-top: 10px; }
.bigq { margin-top: 40px; font-weight: 800; font-size: 60px; line-height: 1.2; width: 700px; height: 760px; display: flex;
        flex-direction: column; justify-content: flex-start; position: relative; z-index: 2; }
.bigq .mark { font-size: 200px; line-height: .6; color: #fff; opacity: .5; }
.bigq .by { font-size: 28px; font-weight: 700; margin-top: 30px; opacity: .85; }
.rlist { list-style: none; margin-top: 40px; height: 820px; display: flex; flex-direction: column; gap: 20px; }
.rlist li { background: #F1F6FD; border-radius: 24px; padding: 28px 36px; font-size: 38px; font-weight: 700; display: flex; gap: 26px; }
.rlist li b { color: #258AF3; min-width: 44px; }
.cta h1 { font-weight: 800; font-size: 92px; line-height: 1.08; margin-top: 110px; height: 480px; display: flex;
          flex-direction: column; justify-content: flex-end; }
.cta p { font-size: 38px; line-height: 1.35; margin-top: 44px; height: 160px; }
.btn { margin-top: 44px; align-self: flex-start; background: #fff; color: #0A47B6; font-weight: 800; font-size: 40px;
       border-radius: 999px; padding: 30px 56px; text-transform: uppercase; letter-spacing: .03em; }
.url { margin-top: 26px; font-size: 32px; font-weight: 700; }
.ep { margin-top: 56px; font-size: 28px; opacity: .85; }
.foot { color: #151D53; } .foot .page { color: #258AF3; }
.cover .foot, .cta .foot, .quote .foot { color: #fff; } .cover .foot .page, .cta .foot .page, .quote .foot .page { color: #fff; }
"""


def _slide_html(s: dict, i: int, n: int, style: str, ctx: dict) -> str:
    kind = s.get("kind", "point")
    dark_logo = style == "portrait" and kind not in ("cover", "cta", "quote")
    logo = f'<div class="logo">{ctx["logo_dark" if dark_logo else "logo_white"]}</div>'
    nxt = '<div class="next">GLISSEZ <span>→</span></div>' if i == 1 else f'<div class="page">{i:02d} / {n:02d}</div>'
    foot = f'<div class="foot">{logo}{nxt if i < n else ""}</div>'
    deco = ""
    if style == "mix":                      # couverture « portrait » + slides « cas client » (choix d'Arthur, 12/10/2026)
        if kind == "cover" and ctx.get("guest_img"):
            deco = f'<img class="person" src="{ctx["guest_img"]}">'
        elif kind == "cta":
            deco = f'<img class="glass2" src="{ctx["icon"]}"><img class="glass" src="{ctx["icon"]}">'
        style = "usecase"
    elif style == "usecase" and kind in ("cover", "cta"):
        deco = f'<img class="glass2" src="{ctx["icon"]}"><img class="glass" src="{ctx["icon"]}">'
    elif style == "lignes" and kind in ("cover", "cta", "quote", "stat"):
        deco = f'<img class="lines" src="{ctx["lines"]}">'
    elif style == "portrait":
        if kind in ("cover", "quote") and ctx.get("guest_img"):
            deco = f'<img class="person" src="{ctx["guest_img"]}">'
        elif kind not in ("cta",):
            deco = '<div class="bar"></div>'
    gl = f'<img class="gl" src="{ctx["guest_logo"]}">' if ctx.get("guest_logo") else ""
    by = html.escape(ctx["guest_short"])
    q = (f'<div class="qt fit">{_hl(s["quote"])}<span class="by">— {by}</span></div>' if s.get("quote") else "")
    if kind == "cover":
        sub = f'<div class="subt">{_hl(s["subtitle"])}</div>' if s.get("subtitle") else ""
        inner = (f'<div class="kicker">AI Corner · {html.escape(ctx["number"])}</div><h1 class="fit"><span>{_hl(s.get("title"))}</span></h1>'
                 f'{sub}<div class="who">{gl}<span>{html.escape(ctx["guest_line"])}</span></div>')
    elif kind == "stat":
        card_open, card_close = ('<div class="card">', '</div>') if style == "usecase" else ("", "")
        inner = (f'<div class="sub">{_hl(s.get("title") or "Le chiffre")}</div>{card_open}'
                 f'<div class="statv">{html.escape(str(s.get("value", "")))}</div>'
                 f'<div class="statl">{_hl(s.get("label", ""))}</div>'
                 f'<div class="body fit" style="margin-top:30px;height:260px">{_hl(s.get("body", ""))}</div>{card_close}')
    elif kind == "quote":
        inner = (f'<div class="bigq"><span class="mark">“</span><span class="fit" style="display:block;height:560px">'
                 f'{_hl(s.get("text"))}</span><span class="by">— {html.escape(ctx["guest_line"])}</span></div>')
    elif kind == "recap":
        items = "".join(f"<li><b>{k:02d}</b><span>{_hl(x)}</span></li>" for k, x in enumerate(s.get("items") or [], 1))
        inner = f'<h2 class="fit" style="height:200px"><span>{_hl(s.get("title") or "À retenir")}</span></h2><ul class="rlist fit">{items}</ul>'
    elif kind == "cta":
        inner = (f'<h1 class="fit"><span>{_hl(s.get("title"))}</span></h1><p class="fit"><span>{_hl(s.get("text"))}</span></p>'
                 f'<div class="btn">{html.escape(s.get("button", ""))} →</div><div class="url">{html.escape(s.get("note") or s.get("url", ""))}</div>'
                 f'<div class="ep">{html.escape(s.get("episode", ""))}</div>')
    else:                                   # intro / point
        label = "Le contexte" if kind == "intro" else f"Idée {s.get('n') or i - 1}"
        if style == "usecase":
            num = f'<div class="num">{int(s.get("n") or i - 1)}</div>' if kind == "point" else ""
            inner = (f'<h2 class="fit"><span>{_hl(s.get("title"))}</span></h2><div class="sub">{label}</div>'
                     f'<div class="card">{num}<div class="body fit">{_hl(s.get("body"))}</div></div>{q}')
        elif style == "lignes":
            big = f'<div class="bignum">{int(s.get("n") or i - 1):02d}</div>' if kind == "point" else '<div class="sub">Le contexte</div>'
            inner = (f'{big}<h2 class="fit"><span>{_hl(s.get("title"))}</span></h2><div class="rule"></div>'
                     f'<div class="body fit">{_hl(s.get("body"))}</div>{q}')
        else:
            num = f'<div class="num">{int(s.get("n") or i - 1):02d}</div>' if kind == "point" else ""
            inner = (f'{num}<div class="sub">{label}</div><h2 class="fit"><span>{_hl(s.get("title"))}</span></h2>'
                     f'<div class="body fit">{_hl(s.get("body"))}</div>{q}')
    return f'<section class="slide {kind}">{deco}{inner}{foot}</section>'


def render(brand, ep: Path, content: dict, styles: list[str], portraits_: dict | None = None,
           out_root: Path | None = None) -> dict:
    """Rend chaque style -> carrousel/<style>/slide_NN.png + <E>_carrousel_<style>.pdf. Retourne {style: [png…]}."""
    from .thumbnail import _browser, guest_logo_path
    cfg = _cfg(brand)
    cta = {**CTA_DEFAULT, **(cfg.get("cta") or {})}
    cta["episode"] = cta["episode"].format(number=content["episode"])
    slides = list(content["slides"]) + [{"kind": "cta", **cta}]
    fonts = brand.assets_dir / "fonts"
    gp = guest_logo_path(brand, content["company"])
    glogo_png = None
    if gp:
        glogo_png = ep / "carrousel" / "assets" / f"logo_{gp.stem}.png"
        if not glogo_png.exists():
            from .thumbnail import load_logo
            glogo_png.parent.mkdir(parents=True, exist_ok=True)
            load_logo(gp, on_light=True, height=200).save(glogo_png)
    logo_svg = brand.asset("logo_horizontal.svg")
    ctx = {"number": content["episode"], "guest_line": content.get("guest_line", ""),
           "guest_short": content["guest"], "icon": _uri(brand.asset("logo_icon.png")),
           "lines": _uri(brand.asset("outro_bg.png")), "guest_logo": _uri(glogo_png),
           "guest_img": _uri((portraits_ or {}).get("guest")),
           "logo_white": _logo_svg(logo_svg, "#FFFFFF"), "logo_dark": _logo_svg(logo_svg, "#151D53")}
    root = out_root or ep / "carrousel"
    result = {}
    for style in styles:
        css = BASE_CSS.replace("{f_reg}", _uri(fonts / "Metropolis-Regular.ttf")).replace(
            "{f_bold}", _uri(fonts / "Metropolis-Bold.ttf")).replace("{f_xb}", _uri(fonts / "Metropolis-ExtraBold.ttf"))
        body = "".join(_slide_html(s, i, len(slides), style, ctx) for i, s in enumerate(slides, 1))
        page = f"<!doctype html><html><head><meta charset='utf-8'><style>{css}{_style_css(style)}</style></head><body>{body}{FIT_JS}</body></html>"
        d = root / style
        d.mkdir(parents=True, exist_ok=True)
        for old in d.glob("slide_*.png"):
            old.unlink()
        (d / "carrousel.html").write_text(page, encoding="utf-8")
        full = d / "_page.png"
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)          # aucune fenêtre chez l'utilisateur
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as prof:
            subprocess.run([_browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                            f"--user-data-dir={prof}", "--virtual-time-budget=8000", "--force-device-scale-factor=1",
                            f"--window-size={W},{H * len(slides)}", f"--screenshot={full}", (d / "carrousel.html").as_uri()],
                           capture_output=True, timeout=180, creationflags=flags)
        if not full.exists():
            raise SystemExit(f"Rendu Chrome échoué pour le style {style}")
        big = Image.open(full).convert("RGB")
        pngs = []
        for k in range(len(slides)):
            f = d / f"slide_{k + 1:02d}.png"
            big.crop((0, k * H, W, (k + 1) * H)).save(f)
            pngs.append(f)
        full.unlink()
        pdf = d / f"{content['episode']}_carrousel_{style}.pdf"
        ims = [Image.open(p).convert("RGB") for p in pngs]
        ims[0].save(pdf, save_all=True, append_images=ims[1:], resolution=150, quality=92)
        result[style] = pngs
    return result


def contact_sheet(brand, result: dict, out: Path) -> Path:
    """Une ligne par style : toutes ses slides en vignettes, lettre et nom du style à gauche (choix de l'équipe)."""
    from .canva_template import font
    tw, th, gap, pad, lab = 216, 270, 14, 30, 70
    n = max(len(v) for v in result.values())
    sheet = Image.new("RGB", (pad * 2 + n * tw + (n - 1) * gap, pad + len(result) * (th + lab + pad)), (245, 247, 252))
    d = ImageDraw.Draw(sheet)
    f = font(brand.assets_dir, "Montserrat", "Bold", 30)
    for r, (style, pngs) in enumerate(result.items()):
        y = pad + r * (th + lab + pad)
        d.text((pad, y), STYLES.get(style, style), font=f, fill=(21, 29, 83))
        for k, p in enumerate(pngs):
            im = Image.open(p).convert("RGB").resize((tw, th), Image.Resampling.LANCZOS)
            sheet.paste(im, (pad + k * (tw + gap), y + lab - 10))
    sheet.save(out, quality=90)
    return out


def finalize(ep: Path, content: dict, style: str, by: str = "", note: str = "") -> dict:
    """Validation par l'équipe : le style retenu devient LE carrousel de l'épisode (PDF + PNG + post)."""
    src = ep / "carrousel" / style
    pdf = src / f"{content['episode']}_carrousel_{style}.pdf"
    if not pdf.exists():
        raise SystemExit(f"Style « {style} » pas encore rendu : lancer `carousel --render`")
    final = ep / "carrousel" / "final"
    final.mkdir(parents=True, exist_ok=True)
    for old in final.glob("*"):
        old.unlink()
    import shutil
    shutil.copy2(pdf, final / f"{content['episode']}_carrousel.pdf")
    for p in sorted(src.glob("slide_*.png")):
        shutil.copy2(p, final / p.name)
    (final / "post_linkedin.md").write_text((content.get("post_final") or content.get("post", "")) + "\n", encoding="utf-8")
    rec = {"episode": content["episode"], "style": style, "angle": content.get("angle"), "validated_by": by,
           "validated_on": date.today().isoformat(), "note": note}
    (ep / "carrousel" / "carrousel_valide.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    return rec
