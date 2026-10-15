#!/usr/bin/env python
"""Vérifie que le schéma du process suit le code (règle d'Arthur, 09/10/2026 : « mets à jour le schéma d'architecture à chaque fois
qu'on modifie le process » ; le schéma de référence est celui de GitHub, affiché par le README). À lancer avant de commiter
toute modification du process ; code de sortie 1 si un oubli est détecté.

Le schéma (v2, depuis le 15/10/2026) : contenu dans `docs/v2/process.js`, page `docs/v2/index.html`, images du README
`docs/v2/apercu.png` et `schema_complet.png` (`python scripts/render_schema.py`). Contrôles :
1. chaque commande du CLI figure dans la liste « commandes » de docs/ARCHITECTURE.md ;
2. chaque commande qui est une ÉTAPE du process (PROCESS) est citée dans process.js ;
3. process.js cite les validations humaines (HUMAN_GATES) ;
4. process.js est cohérent : acteurs connus, boucles qui reviennent EN ARRIÈRE dans le même process, dépendances qui pointent
   vers des étapes qui existent et qui partent d'une validation de l'équipe ;
5. le README affiche docs/v2/apercu.png et les images ont été régénérées depuis les sources actuelles (empreinte).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_schema import SHA, V2, source_hash  # noqa: E402

SRC = V2 / "process.js"
# commandes qui sont une étape du process (les autres : utilitaires, sous-étapes de `polish`, recours)
PROCESS = ["livraison", "rushes", "transcribe", "propose", "pick", "polish", "qa", "render", "posts", "episode-plan", "episode-render",
           "titles", "thumbnail", "thumbnail-template", "outro", "carousel", "newsletter", "review"]
HUMAN_GATES = ["titles --pick", "thumbnail --pick", "carousel --pick", "carousel --final", "newsletter --final"]
ACTORS = {"claude", "equipe", "auto", "entree", "livrable"}


def cli_commands() -> list[str]:
    out = subprocess.run([sys.executable, "-m", "clipper", "-h"], cwd=ROOT, capture_output=True, text=True,
                         encoding="utf-8", errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"}).stdout
    m = re.search(r"\{([a-z0-9,-]+)\}", out)
    if not m:
        sys.exit("Impossible de lire la liste des commandes (python -m clipper -h)")
    return m.group(1).split(",")


def mentions(text: str, cmd: str) -> bool:
    return re.search(rf"(?<![\w-]){re.escape(cmd)}(?![\w-])", text) is not None


def load_process() -> dict:
    """process.js est du JavaScript (window.PROCESS = …) : Node le lit tel que le navigateur le lira."""
    js = f"global.window={{}};require({json.dumps(str(SRC))});process.stdout.write(JSON.stringify(window.PROCESS))"
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        sys.exit(f"docs/v2/process.js illisible (erreur JavaScript) :\n{r.stderr[-800:]}")
    return json.loads(r.stdout)


def structure(P: dict) -> list[str]:
    out, ids = [], {}
    for p in P["processes"]:
        if p["id"] in ids:
            out.append(f"process.js : identifiant de process en double `{p['id']}`")
        ids[p["id"]] = p
        for i, s in enumerate(p["steps"]):
            where = f"process.js : {p['title']}, étape {i + 1} « {s.get('title')} »"
            if s.get("actor") not in ACTORS:
                out.append(f"{where} : acteur inconnu `{s.get('actor')}` ({', '.join(sorted(ACTORS))})")
            loop = s.get("loop")
            if loop and not (0 <= loop.get("to", -1) < i):
                out.append(f"{where} : la boucle doit revenir à une étape PRÉCÉDENTE (to = numéro d'étape - 1, à partir de 0)")
    for m in P.get("milestones", []):
        for ref, kind in [(m["from"], "départ")] + [(u, "arrivée") for u in m["unlocks"]]:
            p = ids.get(ref["proc"])
            if not p or not (0 <= ref["step"] < len(p["steps"])):
                out.append(f"process.js : dépendance « {m['title']} » : {kind} vers une étape qui n'existe pas ({ref})")
            elif kind == "départ" and p["steps"][ref["step"]]["actor"] != "equipe":
                out.append(f"process.js : dépendance « {m['title']} » : doit partir d'une validation de l'équipe")
    return out


def main() -> int:
    cmds = cli_commands()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    arch = (ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")
    text = SRC.read_text(encoding="utf-8") if SRC.exists() else ""
    cli_row = next((l for l in arch.splitlines() if "commandes :" in l), "")
    problems: list[str] = []
    for c in cmds:
        if not mentions(cli_row, c):
            problems.append(f"docs/ARCHITECTURE.md : la commande `{c}` manque dans la liste « commandes » du bloc cli.py")
    for c in PROCESS:
        if c not in cmds:
            problems.append(f"scripts/check_schema.py : `{c}` n'est plus une commande (mettre PROCESS à jour)")
        elif not mentions(text, c):
            problems.append(f"docs/v2/process.js : l'étape `{c}` n'est pas dans le schéma (champ cmd ou details d'une étape)")
    for g in HUMAN_GATES:
        if g not in text:
            problems.append(f"docs/v2/process.js : la validation humaine `{g}` n'est pas dans le schéma")
    P = load_process()
    problems += structure(P)
    if "docs/v2/apercu.png" not in readme:
        problems.append("README.md : l'image docs/v2/apercu.png n'est plus affichée")
    if not SHA.exists() or SHA.read_text(encoding="utf-8").strip() != source_hash():
        problems.append("docs/v2/apercu.png : images périmées, lancer `python scripts/render_schema.py`")
    if problems:
        print("Le schéma n'est pas à jour avec le process :")
        print("\n".join(f"  - {p}" for p in problems))
        return 1
    n = sum(len(p["steps"]) for p in P["processes"])
    print(f"Schéma à jour : {len(cmds)} commandes, {len(P['processes'])} process, {n} étapes, "
          f"{len(P.get('milestones', []))} dépendances, {len(HUMAN_GATES)} validations humaines, images régénérées.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
