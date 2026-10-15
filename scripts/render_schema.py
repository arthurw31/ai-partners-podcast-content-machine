#!/usr/bin/env python
"""Schéma du process (v2) -> images affichées par le README.

Le schéma est une page interactive (Arthur, 15/10/2026 : vue d'ensemble synthétique, un clic sur un process ouvre son détail,
une case « schéma complet » montre tous les process côte à côte avec leurs dépendances) :
- docs/v2/process.js  : SEULE source du contenu (process, étapes, boucles, dépendances) ;
- docs/v2/index.html  : la page qui dessine tout à partir de process.js (rien à y changer quand le process change) ;
- publiée par GitHub Pages : https://arthurw31.github.io/ai-partners-podcast-content-machine/ (redirige vers v2/).

GitHub n'exécute pas de page dans un README : ce script en prend deux captures avec Chrome sans fenêtre
- docs/v2/apercu.png          : la vue d'ensemble (image du README, cliquable vers la page) ;
- docs/v2/schema_complet.png  : le schéma complet avec les dépendances.
L'empreinte des deux sources est écrite dans docs/v2/images.sha256 : `check_schema.py` signale des images périmées.

    python scripts/render_schema.py        (~10 s)
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
V2 = ROOT / "docs" / "v2"
SOURCES = [V2 / "process.js", V2 / "index.html"]
SHA = V2 / "images.sha256"
SHOTS = [("", 1300, V2 / "apercu.png"), ("#tout", 1400, V2 / "schema_complet.png")]
BG = (244, 246, 251)                      # fond de la page (--bg) : rogné sous le contenu


def source_hash() -> str:
    h = hashlib.sha256()
    for f in SOURCES:
        h.update(f.read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()


def shot(fragment: str, width: int, out: Path) -> None:
    sys.path.insert(0, str(ROOT))
    from PIL import Image, ImageChops
    from clipper.thumbnail import _browser
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        raw = Path(td) / "raw.png"
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)              # aucune fenêtre chez l'utilisateur
        subprocess.run([_browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                        f"--user-data-dir={Path(td) / 'prof'}", "--virtual-time-budget=6000", "--force-device-scale-factor=1",
                        f"--window-size={width},3200", f"--screenshot={raw}", (V2 / "index.html").as_uri() + fragment],
                       capture_output=True, timeout=120, creationflags=flags)
        if not raw.exists():
            raise SystemExit(f"Capture Chrome échouée : {out.name}")
        im = Image.open(raw).convert("RGB")
        box = ImageChops.difference(im, Image.new("RGB", im.size, BG)).getbbox()
        bottom = min(im.height, (box[3] if box else im.height) + 40)
        im.crop((0, 0, im.width, bottom)).save(out, optimize=True)


def main() -> int:
    for fragment, width, out in SHOTS:
        shot(fragment, width, out)
        print(f"{out.relative_to(ROOT)} : {out.stat().st_size // 1024} Ko")
    SHA.write_text(source_hash() + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
