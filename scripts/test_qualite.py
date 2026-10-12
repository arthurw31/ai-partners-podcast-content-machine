"""Tests anti-régression de la qualité (Arthur, 12/10/2026 : « une boucle de vérification intransigeante »).

Chaque défaut trouvé par Arthur ou par la QA devient un cas ici : une correction future ne peut plus le faire revenir sans
que ce script échoue. Lancer : `python scripts/test_qualite.py` (≈ 1 min ; les cas E22 sont sautés si l'audio n'est pas là).
Ajouter un cas = une fonction `test_…` (assert) + la date et la phrase d'Arthur en commentaire.
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from clipper.captions import group_words  # noqa: E402
from clipper.compose import cfg_for_format  # noqa: E402
from clipper.config import Brand  # noqa: E402
from clipper.strict import caption_problems, edge_problems, fix_edges  # noqa: E402

E22_WAV = ROOT / "brands" / "ai-corner" / "episodes" / "E22_nicolas-comestaz_coty.wav"


def _words(spec: list[tuple[str, float, float]]) -> list[dict]:
    return [{"w": w, "s": s, "e": e, "spk": "guest"} for w, s, e in spec]


def test_sous_titres_jamais_superposes():
    """12/10/2026 « des sous-titres qui se chevauchent » : un bloc court prolongé à sa durée minimale débordait sur le
    suivant (0,1–0,3 s de deux blocs à l'écran, shorts 1 et 2 E22)."""
    cfg = cfg_for_format(Brand("ai-corner").cfg, "9x16")
    # débit rapide + une pause courte : des groupes de < 0,5 s
    ws = _words([("Je", 0.0, 0.1), ("crois", 0.1, 0.3), ("qu'on", 0.32, 0.4), ("a", 0.75, 0.8), ("plus", 0.8, 0.95),
                 ("de", 0.95, 1.0), ("3000", 1.0, 1.4), ("agents", 1.4, 1.8), ("aujourd'hui.", 1.8, 2.3),
                 ("Et", 2.6, 2.7), ("si", 2.7, 2.8), ("on", 2.8, 2.9), ("regarde,", 2.9, 3.3), ("Oui.", 3.5, 3.6),
                 ("On", 3.75, 3.8), ("voit", 3.8, 4.0), ("dix", 4.0, 4.2), ("agents.", 4.2, 4.6)])
    caps = group_words(ws, 0.0, 5.0, cfg, ["3000 agents"], breaks=[0.7, 3.7])
    for a, b in zip(caps, caps[1:]):
        assert b["start"] >= a["end"] - 1e-6, f"blocs {a['id']} ({a['start']}–{a['end']}) et {b['id']} ({b['start']}) superposés"


def test_controle_composition_sous_titres():
    """Le contrôle lit la composition rendue : deux blocs ensemble = défaut ; un mot hors de son bloc = défaut."""
    html = ('<div class="clip layer cap" id="cap-1" data-start="0.0" data-duration="1.2" data-track-index="3">'
            '<span class="cap-word" id="w-1-1" data-t="0.1"></span></div>\n      </div>'
            '<div class="clip layer cap" id="cap-2" data-start="1.0" data-duration="1.0" data-track-index="3">'
            '<span class="cap-word" id="w-2-1" data-t="1.05"></span><span class="cap-word" id="w-2-2" data-t="2.4"></span>'
            '</div>\n      </div>')
    pb = caption_problems(html)
    assert any("ensemble" in p for p in pb), pb
    assert any("hors du bloc" in p for p in pb), pb
    ok = html.replace('data-start="1.0" data-duration="1.0"', 'data-start="1.2" data-duration="1.5"')
    assert not [p for p in caption_problems(ok) if "ensemble" in p]


def _e22():
    if not E22_WAV.exists():
        raise _Skip("audio E22 absent")
    return E22_WAV


def test_fin_coupee_trop_tot_detectee_et_corrigee():
    """07–08/10/2026 teaser E22 « …en productivité » coupé sur la dernière syllabe (« -té » jusqu'à 1294,94, coupe à
    1294,85) : le contrôle strict doit le voir, la correction doit finir dans le silence."""
    wav = _e22()
    segs = [{"start": 1290.0, "end": 1294.85, "end_text": "en productivité."}]
    fins = lambda ss: [p for p in edge_problems(ss, wav) if p["kind"] == "fin"]   # noqa: E731
    assert fins(segs), "fin dans la syllabe non détectée"
    fixed, done, left = fix_edges(segs, wav)
    assert any(m.startswith("fin") for m in done) and not [m for m in left if m.startswith("fin")], (done, left)
    assert fixed[0]["end"] > 1294.94, fixed[0]["end"]
    assert not fins(fixed), fins(fixed)


def test_fin_validee_acceptee():
    """Fins validées par Arthur (shorts 1 et 2 E22, 11/10/2026) : jamais signalées (pas de fausse alerte)."""
    wav = _e22()
    for end in (2372.76, 2089.31):
        segs = [{"start": end - 5, "end": end, "end_text": "x"}]
        assert not [p for p in edge_problems(segs, wav) if p["kind"] == "fin"], end


def test_raccord_interne_serre_accepte():
    """Raccord entre deux phrases avec 0,08 s de silence dans la source (short 1 E22 « …à venir. ‖ et je pense », « et » à
    2339,72) : accepté ou recalé DANS le creux, jamais dans le « et » qui suit."""
    wav = _e22()
    segs = [{"start": 2334.68, "end": 2339.68, "end_text": "dans les années à venir."},
            {"start": 2345.08, "end": 2350.0, "end_text": "x"}]
    fixed, _done, _left = fix_edges(segs, wav)
    assert 2339.6 <= fixed[0]["end"] <= 2339.71, fixed[0]["end"]
    assert not [p for p in edge_problems(fixed, wav) if p["kind"] == "fin" and p["k"] == 0]


def test_depart_sur_une_traine_corrige_en_avant():
    """Short 1 E22 démarrait à 2228,67 sur la traîne d'une hésitation (« Et donc » à 2228,82) : départ avancé dans le
    silence, jamais reculé dans l'hésitation."""
    wav = _e22()
    segs = [{"start": 2228.67, "end": 2230.0, "start_text": "Et donc"}]
    fixed, done, _left = fix_edges(segs, wav)
    assert done and 2228.68 <= fixed[0]["start"] <= 2228.82, fixed[0]["start"]


def test_durees_a_l_image_sans_double_arrondi():
    """12/10/2026 : une durée déjà arrondie à l'image (6,266667 s) repassait à 189 images au lieu de 188 (erreur de
    virgule flottante) -> une image de trop par morceau, son et image décalés de 33 ms par raccord."""
    import math
    for d in (6.25, 4.16, 6.85, 5.85, 7.45, 0.51, 3.08):
        n1 = max(1, math.ceil(d * 30 - 1e-3))
        q = round(n1 / 30, 6)
        assert max(1, math.ceil(q * 30 - 1e-3)) == n1, (d, q)


def test_son_reconstruit_a_la_bonne_duree():
    """12/10/2026 « phrases coupées trop tôt » : le son des morceaux recollés sans réencodage prenait ~25 ms de retard par
    raccord (préchauffage AAC) ; reconstruit en un passage, il doit durer exactement la somme des morceaux."""
    wav = _e22()
    import shutil, subprocess, tempfile
    from clipper.media import FFMPEG, rebuild_audio
    with tempfile.TemporaryDirectory() as d:
        v = Path(d) / "v.mp4"
        subprocess.run([FFMPEG, "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=64x64:r=30:d=3.0",
                        "-c:v", "libx264", str(v)], check=True)
        pieces = [(2045.093, 0.5333333), (2046.023, 1.1), (2049.903, 1.3666667)]
        rebuild_audio(v, wav, pieces, normalize=False)
        out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=duration",
                              "-of", "csv=p=0", str(v)], capture_output=True, text=True).stdout.strip()
        assert abs(float(out) - sum(x for _, x in pieces)) < 0.03, out


def test_retrait_euh_colle_garde_la_fin_du_mot():
    """12/10/2026 : « …leur job principal‖euh » (short 2 E22, coupe à 2076,47 en pleine voix, 81 %) : la coupe est recalée
    au début du « euh » tenu, la fin de « principal » est gardée."""
    wav = _e22()
    from clipper.strict import refine_joins
    segs = [{"start": 2070.6, "end": 2076.47}, {"start": 2077.0, "end": 2077.77}, {"start": 2078.42, "end": 2080.0,
                                                                                 "end_text": "x"}]
    fixed, log = refine_joins(segs, wav)
    assert fixed[0]["end"] > 2076.47 and fixed[0]["end"] < 2076.6, (fixed[0]["end"], log)


def test_pensee_pas_finie_detectee():
    """11/10/2026 « le mec était en train de parler » : short 1 coupé après « …de l'entreprise. » alors que l'invité
    enchaînait « Et puis… » : Smart Turn doit dire « pas fini » (< 0,5) ; les fins validées, « fini » (> 0,9)."""
    wav = _e22()
    from clipper.endpoint import turn_complete
    assert turn_complete(wav, 2345.08) < 0.5
    assert turn_complete(wav, 2372.76) > 0.9 and turn_complete(wav, 2089.31) > 0.9


def test_hesitation_collee_retiree_par_alignement():
    """12/10/2026 : « produits de beauté, euh, à nos consommateurs » (short 2 E22, « euh » collé, retrait annulé par
    fillers) : retiré grâce à l'alignement CTC, sans perdre « beauté » ni « à »."""
    wav = _e22()
    from clipper.config import Brand
    from clipper.strict import ctc_hesitations
    segs = [{"start": 2085.0, "end": 2089.31, "end_text": "à nos consommateurs."}]
    out, log = ctc_hesitations(segs, [], wav, Brand("ai-corner").cfg)
    assert any("beauté" in m for m in log), log
    assert out[-1].get("end_text") and len(out) >= 2


class _Skip(Exception):
    pass


def main() -> int:
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    bad = 0
    for name, fn in tests:
        try:
            fn()
            print(f"OK     {name}")
        except _Skip as e:
            print(f"SAUTÉ  {name} ({e})")
        except Exception:  # noqa: BLE001
            bad += 1
            print(f"ÉCHEC  {name}\n{traceback.format_exc()}")
    print(f"\n{len(tests) - bad}/{len(tests)} tests OK")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
