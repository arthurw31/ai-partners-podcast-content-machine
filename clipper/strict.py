"""Contrôle intransigeant (Arthur, 12/10/2026 : « il y a parfois des petits accrocs quand même, des sous-titres qui se
chevauchent ou des phrases coupées légèrement trop tôt — il faudrait vraiment une boucle de vérification intransigeante »).

Ce que la QA « classique » laissait passer :
- une fin de phrase coupée pendant que la voix S'ÉTEINT (dernière syllabe à 10–20 % du niveau de parole : sous le seuil de
  `qa._voice_at`, mais audible : « coupé un peu trop tôt ») ;
- deux blocs de sous-titres affichés en même temps (durée minimale d'un bloc qui débordait sur le suivant).

Ici, tout est jugé sur le SON du micro (fins / débuts de passage) et sur la COMPOSITION réellement rendue (sous-titres), avec
des seuils durs, et `fix_edges` corrige seul ce qui peut l'être (fin prolongée jusqu'au vrai silence, début avancé jusqu'au
silence qui précède) ; `polish` boucle (3 tours au plus) tant qu'il reste un défaut corrigeable. Un défaut qui ne se corrige
pas reste en ÉCHEC : rien ne part en rendu.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import numpy as np

from .media import FFMPEG

FRAME = 0.02          # trames d'énergie de tighten._rms (20 ms)
END_HOLD = 0.12       # une fin est propre si la voix est retombée sous END_THR pendant les 0,12 s avant la coupe
END_THR = 0.10        # … 10 % du niveau de parole (90e centile des 1,5 s précédentes) ; qa._voice_at tolère 20 %
START_HOLD = 0.06     # un début est propre s'il part d'un silence d'au moins 0,06 s (< START_THR)
START_THR = 0.12
JOIN_HOLD = 0.04      # fin de phrase INTERNE (une autre phrase suit au montage) : la suite masque un souffle ; la voix doit
JOIN_THR = 0.15       # seulement être retombée (E22 short 1 : « …à venir. ‖ Et puis », 0,08 s de silence dans la source)
MAX_EXT = 0.6         # correction : fin prolongée au plus de 0,6 s, début avancé au plus de 0,4 s
MAX_BACK = 0.4


def _rms(wav: Path, a: float, b: float) -> np.ndarray:
    from .tighten import _rms as r
    return r(wav, max(0.0, a), b)


def _level(wav: Path, t: float) -> float:
    r = _rms(wav, t - 1.5, t + 1.5)
    return float(np.percentile(r, 90)) if len(r) >= 10 else 0.0


def end_ratio(wav: Path, t: float, hold: float = END_HOLD) -> float:
    """Énergie maximale des `hold` s avant la coupe, en fraction du niveau de parole (0 = silence, 1 = pleine voix)."""
    lvl = _level(wav, t - 1.0)
    r = _rms(wav, t - hold, t)
    return float(r.max() / lvl) if lvl > 0 and len(r) else 0.0


def start_ratio(wav: Path, t: float, hold: float = START_HOLD) -> float:
    lvl = _level(wav, t + 1.0)
    r = _rms(wav, t, t + hold)
    return float(r.max() / lvl) if lvl > 0 and len(r) else 0.0


def passage_edges(segs: list[dict]) -> tuple[list[int], list[int]]:
    """Indices des segments qui FINISSENT une phrase (end_text, ou le dernier) et qui en COMMENCENT une (start_text, ou le
    premier). Les autres bords sont des retraits de « euh » au point le plus calme, contrôlés à l'écoute (`audit_joins`)."""
    ends = sorted({k for k, s in enumerate(segs) if s.get("end_text")} | {len(segs) - 1})
    starts = sorted({k for k, s in enumerate(segs) if s.get("start_text")} | {0})
    return ends, starts


def edge_problems(segs: list[dict], wav: Path) -> list[dict]:
    """[{k, kind: 'fin'|'début', t, ratio}] : bords de phrase coupés dans la voix (seuils durs ci-dessus)."""
    ends, starts = passage_edges(segs)
    out = []
    for k in ends:
        t = float(segs[k]["end"])
        last = k == len(segs) - 1
        # fin du short suivie DE PRÈS par un autre son dans la source (≤ 0,12 s : souffle, « Ouais » de l'autre) : impossible
        # d'avoir 0,12 s de silence -> même règle qu'un raccord interne (short 5 E22, « …en bon escient. » / « Ouais », 12/10)
        if last:
            lvl = _level(wav, t - 1.0)
            nxt = _rms(wav, t, t + 0.12)
            # … SEULEMENT si la voix est déjà retombée au point de coupe (sinon c'est la même voix qui continue, en plein mot :
            # « productivi-té » — 13/10/2026, le test anti-régression l'a vu)
            if lvl > 0 and len(nxt) and float(nxt.max()) > END_THR * lvl and end_ratio(wav, t, JOIN_HOLD) < JOIN_THR:
                last = False
        hold, thr = (END_HOLD, END_THR) if last else (JOIN_HOLD, JOIN_THR)
        x = end_ratio(wav, t, hold)
        if x >= thr:
            out.append({"k": k, "kind": "fin", "t": t, "ratio": round(x, 2), "hold": hold, "thr": thr})
    for k in starts:
        t = float(segs[k]["start"])
        x = start_ratio(wav, t)
        if x >= START_THR and _valley(wav, t):   # début au creux entre un « euh » collé et le mot : rien de mieux possible
            continue
        if x >= START_THR:
            out.append({"k": k, "kind": "début", "t": t, "ratio": round(x, 2)})
    return out


def _valley(wav: Path, t: float, around: float = 0.3, max_ratio: float = 0.3) -> bool:
    """t est-il au CREUX d'énergie entre deux sons collés (aucun silence à moins de `around` s : « euh » enchaîné sur le
    mot) ? Vrai si la voix y descend sous `max_ratio` du niveau et que c'est le point le plus bas des environs (± 0,04 s).
    Short 4 E22 : « euh, ‖ là où » — 22 % à 579,08, aucun silence entre les deux (12/10/2026)."""
    lvl = _level(wav, t)
    r = _rms(wav, t - around, t + 0.1)
    if lvl <= 0 or len(r) < 5:
        return False
    q = r < START_THR * lvl
    n = max(1, int(round(START_HOLD / FRAME)))
    # un vrai silence (≥ START_HOLD d'affilée) existe à côté : la correction doit aller le chercher. Des trames calmes
    # ISOLÉES ne suffisent pas (15/10/2026, short 1 E21 : « euh ‖ tu galères », une seule trame à 8 % entre les deux)
    if any(q[i:i + n].all() for i in range(0, len(q) - n + 1)):
        return False
    i = int(round(around / FRAME))
    lo = max(0, i - 2)
    return float(r[lo:i + 2].min()) <= max_ratio * lvl and float(r[lo:i + 2].min()) <= float(r.min()) * 1.05


def _fix_end(wav: Path, t: float, limit: float, hold: float = END_HOLD, thr: float = END_THR) -> float | None:
    """Fin recalée dans le vrai silence : d'abord EN AVANT (≤ t + MAX_EXT, ≤ limit) jusqu'à ce que la voix soit retombée sous
    `thr` depuis `hold`, à condition qu'aucun NOUVEAU son ne démarre entre-temps (sinon on avalerait le mot suivant) ; sinon
    EN ARRIÈRE (≤ 0,3 s) si la coupe est tombée sur le début d'un nouveau son précédé d'un vrai silence. None : la voix
    continue (phrase pas finie : à traiter à la main)."""
    lvl = _level(wav, t - 1.0)
    if lvl <= 0:
        return None
    n = max(1, int(round(hold / FRAME)))
    r = _rms(wav, t - hold, t + MAX_EXT)
    if len(r) > n:
        q = r < thr * lvl
        quiet_run = 0          # silence vu APRÈS la coupe (une occlusion dans le mot, avant la coupe, ne compte pas :
        for i in range(n, len(r) + 1):   # « productivi-t-é », 0,04 s à 6 %, teaser E22)
            if q[i - n:i].all():
                k = i
                while k < min(len(r), i + 3) and q[k]:   # + un souffle (≤ 0,06 s) SEULEMENT tant que le silence dure
                    k += 1
                nt = t - hold + k * FRAME
                if k < len(r) and not q[k] and k > i - 1:   # un son repart juste après : une trame de marge avant lui
                    nt -= FRAME
                return round(min(nt, limit), 3) if t - hold + i * FRAME <= limit else None
            x = float(r[i - 1])
            if i - 1 >= n:                                      # trame après la coupe
                if x < 0.15 * lvl:
                    quiet_run += 1
                elif quiet_run >= 3 and x > 0.3 * lvl:          # vrai silence (≥ 0,06 s) puis un nouveau son : le mot suivant
                    break
                else:
                    quiet_run = 0
    rb = _rms(wav, t - 0.3, t)
    q = rb < thr * lvl
    for i in range(len(rb), n - 1, -1):          # en reculant : dernier silence de `hold` avant la coupe
        if q[i - n:i].all():
            return round(t - 0.3 + i * FRAME - 0.02, 3)
    return None


def _fix_start(wav: Path, t: float, limit: float) -> float | None:
    """Début recalé dans un silence : d'abord EN AVANT (≤ 0,25 s) si l'on démarre sur la traîne d'un son qui s'éteint avant
    le 1er mot (E22 short 1 : fin d'hésitation à 2228,67, « Et donc » à 2228,82) ; sinon EN ARRIÈRE (≤ MAX_BACK)."""
    lvl = _level(wav, t + 1.0)
    if lvl <= 0:
        return None
    n = max(1, int(round(START_HOLD / FRAME)))
    rf = _rms(wav, t, t + 0.25 + START_HOLD)
    qf = rf < START_THR * lvl
    for j in range(0, len(rf) - n + 1):
        if qf[j:j + n].all():
            if (rf[:j] > START_THR * lvl).any() and not (rf[:j] > 0.5 * lvl).any():   # traîne faible, pas un mot
                return round(t + j * FRAME, 3)
            break
    r = _rms(wav, t - MAX_BACK, t + START_HOLD)
    if len(r) < 3:
        return None
    q = r < START_THR * lvl
    for j in range(len(r) - n, -1, -1):           # en reculant depuis t : premier silence de START_HOLD
        if q[j:j + n].all():
            nt = t - MAX_BACK + j * FRAME
            return round(nt, 3) if nt >= limit else None
    return None


def fix_edges(segs: list[dict], wav: Path) -> tuple[list[dict], list[str], list[str]]:
    """Corrige les bords de phrase coupés dans la voix. Renvoie (segments, corrections faites, défauts restants)."""
    segs_in = [dict(s) for s in segs]
    segs = [dict(s) for s in segs]
    done, left = [], []
    for p in edge_problems(segs, wav):
        k = p["k"]
        if p["kind"] == "fin":
            nxt = [float(s["start"]) for s in segs if float(s["start"]) > float(segs[k]["end"]) - 0.01]
            limit = min(nxt) - 0.02 if nxt else p["t"] + MAX_EXT
            nt = _fix_end(wav, p["t"], limit, p["hold"], p["thr"])
            if nt and abs(nt - p["t"]) > 0.005 and nt > float(segs[k]["start"]) + 0.3:
                segs[k]["end"] = nt
                done.append(f"fin {p['t']:.2f} -> {nt:.2f} (la voix s'éteignait encore : {int(p['ratio'] * 100)} %)")
            else:
                left.append(f"fin à {p['t']:.2f} : la voix continue ({int(p['ratio'] * 100)} % du niveau) — phrase pas finie")
        else:
            prv = [float(s["end"]) for s in segs if float(s["end"]) < float(segs[k]["start"]) + 0.01]
            limit = max(prv) + 0.02 if prv else p["t"] - MAX_BACK
            nt = _fix_start(wav, p["t"], limit)
            if nt is not None and abs(nt - p["t"]) > 0.005 and nt < float(segs[k]["end"]) - 0.3:
                segs[k]["start"] = nt
                done.append(f"début {p['t']:.2f} -> {nt:.2f} (départ dans un son : {int(p['ratio'] * 100)} %)")
            else:
                left.append(f"début à {p['t']:.2f} : démarre dans la voix ({int(p['ratio'] * 100)} %)")
    for s in segs:
        s["duration"] = round(float(s["end"]) - float(s["start"]), 3)
    # chaque correction est REVÉRIFIÉE : si le bord reste (ou devient) mauvais, on revient à l'original et on le signale
    still = {(p["k"], p["kind"]) for p in edge_problems(segs, wav)}
    if still:
        for k, kind in still:
            orig = segs_in[k]
            key = "end" if kind == "fin" else "start"
            if abs(float(segs[k][key]) - float(orig[key])) > 0.005:
                segs[k][key] = orig[key]
                segs[k]["duration"] = round(float(segs[k]["end"]) - float(segs[k]["start"]), 3)
                done = [m for m in done if not m.startswith(f"{kind} {float(orig[key]):.2f}")]
                left.append(f"{kind} à {float(orig[key]):.2f} : correction automatique refusée (le bord restait dans la voix)")
    return segs, done, left


# ----------------------------------------------------------------------------------------------- sous-titres

def caption_blocks(html: str) -> list[dict]:
    """Blocs de sous-titres d'une composition : [{id, start, end, words: [t…]}] (ce que HyperFrames affichera)."""
    out = []
    parts = re.split(r'(?=<div class="clip layer cap" id="cap-)', html)
    for p in parts[1:]:
        m = re.match(r'<div class="clip layer cap" id="cap-(\d+)" data-start="([\d.]+)" data-duration="([\d.]+)"', p)
        if not m:
            continue
        body = p[:p.find("</div>\n      </div>")] if "</div>\n      </div>" in p else p[:4000]
        s, d = float(m.group(2)), float(m.group(3))
        out.append({"id": int(m.group(1)), "start": s, "end": round(s + d, 3),
                    "words": [float(x) for x in re.findall(r'(?:class="cap-word[^"]*"[^>]*?|id="w-\d+-\d+" )data-t="([\d.]+)"', body)],
                    "lines": len(re.findall(r'class="cap-line[" ]', body))})
    return out


def caption_problems(html: str, max_lines: int = 3, max_words: int = 12) -> list[str]:
    """Deux blocs à l'écran en même temps (≥ 1 image à 30 i/s) ; mot qui apparaît hors de son bloc (jamais vu)."""
    bl = sorted(caption_blocks(html), key=lambda b: b["start"])
    out = []
    for a, b in zip(bl, bl[1:]):
        if b["start"] < a["end"] - 0.02:
            out.append(f"blocs {a['id']} et {b['id']} à l'écran ensemble {a['end'] - b['start']:.2f} s (à {b['start']:.2f} s)")
    for b in bl:
        if len(b["words"]) > max_words:
            out.append(f"bloc {b['id']} ({b['start']:.2f} s) : {len(b['words'])} mots (max {max_words}) : trop long pour être lu")
        if b.get("lines", 0) > max_lines:   # bloc trop long : ses dernières lignes sortent de l'écran (15/10/2026, short 1 E21)
            out.append(f"bloc {b['id']} ({b['start']:.2f} s) : {b['lines']} lignes (max {max_lines}) : la fin ne s'affiche pas")
        if b["end"] - b["start"] < 0.3 and b is not bl[-1]:
            out.append(f"bloc {b['id']} ({b['start']:.2f} s) affiché {b['end'] - b['start']:.2f} s seulement : illisible")
        lost = [t for t in b["words"] if t < b["start"] - 0.02 or t > b["end"] - 0.03]
        if lost:
            out.append(f"bloc {b['id']} ({b['start']:.2f}–{b['end']:.2f} s) : {len(lost)} mot(s) prévu(s) hors du bloc ({lost[0]:.2f} s)")
    return out


# ----------------------------------------------------------------------------------------------- film des moments à risque

def moments_reel(render: Path, junctions: list[float], d_speech: float, out: Path, font: Path | None = None,
                 around: float = 1.5) -> Path | None:
    """MP4 court qui enchaîne seulement les moments délicats du rendu : chaque raccord (± `around` s) et la fin de la
    parole (- 2,5 s / + 1 s), avec l'instant écrit en haut — pour qu'Arthur valide en ~20 s au lieu de tout revoir."""
    pts = [("raccord", j) for j in junctions] + [("fin", d_speech)]
    if not pts:
        return None
    win = []
    for name, t in pts:
        a, b = (t - 2.5, t + 1.0) if name == "fin" else (t - around, t + around)
        a = max(0.0, a)
        if win and a <= win[-1][1]:            # fenêtres qui se touchent : réunies
            win[-1] = (win[-1][0], b, win[-1][2] + [(name, t)])
        else:
            win.append((a, b, [(name, t)]))
    out.parent.mkdir(parents=True, exist_ok=True)
    vf, af = [], []
    for i, (a, b, items) in enumerate(win):
        label = " · ".join(f"{n} {t:.1f} s" for n, t in items).replace(":", "\\:")
        txt = (f",drawtext=fontfile='{font.name}':text='{label}':x=(w-tw)/2:y=60:fontsize=46:fontcolor=white:"
               f"box=1:boxcolor=black@0.6:boxborderw=14") if font else ""
        vf.append(f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS{txt}[v{i}];")
        af.append(f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS[a{i}];")
    graph = "".join(vf) + "".join(af) + "".join(f"[v{i}][a{i}]" for i in range(len(win))) + \
        f"concat=n={len(win)}:v=1:a=1[v][a]"
    cmd = [FFMPEG, "-y", "-v", "error", "-i", str(Path(render).resolve()), "-filter_complex", graph, "-map", "[v]",
           "-map", "[a]", "-c:v", "libx264", "-crf", "23", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac",
           "-b:a", "128k", "-movflags", "+faststart", str(Path(out).resolve())]
    # police lue depuis son dossier (chemin sans accent ni « : » dans le filtre)
    subprocess.run(cmd, check=True, cwd=str(font.parent) if font else None)
    return out


# ----------------------------------------------------------------------------------------------- synchro réelle du fichier

def _pcm(f: Path, ss: float | None = None, t: float | None = None) -> np.ndarray:
    cmd = [FFMPEG, "-v", "error"] + (["-ss", f"{ss:.4f}"] if ss is not None else []) + ["-i", str(f)] + \
        (["-t", f"{t:.4f}"] if t else []) + ["-ac", "1", "-ar", "16000", "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32)


def sync_problems(clip_media: Path, segs: list[dict], audio: Path, delay: float, fps: int, tol: float = 0.015) -> list[str]:
    """Le son DU FICHIER monté (assets/source.mp4) est-il exactement celui prévu, morceau par morceau ? Corrélation
    NORMALISÉE d'un extrait de 0,5 s au milieu de chaque morceau avec la source (12/10/2026 : on ne contrôlait que le plan,
    pas le fichier ; le son dérivait de ~25 ms par raccord sans qu'aucun contrôle le voie). Morceaux de moins de 0,8 s
    ignorés (extrait trop court pour une mesure sûre). Renvoie les morceaux décalés de plus de `tol`."""
    import math
    got = _pcm(clip_media)
    out, off = [], 0.0
    L, W = 0.5, 0.3
    for k, s in enumerate(segs):
        d = max(1, math.ceil((float(s["end"]) - float(s["start"])) * fps - 1e-3)) / fps
        if d >= 0.8:
            L_ = min(L, d - 0.1)
            mid_rel, mid_src = off + d / 2, float(s["start"]) + d / 2 - delay
            ref = _pcm(audio, mid_src - L_ / 2, L_).astype(np.float64)
            lo = max(0, int((mid_rel - L_ / 2 - W) * 16000))
            g = got[lo:int((mid_rel + L_ / 2 + W) * 16000)].astype(np.float64)
            n = len(ref)
            if n > 800 and len(g) > n and float((ref ** 2).sum()) > 1e-6:
                cc = np.correlate(g, ref, "valid")
                en = np.sqrt(np.convolve(g ** 2, np.ones(n), "valid") * (ref ** 2).sum()) + 1e-12
                ncc = cc / en
                i = int(np.argmax(ncc))
                lag = (lo + i) / 16000 - (mid_rel - L_ / 2)
                if ncc[i] > 0.5 and abs(lag) > tol:
                    out.append(f"morceau {k + 1} décalé de {lag * 1000:+.0f} ms")
                elif ncc[i] <= 0.5:
                    out.append(f"morceau {k + 1} : son différent de la source (ressemblance {ncc[i]:.2f})")
        off += d
    return out


# ----------------------------------------------------------------------------------------------- retraits de « euh » collés

def _spec(wav: Path, a: float, b: float, hop: float = 0.01) -> tuple[np.ndarray, np.ndarray]:
    """Spectre (trames de 25 ms tous les 10 ms) et énergie par trame entre a et b."""
    x = _pcm(wav, max(0.0, a), b - max(0.0, a)).astype(np.float64)
    n, h = 400, int(hop * 16000)
    if len(x) < n + h:
        return np.zeros((0, 201)), np.zeros(0)
    fr = np.stack([x[i:i + n] * np.hanning(n) for i in range(0, len(x) - n, h)])
    mag = np.abs(np.fft.rfft(fr, axis=1))
    return np.log1p(mag), np.sqrt((fr ** 2).mean(1))


def _steady_onset(wav: Path, t: float, ahead: float = 0.12) -> float | None:
    """Coupe tombée en pleine voix avant un « euh » collé : instant (≥ t, ≤ t + ahead) où commence la voyelle TENUE (flux
    spectral bas sur 3 trames) — avant lui : la fin du mot (détente, consonne), à garder. None si rien de stable."""
    S, e = _spec(wav, t - 0.02, t + ahead + 0.06)
    if len(S) < 6:
        return None
    flux = np.r_[0, np.sqrt(((S[1:] - S[:-1]) ** 2).mean(1))]
    lim = np.percentile(flux, 35)
    for i in range(2, len(flux) - 2):
        if (flux[i:i + 3] <= lim).all() and e[i] > 0:
            return round(t - 0.02 + i * 0.01, 3) if t - 0.02 + i * 0.01 > t + 0.005 else None
    return None


def _attack_start(wav: Path, t: float, back: float = 0.12) -> float | None:
    """Début de morceau en pleine voix juste après un « euh » collé : instant (≤ t, ≥ t - back) où finit la voyelle tenue,
    avant l'attaque du mot (flux qui remonte) — le mot qui suit garde son attaque."""
    S, e = _spec(wav, t - back - 0.04, t + 0.06)
    if len(S) < 6:
        return None
    flux = np.r_[0, np.sqrt(((S[1:] - S[:-1]) ** 2).mean(1))]
    lim = np.percentile(flux, 35)
    base = t - back - 0.04
    for i in range(len(flux) - 3, 1, -1):
        if (flux[i - 2:i + 1] <= lim).all():
            nt = base + (i + 1) * 0.01
            return round(nt, 3) if nt < t - 0.005 else None
    return None


def refine_joins(segs: list[dict], wav: Path, voiced: float = 0.25) -> tuple[list[dict], list[str]]:
    """Retraits de « euh » coupés EN PLEINE VOIX (voix > `voiced` du niveau juste avant la coupe : E22, 9 coupes sur 18 dans le
    short 1) : la fin du mot passait à la trappe (« job principal‖ », perçu comme « coupé trop tôt »). Fin recalée au début
    du « euh » tenu, début du morceau suivant juste avant l'attaque du mot. Un morceau ne déborde jamais sur le suivant."""
    segs = [dict(s) for s in segs]
    log = []
    ends, starts = passage_edges(segs)
    for k in range(len(segs) - 1):
        if k in ends:
            continue
        t = float(segs[k]["end"])
        if end_ratio(wav, t, 0.04) > voiced:
            nt = _steady_onset(wav, t)
            if nt and nt < float(segs[k + 1]["start"]) - 0.02:
                segs[k]["end"] = nt
                log.append(f"fin de morceau {t:.2f} -> {nt:.2f} (fin du mot gardée, « euh » tenu laissé de côté)")
    for k in range(1, len(segs)):
        if k in starts:
            continue
        t = float(segs[k]["start"])
        if start_ratio(wav, t, 0.04) > voiced:
            nt = _attack_start(wav, t)
            if nt and nt > float(segs[k - 1]["end"]) + 0.02:
                segs[k]["start"] = nt
                log.append(f"début de morceau {t:.2f} -> {nt:.2f} (attaque du mot gardée)")
    for s in segs:
        s["duration"] = round(float(s["end"]) - float(s["start"]), 3)
    return segs, log


# ----------------------------------------------------------------------------------------------- hésitations restantes (CTC)

def ctc_hesitations(segs: list[dict], words: list[dict], wav: Path, cfg=None, min_gap: float = 0.35, voiced: float = 0.15,
                    pad_end: float = 0.06, pad_start: float = 0.03, min_piece: float = 0.25) -> tuple[list[dict], list[str]]:
    """Retire les blocs de voix SANS MOT entre deux mots (« euh » collés que `fillers` n'a pas pu couper, « hmm »
    d'acquiescement de l'autre personne, Arthur 12/10/2026 : « on entend plusieurs fois Thomas acquiescer en faisant hmm,
    ça n'apporte rien, ça ne fait pas pro »). Les mots de la transcription normale (qui n'écrit jamais ces bruits) sont
    ALIGNÉS sur le son (CTC, `endpoint.align`) : leurs frontières sont exactes à ~20 ms près ; un trou ≥ `min_gap` entre
    deux mots alignés qui contient de la voix est coupé de la fin du mot (+ `pad_end`) au début du suivant (- `pad_start`)."""
    from .endpoint import align
    from .verify import FILLERS, _norm, verbatim
    out, log = [], []
    for s in segs:
        a, b = float(s["start"]), float(s["end"])
        # texte VERBATIM (hésitations comprises) : la transcription normale « nettoie » aussi de vrais mots (« en fait »,
        # « c'est ») qu'il ne faut pas couper ; seuls les fillers et la voix que personne n'a transcrite sont retirés
        vb = verbatim(wav, a, b, cfg) if cfg is not None else []
        toks = [w["w"] for w in vb] or [w["w"] for w in words if w["s"] >= a - 0.05 and w["e"] <= b + 0.05]
        merged: list[str] = []
        for tk in toks:                     # « qu » + « 'il » (Whisper) -> « qu'il » : jamais de coupe dans un mot élidé
            if merged and (tk.startswith("'") or tk.startswith("’") or merged[-1].endswith("'")):
                merged[-1] += tk
            else:
                merged.append(tk)
        toks = merged
        if len(toks) < 2 or b - a < 1.0:
            out.append(dict(s))
            continue
        al = [x for x in align(wav, a, b, " ".join(toks)) if _norm(x["w"]) not in FILLERS]
        cuts = []
        for x, y in zip(al, al[1:]):
            g0, g1 = x["e"] + pad_end, y["s"] - pad_start
            if g1 - g0 < min_gap:          # retrait réel ≥ min_gap (avant le 14/10 : 0,26 s acceptées, « tu ‖ donnes »)
                continue
            r = _rms(wav, g0, g1)
            lvl = _level(wav, (g0 + g1) / 2)
            if len(r) and lvl > 0 and float((r > voiced * lvl).mean()) > 0.3:   # de la voix, pas un silence
                cuts.append((round(g0, 3), round(g1, 3), x["w"], y["w"]))
        # répétitions (« qu'il faut avoir, qu'il faut avoir », « de mes… de d'un ») : groupe de 1 à 4 mots dit deux fois de
        # suite -> la 1re occurrence est retirée (12/10/2026, shorts 4 et 5 E22 ; un monteur les coupe toujours)
        norm = [_norm(x["w"]) for x in al]
        i = 0
        while i < len(al) - 1:
            hit = 0
            for n_ in (4, 3, 2, 1):
                if i + 2 * n_ <= len(al) and norm[i:i + n_] == norm[i + n_:i + 2 * n_] and any(len(t) > 2 for t in norm[i:i + n_]):
                    hit = n_
                    break
            if hit:
                g0 = max(a, al[i]["s"] - pad_start)
                g1 = al[i + hit]["s"] - pad_start
                if g1 - g0 > 0.1:
                    cuts.append((round(g0, 3), round(g1, 3), "", " ".join(x["w"] for x in al[i:i + hit]) + " (répété)"))
                i += hit
            else:
                i += 1
        cuts.sort()
        pieces, cur = [], a
        for g0, g1, w0, w1 in cuts:
            if g0 < cur:      # recouvrements entre retraits : ignorés
                continue
            if g0 - cur >= min_piece and b - g1 >= min_piece:
                pieces.append((cur, g0))
                cur = g1
                log.append(f"répétition « {w1.replace(' (répété)', '')} » retirée ({g0:.2f}–{g1:.2f})" if not w0 else
                           f"« {w0} ‖ {w1} » : {g1 - g0:.2f} s de voix sans mot retirées ({g0:.2f}–{g1:.2f})")
        pieces.append((cur, b))
        for k, (p0, p1) in enumerate(pieces):
            n = dict(s)
            n["start"], n["end"], n["duration"] = round(p0, 3), round(p1, 3), round(p1 - p0, 3)
            if k < len(pieces) - 1:          # seul le dernier morceau garde la citation de fin
                n.pop("end_text", None)
            if k > 0:
                n.pop("start_text", None)
            out.append(n)
    return out, log


# ----------------------------------------------------------------------------------------------- fluidité des raccords internes
# Arthur, 14/10/2026 (short 2 E21) : « les phrases ont tendance à être coupées trop tôt ». Mesure : 5 raccords sur 10 tombaient
# en PLEINE VOIX (« il y ‖ a », retrait de 0,14 s ; « aborder ‖ assez », la voix continuait 0,3 s après la coupe) : `fillers`
# prenait l'allongement naturel d'une voyelle pour un « euh », et l'étape `ctc` acceptait des retraits de 0,26 s. Bon sens de
# monteur : on ne coupe au milieu d'une phrase que pour retirer une VRAIE hésitation, et jamais en tranchant la fin d'un mot.

MIN_CUT = 0.35        # retrait plus court : aucun gain de rythme, seulement le risque d'une coupe audible -> recollé
VOICE_CUT = 0.30      # voix au point de coupe (fraction du niveau de parole) au-delà de laquelle le mot est encore en cours


def _flux(wav: Path, a: float, b: float) -> np.ndarray:
    S, _e = _spec(wav, a, b)
    return np.r_[0, np.sqrt(((S[1:] - S[:-1]) ** 2).mean(1))] if len(S) > 1 else np.zeros(0)


def _steady_after(wav: Path, t: float, span: float = 0.10) -> bool:
    """Juste après t, un son TENU (spectre stable : « euh » / « hmm ») plutôt qu'une fin de mot (détente, consonne) ?"""
    f = _flux(wav, t - 0.25, t + span + 0.03)
    if len(f) < 12:
        return False
    after = f[-int(span / 0.01):]
    return float(np.median(after)) <= float(np.percentile(f, 40))


def join_flow_problems(segs: list[dict], wav: Path) -> list[dict]:
    """Raccords internes (deux morceaux d'un même passage, ≤ 3 s d'écart dans la source) qui cassent le rythme :
    [{k, why, t}] (k = morceau AVANT le raccord). Raisons : retrait < MIN_CUT ; fin du morceau en pleine voix sans « euh »
    tenu derrière (fin de mot tranchée) ; fin ET début en pleine voix sur un retrait court (coupe dans une voix continue)."""
    out = []
    for k in range(len(segs) - 1):
        a, b = segs[k], segs[k + 1]
        e, s = float(a["end"]), float(b["start"])
        gap = s - e
        er, sr = end_ratio(wav, e, 0.04), start_ratio(wav, s, 0.04)
        if gap > 3.0:
            # passage suivant pris ailleurs : la fin du morceau doit être une fin de MOT (Thomas, 15/10/2026, short 1 E21 :
            # « à 0:07 le mot "métiers" est complètement croppé » — coupe posée sur un changement de plan, pas sur la voix)
            after = start_ratio(wav, e, 0.06)   # la coupe peut tomber dans un micro-creux DU mot (« métier‖s », 1201,62)
            if er > VOICE_CUT or after > 0.5:
                er = max(er, after)
                out.append({"k": k, "t": e, "extend": True, "hard": True,
                            "why": f"mot coupé à {e:.2f} avant un saut de passage (voix à {int(er * 100)} %)"})
            continue
        if gap < -0.01:
            continue
        if gap < MIN_CUT and (er > VOICE_CUT or sr > VOICE_CUT):   # court ET dans la voix (un « euh » court coupé
            # proprement dans des silences reste : 1224,19–1224,52 short 1 E21)
            out.append({"k": k, "t": e, "why": f"retrait de {gap:.2f} s seulement (< {MIN_CUT} s) en pleine voix à {e:.2f} : coupe inutile"})
            continue
        if er > VOICE_CUT and not _steady_after(wav, e):
            # long retrait (vraie hésitation : « ok ‖ bah… si », 1,47 s) : on PROLONGE la fin jusqu'au creux qui finit le mot
            # plutôt que de remettre l'hésitation ; retrait court : recollé
            out.append({"k": k, "t": e, "extend": gap >= 0.5,
                        "why": f"fin de mot tranchée à {e:.2f} (voix à {int(er * 100)} %, pas de « euh » derrière)"})
        elif er > VOICE_CUT and sr > VOICE_CUT and gap < 0.5:
            out.append({"k": k, "t": e, "why": f"coupe dans une voix continue à {e:.2f}–{s:.2f} ({gap:.2f} s retirées)"})
    return out


def _word_end_after(wav: Path, t: float, limit: float) -> float | None:
    """Fin réelle du mot tranché : première trame après t (avant `limit`) où la voix passe sous VOICE_CUT et y reste 2 trames,
    + 0,04 s de détente."""
    lvl = _level(wav, t)
    r = _rms(wav, t, limit)
    if lvl <= 0 or len(r) < 3:
        return None
    for i in range(1, len(r) - 1):
        if (r[i:i + 2] < VOICE_CUT * lvl).all():
            return round(min(limit, t + i * FRAME + 0.04), 3)
    return None


def fix_join_flow(segs: list[dict], wav: Path) -> tuple[list[dict], list[str]]:
    """Recolle les morceaux des raccords signalés par `join_flow_problems` : le retrait est annulé, la phrase redevient entière
    (toujours possible, toujours sûr : c'est le son d'origine)."""
    segs = [dict(s) for s in segs]
    log = []
    for p in sorted(join_flow_problems(segs, wav), key=lambda p: -p["k"]):
        k = p["k"]
        a, b = segs[k], segs[k + 1]
        if p.get("extend"):
            # retrait long = une vraie hésitation retirée par `fillers` / `ctc` (aucun mot perdu, déjà vérifié) : on ne la
            # remet JAMAIS ; on prolonge la fin jusqu'au creux qui finit le mot, sinon on laisse la coupe (écoute de `qa`)
            lim = float(a["end"]) + 0.45 if p.get("hard") else min(float(a["end"]) + 0.45, float(b["start"]) - 0.1)
            nt = _word_end_after(wav, float(a["end"]), lim)
            if nt and nt > float(a["end"]) + 0.01:
                segs[k] = dict(a, end=nt, duration=round(nt - float(a["start"]), 3))
                log.append(f"fin du mot gardée : {float(a['end']):.2f} -> {nt:.2f} ({p['why']})")
            continue
        segs[k] = dict(a, end=b["end"], duration=round(float(b["end"]) - float(a["start"]), 3),
                       **({"end_text": b["end_text"]} if b.get("end_text") else {}))
        del segs[k + 1]
        log.append(f"raccord recollé ({p['why']})")
    return segs, log


# ----------------------------------------------------------------------------------------------- bruit de bouche en fin de short
# Arthur, 14/10/2026 (short 2 E21) : « il y a un bruit de bouche à la fin ». La respiration gardée après le dernier mot
# (`pad_end`, jusqu'à 0,35 s) contenait un claquement de lèvres (1503,59 : 30 ms isolées dans le silence).

def tail_noise(wav: Path, t: float, look: float = 1.0) -> dict | None:
    """Dans la traîne finale (entre la fin de la voix et la coupe t) : un son bref et isolé (≤ 0,08 s, séparé de la voix par
    ≥ 0,06 s de silence) = bruit de bouche. Renvoie {voice_end, noise, end} (end = coupe conseillée) ou None."""
    lvl = _level(wav, t - 1.0)
    r = _rms(wav, t - look, t)
    if lvl <= 0 or len(r) < 10:
        return None
    on = r > END_THR * lvl
    ve, run = None, 0
    for i, v in enumerate(on):   # fin de la voix = dernière trame d'une suite d'au moins 5 trames (0,1 s) de son
        run = run + 1 if v else 0
        if run >= 5:
            ve = i
    if ve is None:
        return None
    for i in range(ve + 2, len(on)):
        if on[i]:
            j = i
            while j < len(on) and on[j]:
                j += 1
            if j - i <= 4 and i - ve >= 3:
                v_end = t - look + (ve + 1) * FRAME
                n_t = t - look + i * FRAME
                return {"voice_end": round(v_end, 3), "noise": round(n_t, 3),
                        "end": round(max(v_end + 0.06, min(v_end + 0.15, n_t - 0.02)), 3)}
            break
    return None


def fix_tail_noise(segs: list[dict], wav: Path) -> tuple[list[dict], list[str]]:
    segs = [dict(s) for s in segs]
    p = tail_noise(wav, float(segs[-1]["end"]))
    if not p:
        return segs, []
    segs[-1]["end"] = p["end"]
    segs[-1]["duration"] = round(p["end"] - float(segs[-1]["start"]), 3)
    return segs, [f"bruit de bouche à {p['noise']:.2f} après la dernière voix -> fin du short à {p['end']:.2f}"]


# ----------------------------------------------------------------------------------------------- qui est à l'image (épisode déjà monté)
# Arthur, 14/10/2026 (short 1 E21) : « vers le début, Thomas coupe la parole à l'invité, il faut pas ; et ça sert à rien de
# mettre l'image et le son de Thomas qui acquiesce ». Dans un épisode DÉJÀ MONTÉ, l'image vient du montage du monteur : quand
# Thomas réagit, le plan passe sur lui (short 1 : 6,9–7,8 s, l'invité parle encore). Le son « hmm » est retiré par `ctc` ;
# l'IMAGE de celui qui écoute, rien ne la voyait. On reconnaît le visage à l'image (SFace, comme `rushes`).

def listener_shown(clip_media: Path, segs: list[dict], words: list[dict], host_ref, step: float = 0.25,
                   min_run: float = 0.3, fps: int = 30) -> list[dict]:
    """Moments où le visage SEUL à l'image est celui de la personne qui ÉCOUTE (ou qui coupe la parole par-dessus l'autre).
    `clip_media` = vidéo du montage (assets/source.mp4, temps du clip) ; `words` avec `spk` (diarized_words.json).
    Renvoie [{t0, t1, abs0, abs1, k, shown, speaking}] (temps du clip, temps source, morceau)."""
    from .ingest import _faces, _frame, embedding
    if host_ref is None or not words or not any("spk" in w for w in words):
        return []
    spans, acc = [], 0.0
    import math
    for k, s in enumerate(segs):   # durées arrondies à l'image supérieure, EXACTEMENT comme `compose` (sinon dérive ~0,2 s)
        d = math.ceil((float(s["end"]) - float(s["start"])) * fps - 1e-3) / fps
        spans.append((acc, acc + d, k, float(s["start"])))
        acc += d
    ws = sorted((w for w in words if "spk" in w), key=lambda w: w["s"])
    starts = np.array([w["s"] for w in ws])

    def speaker(ts: float) -> str | None:
        i = int(np.searchsorted(starts, ts))
        for j in (i - 1, i):
            if 0 <= j < len(ws) and ws[j]["s"] - 0.15 <= ts <= ws[j]["e"] + 0.15:
                return ws[j]["spk"]
        return None

    marks = []
    t = step / 2
    while t < acc:
        sp = next((x for x in spans if x[0] <= t < x[1]), None)
        if sp is None:
            break
        ts = sp[3] + (t - sp[0])
        talk = speaker(ts)
        bad = None
        if talk:
            img = _frame(clip_media, t, 960)
            fs = _faces(img) if img is not None else []
            if len(fs) == 1:          # gros plan : une seule personne (le plan large montre les deux : rien à dire)
                sim = float(embedding(img, fs[0]) @ host_ref)
                shown = "host" if sim > 0.45 else ("guest" if sim < 0.3 else None)
                bad = shown if shown and shown != talk else None
        marks.append((t, ts, sp[2], bad, talk))
        t += step
    # DERNIÈRE IMAGE (15/10/2026, short 1 E21 : « enlève le plan avec Thomas à la fin, ça n'apporte rien ») : elle reste figée
    # ~0,4 s pendant le fondu vers l'outro. Le montage passait sur Thomas à 1243,125, 0,02 s avant la fin du short ; Thomas
    # allait dire « Et », donc « il parlait » et rien n'était signalé. À la fin, la personne à l'image doit être celle qui a dit
    # la DERNIÈRE PHRASE du short (son dernier mot entier), pas celle qui va parler juste après.
    end_run = None
    end_abs = float(segs[-1]["end"])
    last_words = [w for w in ws if w["e"] <= end_abs + 0.05 and w["s"] >= float(segs[-1]["start"])]
    closer = last_words[-1]["spk"] if last_words else None
    tail = acc - 0.03
    img = _frame(clip_media, tail, 960)
    fs = _faces(img) if img is not None else []
    if closer and len(fs) == 1:
        sim = float(embedding(img, fs[0]) @ host_ref)
        shown = "host" if sim > 0.45 else ("guest" if sim < 0.3 else None)
        if shown and shown != closer:
            t0 = tail
            while t0 - 0.04 > max(0.0, acc - 2.0):   # en reculant : début du plan de l'autre
                im2 = _frame(clip_media, t0 - 0.04, 960)
                f2 = _faces(im2) if im2 is not None else []
                if len(f2) != 1 or (float(embedding(im2, f2[0]) @ host_ref) > 0.45) != (shown == "host"):
                    break
                t0 -= 0.04
            marks = [m for m in marks if m[0] < t0 - step]
            end_run = {"t0": round(t0, 3), "t1": round(acc, 3), "abs0": round(end_abs - (acc - t0), 3), "abs1": end_abs,
                       "k": len(segs) - 1, "shown": shown, "speaking": closer, "end": True}
    out, cur = [], None
    for t, ts, k, bad, talk in marks + [(acc, 0.0, -1, None, None)]:
        if bad and cur and cur["k"] == k and cur["shown"] == bad:
            cur["t1"], cur["abs1"] = t + step / 2, ts + step / 2
            continue
        if cur and cur["t1"] - cur["t0"] >= min_run:
            out.append(cur)
        cur = {"t0": t - step / 2, "t1": t + step / 2, "abs0": ts - step / 2, "abs1": ts + step / 2, "k": k,
               "shown": bad, "speaking": talk} if bad else None
    if end_run:
        out.append(end_run)
    return out


def fix_listener_shown(segs: list[dict], runs: list[dict], min_piece: float = 0.4) -> tuple[list[dict], list[str], list[str]]:
    """Retire du montage le moment où l'on voit celui qui écoute : au bord d'un morceau, le morceau est raccourci (la
    correction des bords de phrase recale ensuite la coupe dans un silence) ; au milieu, il est coupé en deux autour."""
    segs = [dict(s) for s in segs]
    done, left = [], []
    for r in sorted(runs, key=lambda r: -r["abs0"]):
        # morceau retrouvé par le temps SOURCE (les indices changent quand d'autres corrections recollent des morceaux)
        k = next((i for i, x in enumerate(segs) if float(x["start"]) - 0.05 <= (r["abs0"] + r["abs1"]) / 2 <= float(x["end"]) + 0.05), None)
        if k is None:
            continue
        s = segs[k]
        a, b = float(s["start"]), float(s["end"])
        x0, x1 = max(a, r["abs0"] - (0.02 if r.get("end") else 0.05)), min(b, r["abs1"] + 0.05)
        who = "Thomas" if r["shown"] == "host" else "l'invité"
        # bon sens (14/10/2026) : couper au MILIEU d'un morceau trancherait une phrase de l'invité -> jamais automatique ; Claude
        # choisit à la main les coupes sur des silences voisins (quitte à retirer la phrase entière), d'après les mots alignés
        if x0 - a >= min_piece and b - x1 >= min_piece or x0 - a < min_piece and b - x1 < min_piece:
            left.append(f"{r['t0']:.1f}–{r['t1']:.1f} s : on voit {who} pendant que l'autre parle ({r['abs0']:.2f}–{r['abs1']:.2f}, "
                        f"morceau {k + 1}) -> recouper à la main sur des silences voisins")
            continue
        if x0 - a < min_piece:
            segs[k] = dict(s, start=round(x1, 3))
            segs[k].pop("start_text", None)
        else:
            segs[k] = dict(s, end=round(x0, 3))
            segs[k].pop("end_text", None)
        done.append(f"{r['t0']:.1f}–{r['t1']:.1f} s : on voyait {who} pendant que l'autre parle ({r['abs0']:.2f}–{r['abs1']:.2f}) -> retiré")
    for s in segs:
        s["duration"] = round(float(s["end"]) - float(s["start"]), 3)
    return segs, done, left
