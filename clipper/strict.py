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
            if lvl > 0 and len(nxt) and float(nxt.max()) > END_THR * lvl:
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
    if (r < START_THR * lvl).sum() >= 3:      # un vrai silence existe à côté : la correction doit aller le chercher
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
                    "words": [float(x) for x in re.findall(r'id="w-\d+-\d+" data-t="([\d.]+)"', body)]})
    return out


def caption_problems(html: str) -> list[str]:
    """Deux blocs à l'écran en même temps (≥ 1 image à 30 i/s) ; mot qui apparaît hors de son bloc (jamais vu)."""
    bl = sorted(caption_blocks(html), key=lambda b: b["start"])
    out = []
    for a, b in zip(bl, bl[1:]):
        if b["start"] < a["end"] - 0.02:
            out.append(f"blocs {a['id']} et {b['id']} à l'écran ensemble {a['end'] - b['start']:.2f} s (à {b['start']:.2f} s)")
    for b in bl:
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
            if g1 - g0 < min_gap - pad_end - pad_start:
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
