"""Logo AI Partners blanc ou noir selon la luminosité du haut de l'image (Arthur, 02/11/2026 : « le studio est très lumineux, on voit
mal le logo en haut ; analyse la couleur des rushs en haut : fond plutôt sombre -> logo blanc, fond clair -> logo noir »).

Une mesure par vidéo (short, teaser) ou par plan (épisode) : luminosité moyenne de la zone où le logo est posé, médiane de
quelques images. Seuil 0,5 (luminosité perceptuelle 0 à 1) : au-dessus le logo noir contraste mieux, en dessous le blanc.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

THRESHOLD = 0.5
# zone du logo (x0, x1, y0, y1) en fraction de l'image : barre centrée des shorts, coin haut droit du 16:9
BOXES = {"bar": (0.18, 0.82, 0.0, 0.11), "top-right": (0.68, 1.0, 0.0, 0.14), "top-left": (0.0, 0.32, 0.0, 0.14)}


def box_luminance(img: np.ndarray, box: tuple[float, float, float, float]) -> float:
    """Luminosité moyenne (0 noir, 1 blanc) de la zone `box` d'une image BGR."""
    h, w = img.shape[:2]
    x0, x1, y0, y1 = box
    zone = img[int(h * y0):max(int(h * y1), int(h * y0) + 1), int(w * x0):max(int(w * x1), int(w * x0) + 1)]
    b, g, r = zone[..., 0].astype(float), zone[..., 1].astype(float), zone[..., 2].astype(float)
    return float((0.114 * b + 0.587 * g + 0.299 * r).mean() / 255.0)


def video_luminance(video: Path, t0: float, t1: float, box: tuple[float, float, float, float], n: int = 5) -> float | None:
    """Médiane de la luminosité de `box` sur `n` images réparties entre t0 et t1 ; None si aucune image lisible."""
    from .ingest import _frame

    vals = []
    for i in range(n):
        t = t0 + (t1 - t0) * (i + 0.5) / n
        img = _frame(Path(video), max(0.0, t), 480)
        if img is not None:
            vals.append(box_luminance(img, box))
    return float(np.median(vals)) if vals else None


def is_light(lum: float | None, threshold: float = THRESHOLD) -> bool:
    return lum is not None and lum >= threshold


def pick_logo(brand, lum: float | None, cfg_logo=None) -> tuple[Path | None, str]:
    """(fichier du logo, « clair » | « sombre ») : le logo noir (`logo.file_on_light`) sur un fond clair, sinon le logo normal (blanc)."""
    cfg_logo = cfg_logo if cfg_logo is not None else brand.cfg.logo
    base = brand.asset(cfg_logo.get("file"))
    on_light = brand.asset(cfg_logo.get("file_on_light"))
    if on_light and cfg_logo.get("auto_tone", True) and is_light(lum, float(cfg_logo.get("light_threshold", THRESHOLD))):
        return on_light, "clair"
    return base, "sombre"
