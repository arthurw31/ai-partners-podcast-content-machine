"""Rédaction des textes de publication de chaque clip : TROIS textes par short (Arthur, 21/10/2026 : « on poste sur plusieurs
plateformes » : un post LinkedIn en français, le même en anglais, et un texte français pour Instagram / TikTok / YouTube Shorts).

Entrées : clips.json, transcript.json, le brief `MARQUES/<slug>/posts.md` (règles + posts publiés
servant de référence de ton) et la section « Publication » de guidelines.md.
Sortie  : EPISODES/<marque>/<épisode>/travail/posts/clip_NN_<titre>.md (un fichier par clip), les champs
`linkedin_post` (anglais), `linkedin_post_fr` et `social_post_fr` dans clips.json, et le récap dans summary.md.
Le texte « réseaux » finit toujours par la présentation d'AI Partners + l'invitation à s'abonner à la chaîne YouTube,
ajoutées par le programme (`publication.social_fr` de brand.yaml), jamais par le modèle. Jamais de tiret cadratin.

Un seul appel LLM pour tous les clips de l'épisode : le modèle voit l'ensemble et varie les
angles / structures d'un post à l'autre (pas six posts « Nouvel épisode »).
"""
from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console

from .config import Brand
from .llm import ask_json
from .transcribe import words_between

console = Console()

SYSTEM_PROMPT = """Tu es le community manager d'un podcast. Pour chaque clip vidéo (extrait monté d'un épisode)
tu rédiges TROIS textes qui l'accompagnent sur les réseaux :

1. `linkedin_post` : le post LinkedIn en ANGLAIS, prêt à coller, qui suit STRICTEMENT la méthode « post d'un short »
   du brief (accroche, contraste, invité, développement concret, chute, puis CTA vers l'épisode). Voix « we » de la page.
2. `linkedin_post_fr` : le MÊME post LinkedIn en FRANÇAIS : même idée, même structure, même CTA (en français, avec le
   même lien), mais formulé naturellement en français (pas une traduction mot à mot). Voix « nous ».
3. `social_post_fr` : le texte pour Instagram / TikTok / YouTube Shorts, en FRANÇAIS, dans le style des exemples
   « Instagram / TikTok / YouTube Shorts » du brief : la 1re ligne est la thèse du short entre guillemets français
   « … », puis des paragraphes courts (le contraste, l'idée de la personne qui parle, le concret), puis la chute en une
   ligne. AUCUN emoji, AUCUN hashtag, AUCUN lien, AUCUN CTA : la présentation d'AI Partners, l'invitation à s'abonner à la
   chaîne YouTube et le lien du podcast sont ajoutés après par le programme, ne les écris pas.

Règles absolues :
- Les trois textes portent L'IDÉE DU CLIP (ce qui se dit dans cet extrait précis), reformulée avec ses mots-clés,
  pas un résumé générique de l'épisode. Mêmes faits dans les trois, formulations différentes.
- JAMAIS de tiret cadratin « — » ni demi-cadratin « – » dans aucun des trois textes (règle de la marque) : une virgule,
  deux-points, des parenthèses ou deux phrases.
- Attribue chaque idée à la personne qui la dit dans la transcription (animateur ou invité). Quand c'est
  l'animateur qui pose l'idée et l'invité qui réagit, les textes le reflètent (« Thomas Spitz asked… », « dans notre
  échange avec … »), jamais « l'invité explique » pour des mots de l'animateur.
- Ne jamais inventer un chiffre, un nom de client, une citation ou un fait absent de la transcription du clip, ni
  une conclusion que personne ne formule dans le clip. Une citation entre guillemets doit être fidèle à la transcription.
- La CHUTE et chaque transition reformulent ce que dit le clip ; elles n'ajoutent ni définition, ni morale, ni jugement
  que personne ne formule dans l'extrait (21/10/2026 : « le muscle du changement, c'est permettre à l'organisation d'absorber… »
  avait été inventé). En cas de doute, terminer sur la question ou la phrase d'ouverture du clip.
- Suis la méthode « post d'un short » du brief ; les formats d'annonce d'épisode (nouvel épisode, preview) ne
  s'utilisent que si le contexte le demande explicitement.
- Varie les structures entre les clips d'un même épisode (forme de l'accroche, place de l'invité, formulation du
  CTA) ; deux posts ne doivent pas commencer de la même façon.
- Si une URL d'épisode est fournie, elle apparaît en clair dans le CTA des deux posts LinkedIn ; sinon applique la consigne du brief
  (« lien en commentaire » ou équivalent). Ne fabrique jamais d'URL.
- Les sauts de ligne sont des `\\n` dans la chaîne JSON.
- Réponds UNIQUEMENT avec un objet JSON valide de la forme :
{"posts": [{"index": 1, "variant": "citation|constat|question", "linkedin_post": "…", "linkedin_post_fr": "…", "social_post_fr": "…"}]}"""


def _clip_text(transcript: dict, clip: dict, host: str = "", guest: str = "") -> str:
    """Transcription du clip, segment par segment, avec QUI parle (tours de parole du clip) : sans ça, le
    modèle attribue à l'invité des idées lancées par l'animateur."""
    turns = sorted(clip.get("turns") or [], key=lambda t: float(t["at"]))
    names = {"host": f"{host or 'Animateur'} (animateur)", "guest": f"{guest or 'Invité'} (invité)"}

    def speaker(t: float) -> str:
        cur = turns[0]["speaker"] if turns else ""
        for tr in turns:
            if float(tr["at"]) <= t + 0.05:
                cur = tr["speaker"]
        return cur

    def line(spk: str, words: list[str]) -> str:
        return (f"{names.get(spk, '?')} : " if turns else "") + " ".join(words)

    parts = []
    for sg in clip.get("segments") or [{"start": clip["start"], "end": clip["end"]}]:
        lines, cur, buf = [], None, []
        for w in words_between(transcript, float(sg["start"]), float(sg["end"])):
            spk = speaker(w["s"])
            if spk != cur and buf:
                lines.append(line(cur, buf))
                buf = []
            cur = spk
            buf.append(w["w"])
        if buf:
            lines.append(line(cur, buf))
        parts.append("\n".join(lines))
    return "\n[…]\n".join(p for p in parts if p)


def _publication_rules(guidelines: str) -> str:
    """Section « ## Publication » de guidelines.md (hashtags, longueur…), si elle existe."""
    if "## Publication" not in guidelines:
        return ""
    sect = guidelines.split("## Publication", 1)[1]
    return sect.split("\n## ", 1)[0].strip()


def write_posts(brand: Brand, ep: Path, clips: dict, transcript: dict, episode_url: str = "",
                only: set[int] | None = None, force: bool = False) -> dict:
    cfg = brand.cfg
    pub = cfg.get("publication") or {}
    if not pub.get("enabled", True):
        console.print("[dim]publication.enabled: false → pas de posts[/dim]")
        return clips
    posts_dir = ep / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)
    # lien du podcast sur YouTube : donné une fois (`--episode-url`), mémorisé dans clips.json, repris aux relances
    episode_url = episode_url or str(clips.get("episode_url") or "") or str(pub.get("episode_url") or "")
    if episode_url:
        clips["episode_url"] = episode_url

    targets = [c for c in clips["clips"] if not only or c["index"] in only]
    todo = [c for c in targets if force or not all(c.get(k) for k in TEXT_KEYS)]
    if not todo:
        console.print(f"[dim]Posts en cache : {posts_dir}[/dim]")
        if _add_contact(targets, pub) | _add_social_outro(targets, pub, clips, episode_url):
            (ep / "clips.json").write_text(json.dumps(clips, ensure_ascii=False, indent=1), encoding="utf-8")
        _write_files(posts_dir, targets, clips)
        return clips

    brief = brand.posts_brief or "(aucun brief : langue du podcast, ton professionnel, 100–150 mots, CTA vers l'épisode complet)"
    guest, company = clips.get("guest", ""), clips.get("company", "")
    clips_txt = []
    for c in todo:
        clips_txt.append(
            f"### Clip {c['index']} — {c.get('title', '')}\n"
            f"- accroche : {c.get('hook_title', '')}\n"
            f"- pourquoi cet extrait : {c.get('why', '')}\n"
            f"- durée : {c.get('duration', 0):.0f}s\n"
            f"- transcription (avec qui parle) :\n{_clip_text(transcript, c, str(pub.get('host_name') or ''), guest)}\n"
        )
    user = f"""## Brief posts de la marque « {cfg.name} »
{brief}

## Consignes « Publication » des guidelines éditoriales
{_publication_rules(brand.guidelines) or "(aucune)"}

## Contexte
- Podcast : {cfg.get('podcast_name') or cfg.name} · Animateur·ice : {pub.get('host_name') or 'voir brief'}
- Invité : {guest or 'inconnu'} · Rôle : {clips.get('guest_role') or pub.get('guest_role') or 'inconnu'} · Entreprise : {company or 'inconnue'}
- Rôle en français : {clips.get('guest_role_fr') or clips.get('guest_role') or pub.get('guest_role') or 'inconnu'}
- Langues : post LinkedIn en anglais + le même en français + texte réseaux en français (voir le brief)
- URL de l'épisode complet : {episode_url or 'non fournie'}
- Plateformes où écouter : {pub.get('channels') or 'voir brief'}
- Nombre de clips : {len(todo)} — un post distinct par clip, structures variées.

## Les clips
{chr(10).join(clips_txt)}
"""
    data = ask_json(SYSTEM_PROMPT, user, model=str(pub.get("llm_model") or cfg.selection.llm_model),
                    backend=str(pub.get("llm_backend") or cfg.selection.llm_backend), max_tokens=8000)
    (ep / "llm_posts_raw.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    by_index = {}
    for p in data.get("posts", []) or []:
        try:
            by_index[int(p.get("index"))] = p
        except (TypeError, ValueError):
            continue
    for c in todo:
        p = by_index.get(c["index"])
        if not p:
            console.print(f"[yellow]Clip {c['index']} : pas de post dans la réponse du modèle[/yellow]")
            continue
        for k in TEXT_KEYS:
            c[k] = str(p.get(k, "")).strip()
        c.pop("short_description", None)       # ancien champ (hashtags), remplacé par social_post_fr
        c["post_variant"] = str(p.get("variant", ""))
    _add_contact(todo, pub)
    _add_social_outro(todo, pub, clips, episode_url)
    (ep / "clips.json").write_text(json.dumps(clips, ensure_ascii=False, indent=1), encoding="utf-8")
    _write_files(posts_dir, targets, clips)
    for c in todo:
        for m in check_texts(c, pub, episode_url):
            console.print(f"[yellow]Clip {c['index']} : {m}[/yellow]")
    console.print(f"[green]{len([c for c in todo if all(c.get(k) for k in TEXT_KEYS)])} clip(s) : 3 textes rédigés[/green] → {posts_dir}")
    return clips


TEXT_KEYS = ("linkedin_post", "linkedin_post_fr", "social_post_fr")   # anglais, français, réseaux (Insta / TikTok / YT Shorts)
DASH = "\u2014\u2013"                                                    # tiret cadratin et demi-cadratin : interdits


def language_of(cfg, pub: dict, transcript: dict) -> str:
    return str(pub.get("language") or "") or str(cfg.get("language") or transcript.get("language") or "fr")


def contact_line(pub: dict, language: str) -> str:
    """Ligne « travailler avec nous » ajoutée telle quelle à la fin des textes publiés (pas laissée au LLM)."""
    cta = pub.get("contact_cta") or {}
    if not cta.get("enabled", True) or not cta.get("url"):
        return ""
    text = cta.get(f"text_{language[:2]}") or cta.get("text_en") or cta.get("text_fr") or ""
    return f"{text} {cta['url']}".strip()


def _add_contact(clips_list: list[dict], pub: dict) -> bool:
    """Ajoute la ligne de contact aux deux posts LinkedIn (EN / FR), idempotent. Désactivé tant qu'Arthur ne l'a pas demandé."""
    changed = False
    for key, lang in (("linkedin_post", "en"), ("linkedin_post_fr", "fr")):
        line = contact_line(pub, lang)
        if not line:
            continue
        for c in clips_list:
            if c.get(key) and str(pub["contact_cta"]["url"]) not in c[key]:
                c[key] = c[key].rstrip() + "\n\n" + line
                changed = True
    return changed


def guest_line(clips: dict) -> str:
    """« Prénom Nom, Rôle chez Entreprise » (rôle en français), pour la phrase d'abonnement."""
    guest, company = clips.get("guest", ""), clips.get("company", "")
    role = clips.get("guest_role_fr") or ""
    if guest and role and company:
        return f"{guest}, {role} chez {company}"
    return f"{guest} ({company})" if guest and company else (guest or company)


def social_outro(pub: dict, clips: dict, episode_url: str = "") -> str:
    """Fin FIXE du texte Instagram / TikTok / YouTube Shorts (Arthur, 21/10/2026) : la présentation d'AI Partners, l'invitation à
    s'abonner à la chaîne YouTube avec le dernier podcast, puis le LIEN du podcast (Arthur, 21/10/2026 : « il me faut le lien du
    podcast YouTube en lien cliquable dans les textes » ; YouTube Shorts le rend cliquable, Instagram et TikTok demandent le lien
    en bio). Écrite par le programme, jamais par le modèle."""
    s = pub.get("social_fr") or {}
    about, sub = str(s.get("about") or "").strip(), str(s.get("subscribe") or "").strip()
    link = str(s.get("link_line") or "").strip().replace("{episode_url}", episode_url) if episode_url else ""
    return "\n\n".join(x for x in (about, sub.replace("{guest_line}", guest_line(clips)), link) if x)


def _add_social_outro(clips_list: list[dict], pub: dict, clips: dict, episode_url: str = "") -> bool:
    """Ajoute la fin fixe (idempotent) ; si le texte l'a déjà mais pas le lien, ajoute seulement la ligne du lien."""
    s = pub.get("social_fr") or {}
    out, changed = social_outro(pub, clips, episode_url), False
    if not out:
        return False
    marker = str(s.get("about") or "")[:40]
    link = str(s.get("link_line") or "").strip().replace("{episode_url}", episode_url) if episode_url else ""
    for c in clips_list:
        body = c.get("social_post_fr")
        if not body:
            continue
        if marker not in body:
            c["social_post_fr"] = body.rstrip() + "\n\n" + out
            changed = True
        elif link and episode_url not in body:
            c["social_post_fr"] = body.rstrip() + "\n\n" + link
            changed = True
    return changed


def _has_emoji(s: str) -> bool:
    import re
    return bool(re.search("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]", s))


def check_texts(c: dict, pub: dict, episode_url: str = "") -> list[str]:
    """Contrôle des trois textes d'un clip ; renvoie les problèmes (liste vide = OK).
    Règles : les trois textes existent ; jamais de tiret cadratin ; pas de hashtag ; texte réseaux = français, 1re ligne entre
    « », ni emoji ni lien, et il finit par la phrase d'abonnement ; les posts LinkedIn portent le lien de l'épisode (s'il est
    connu) ; une langue ne se mélange pas avec l'autre."""
    import re
    out: list[str] = []
    for k in TEXT_KEYS:
        v = c.get(k) or ""
        if not v.strip():
            out.append(f"texte manquant : {k}")
            continue
        if any(ch in v for ch in DASH):
            out.append(f"{k} : tiret cadratin interdit")
        if re.search(r"(?<!\w)#\w", v):
            out.append(f"{k} : hashtag (la marque n'en met pas)")
    soc = c.get("social_post_fr") or ""
    if soc:
        if not soc.lstrip().startswith("\u00ab"):
            out.append("social_post_fr : la 1re ligne doit être la thèse entre « »")
        if _has_emoji(soc):
            out.append("social_post_fr : pas d'emoji")
        url0 = episode_url or str(c.get("episode_url") or "") or str(pub.get("episode_url") or "")
        import re as _re
        autres = [u for u in _re.findall(r"https?://\S+", soc) if not url0 or u.rstrip(".,;)") != url0]
        if autres:
            out.append("social_post_fr : un seul lien autorisé, celui du podcast YouTube (ajouté par le programme)")
        if url0 and url0 not in soc:
            out.append("social_post_fr : lien du podcast YouTube absent (il doit finir le texte, sans ponctuation collée)")
        sub = str((pub.get("social_fr") or {}).get("subscribe") or "")[:25]
        if sub and sub not in soc:
            out.append("social_post_fr : phrase d'abonnement absente")
    url = episode_url or str(pub.get("episode_url") or "")
    if url:
        for k in ("linkedin_post", "linkedin_post_fr"):
            if c.get(k) and url not in c[k]:
                out.append(f"{k} : lien de l'épisode absent")
    en = (c.get("linkedin_post") or "").lower()
    if len(re.findall(r"\b(les|des|une|est|nous|pour)\b", en)) > 6:
        out.append("linkedin_post : semble contenir du français (il doit être en anglais)")
    for k in ("linkedin_post_fr", "social_post_fr"):
        fr = (c.get(k) or "").lower()
        if len(re.findall(r"\b(the|and|with|our|that)\b", fr)) > 4:
            out.append(f"{k} : semble contenir de l'anglais (il doit être en français)")
    return out


def _write_files(posts_dir: Path, clips_list: list[dict], clips: dict) -> None:
    from .compose import slugify

    for c in clips_list:
        if not c.get("linkedin_post"):
            continue
        name = f"clip_{c['index']:02d}_{slugify(c.get('title', ''))}.md"
        body = [f"# Clip #{c['index']} · {c.get('title', '')}", "",
                f"Invité : {clips.get('guest', '')} ({clips.get('company', '')}) · durée {c.get('duration', 0):.0f}s",
                "", "## Post LinkedIn (français)", "", c.get("linkedin_post_fr", ""), "",
                "## Post LinkedIn (English)", "", c["linkedin_post"], "",
                "## Instagram / TikTok / YouTube Shorts (français)", "", c.get("social_post_fr", ""), ""]
        (posts_dir / name).write_text("\n".join(body), encoding="utf-8")
