"""Tests anti-régression de la qualité (Arthur, 12/10/2026 : « une boucle de vérification intransigeante »).

Chaque défaut trouvé par Arthur ou par la QA devient un cas ici : une correction future ne peut plus le faire revenir sans
que ce script échoue. Lancer : `python scripts/test_qualite.py` (≈ 1 min ; les cas E23 sont sautés si l'audio n'est pas là).
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

E23_WAV = ROOT / "EPISODES" / "ai-corner" / "E23_nicolas-comestaz_coty" / "rushs" / "E23_nicolas-comestaz_coty.wav"


def _words(spec: list[tuple[str, float, float]]) -> list[dict]:
    return [{"w": w, "s": s, "e": e, "spk": "guest"} for w, s, e in spec]


def test_sous_titres_jamais_superposes():
    """12/10/2026 « des sous-titres qui se chevauchent » : un bloc court prolongé à sa durée minimale débordait sur le
    suivant (0,1–0,3 s de deux blocs à l'écran, shorts 1 et 2 E23)."""
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


def _e23():
    if not E23_WAV.exists():
        raise _Skip("audio E23 absent")
    return E23_WAV


def test_fin_coupee_trop_tot_detectee_et_corrigee():
    """07–08/10/2026 teaser E23 « …en productivité » coupé sur la dernière syllabe (« -té » jusqu'à 1294,94, coupe à
    1294,85) : le contrôle strict doit le voir, la correction doit finir dans le silence."""
    wav = _e23()
    segs = [{"start": 1290.0, "end": 1294.85, "end_text": "en productivité."}]
    fins = lambda ss: [p for p in edge_problems(ss, wav) if p["kind"] == "fin"]   # noqa: E731
    assert fins(segs), "fin dans la syllabe non détectée"
    fixed, done, left = fix_edges(segs, wav)
    assert any(m.startswith("fin") for m in done) and not [m for m in left if m.startswith("fin")], (done, left)
    assert fixed[0]["end"] > 1294.94, fixed[0]["end"]
    assert not fins(fixed), fins(fixed)


def test_fin_validee_acceptee():
    """Fins validées par Arthur (shorts 1 et 2 E23, 11/10/2026) : jamais signalées (pas de fausse alerte)."""
    wav = _e23()
    for end in (2372.76, 2089.31):
        segs = [{"start": end - 5, "end": end, "end_text": "x"}]
        assert not [p for p in edge_problems(segs, wav) if p["kind"] == "fin"], end


def test_raccord_interne_serre_accepte():
    """Raccord entre deux phrases avec 0,08 s de silence dans la source (short 1 E23 « …à venir. ‖ et je pense », « et » à
    2339,72) : accepté ou recalé DANS le creux, jamais dans le « et » qui suit."""
    wav = _e23()
    segs = [{"start": 2334.68, "end": 2339.68, "end_text": "dans les années à venir."},
            {"start": 2345.08, "end": 2350.0, "end_text": "x"}]
    fixed, _done, _left = fix_edges(segs, wav)
    assert 2339.6 <= fixed[0]["end"] <= 2339.71, fixed[0]["end"]
    assert not [p for p in edge_problems(fixed, wav) if p["kind"] == "fin" and p["k"] == 0]


def test_depart_sur_une_traine_corrige_en_avant():
    """Short 1 E23 démarrait à 2228,67 sur la traîne d'une hésitation (« Et donc » à 2228,82) : départ avancé dans le
    silence, jamais reculé dans l'hésitation."""
    wav = _e23()
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
    wav = _e23()
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
    """12/10/2026 : « …leur job principal‖euh » (short 2 E23, coupe à 2076,47 en pleine voix, 81 %) : la coupe est recalée
    au début du « euh » tenu, la fin de « principal » est gardée."""
    wav = _e23()
    from clipper.strict import refine_joins
    segs = [{"start": 2070.6, "end": 2076.47}, {"start": 2077.0, "end": 2077.77}, {"start": 2078.42, "end": 2080.0,
                                                                                 "end_text": "x"}]
    fixed, log = refine_joins(segs, wav)
    assert fixed[0]["end"] > 2076.47 and fixed[0]["end"] < 2076.6, (fixed[0]["end"], log)


def test_pensee_pas_finie_detectee():
    """11/10/2026 « le mec était en train de parler » : short 1 coupé après « …de l'entreprise. » alors que l'invité
    enchaînait « Et puis… » : Smart Turn doit dire « pas fini » (< 0,5) ; les fins validées, « fini » (> 0,9)."""
    wav = _e23()
    from clipper.endpoint import turn_complete
    assert turn_complete(wav, 2345.08) < 0.5
    assert turn_complete(wav, 2372.76) > 0.9 and turn_complete(wav, 2089.31) > 0.9


def test_hesitation_collee_retiree_par_alignement():
    """12/10/2026 : « produits de beauté, euh, à nos consommateurs » (short 2 E23, « euh » collé, retrait annulé par
    fillers) : retiré grâce à l'alignement CTC, sans perdre « beauté » ni « à »."""
    wav = _e23()
    from clipper.config import Brand
    from clipper.strict import ctc_hesitations
    segs = [{"start": 2085.0, "end": 2089.31, "end_text": "à nos consommateurs."}]
    out, log = ctc_hesitations(segs, [], wav, Brand("ai-corner").cfg)
    assert any("beauté" in m for m in log), log
    assert out[-1].get("end_text") and len(out) >= 2


def test_fin_suivie_de_pres_par_un_autre_son():
    """12/10/2026, short 5 E23 : « …en bon escient. » puis souffle et « Ouais » de Thomas 0,08 s après : couper dans ce
    petit silence (1408,70) doit être accepté ; couper sur le souffle / le « Ouais » (1409,12) jamais."""
    wav = _e23()
    fins = lambda t: [p for p in edge_problems([{"start": 1405.0, "end": t, "end_text": "x"}], wav) if p["kind"] == "fin"]  # noqa: E731
    assert not fins(1408.70), fins(1408.70)
    assert fins(1409.14)


def test_fin_dans_une_phrase_enchainee_refusee():
    """12/10/2026, short 4 E23 : « …ces réunions. » enchaîné sans pause par « Donc j'ai toujours considéré… » : une coupe
    à 596,42 est dans la voix (refusée) ; la fin prolongée après « …une forme de pouvoir, je dirais. » (602,25) est propre."""
    wav = _e23()
    fins = lambda t: [p for p in edge_problems([{"start": 590.0, "end": t, "end_text": "x"}], wav) if p["kind"] == "fin"]  # noqa: E731
    assert fins(596.42)
    assert not fins(602.253), fins(602.253)


def test_repetition_retiree():
    """12/10/2026, short 5 E23 : « …en fait, qu'il faut avoir, qu'il faut avoir lorsque… » : la 1re occurrence est retirée."""
    wav = _e23()
    from clipper.config import Brand
    from clipper.strict import ctc_hesitations
    out, log = ctc_hesitations([{"start": 1395.15, "end": 1398.65, "end_text": "x"}], [], wav, Brand("ai-corner").cfg)
    assert any("répétition" in m for m in log), log
    assert len(out) == 2 and 1397.0 < out[0]["end"] < 1397.2 and 1397.9 < out[1]["start"] < 1398.15, out


E22 = ROOT / "EPISODES" / "ai-corner" / "E22_quentin-amaudry_mendo"
E22_WAV = E22 / "travail" / "work" / "audio16k.wav"
E22_MP4 = E22 / "rushs" / "E22_quentin-amaudry_mendo.mp4"


def _e22():
    if not E22_WAV.exists():
        raise _Skip("audio E22 absent")
    return E22_WAV


def test_retrait_trop_court_ou_fin_de_mot_tranchee_recolle():
    """14/10/2026 short 2 E22 « les phrases ont tendance à être coupées trop tôt » : « il y ‖ a » (0,14 s retirées en
    pleine voix) et « …mais il ‖ se trouve » (la voix continuait 0,25 s après la coupe)."""
    from clipper.strict import fix_join_flow, join_flow_problems
    wav = _e22()
    segs = [{"start": 1459.63, "end": 1460.28}, {"start": 1460.42, "end": 1462.26},
            {"start": 1488.485, "end": 1499.095}, {"start": 1499.526, "end": 1503.76}]
    why = " ".join(p["why"] for p in join_flow_problems(segs, wav))
    assert "1460.28" in why and ("1499.09" in why or "1499.10" in why), why
    out, _ = fix_join_flow(segs, wav)
    assert len(out) == 2, out


def test_raccord_euh_propre_garde():
    """Contre-épreuve : un vrai retrait de « euh » (short 2 E22, 1473,14 -> 1473,95, coupe dans le silence) reste."""
    from clipper.strict import join_flow_problems
    wav = _e22()
    assert not join_flow_problems([{"start": 1462.79, "end": 1473.14}, {"start": 1473.95, "end": 1476.45}], wav)


def test_bruit_de_bouche_en_fin_de_short():
    """14/10/2026 short 2 E22 « il y a un bruit de bouche à la fin » : claquement à 1503,58 après « …dans des agents »."""
    from clipper.strict import tail_noise
    p = tail_noise(_e22(), 1503.76)
    assert p and 1503.5 < p["noise"] < 1503.65 and p["end"] < p["noise"], p


def test_thomas_a_l_image_pendant_que_l_invite_parle():
    """14/10/2026 short 1 E22 « Thomas coupe la parole à l'invité ; ça sert à rien de mettre l'image et le son de Thomas qui
    acquiesce » : plan de Thomas 1201,625–1203,125 (montage du monteur) pendant « …de tes employés »."""
    import json

    from clipper.ingest import host_reference
    from clipper.strict import listener_shown
    _e22()
    if not E22_MP4.exists():
        raise _Skip("vidéo E22 absente")
    import subprocess
    import tempfile
    words = json.loads((E22 / "travail" / "work" / "diarized_words.json").read_text(encoding="utf-8"))
    cut = Path(tempfile.gettempdir()) / "test_e22_1199.mp4"   # le montage d'un « clip » = 1199–1204 de l'épisode
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1199", "-t", "5", "-i", str(E22_MP4), "-an", "-c:v", "libx264",
                    "-crf", "18", str(cut)], check=True)
    runs = listener_shown(cut, [{"start": 1199.0, "end": 1204.0}], words, host_reference(Brand("ai-corner")), step=0.25)
    hit = [r for r in runs if r["abs0"] < 1203.0 and r["abs1"] > 1201.8]
    assert hit and hit[0]["shown"] == "host", [(r["abs0"], r["abs1"], r["shown"]) for r in runs if r["abs1"] > 1199][:5]


def test_bloc_de_sous_titre_jamais_trop_court():
    """15/10/2026, relecture critique du short 1 E22 : bloc « TU » de 0,06 s (invisible) et « muscle » 0,2 s en fin de bloc."""
    cfg = cfg_for_format(Brand("ai-corner").cfg, "9x16")
    ws = _words([("la", 0.0, 0.2), ("moitié", 0.2, 0.5), ("du", 0.5, 0.6), ("truc", 0.6, 0.9), ("embarquer.", 0.9, 1.4),
                 ("Tu", 1.50, 1.56), ("peux", 1.56, 1.8), ("dire", 1.8, 2.1), ("ok", 2.1, 2.4),
                 ("si", 3.0, 3.1), ("t'as", 3.1, 3.3), ("pas", 3.3, 3.5), ("de", 3.5, 3.7), ("muscle", 3.72, 3.92),
                 ("de", 3.95, 4.0), ("change", 4.0, 4.4), ("t'es", 4.5, 4.7), ("mort.", 4.7, 5.0)])
    caps = group_words(ws, 0.0, 5.5, cfg, ["muscle"], breaks=[1.56, 3.95])
    for a, b in zip(caps, caps[1:]):
        assert b["start"] - a["start"] >= 0.35, f"bloc {a['id']} affiché {b['start'] - a['start']:.2f} s"
    txt = [" ".join(w["text"] for ln in c["lines"] for w in ln) for c in caps]
    assert not any(t.strip().upper().endswith("MUSCLE") for t in txt), txt


def test_mots_cles_espaces_et_expression_entiere():
    """15/10/2026, relecture critique du short 1 E22 : « agent … processus … procurement » (3 italiques en 8 mots, et
    « processus » coloré pour « process ») ; « …PAS DE muscle » / « DE change T'ES MORT » (expression coupée en deux blocs)."""
    cfg = cfg_for_format(Brand("ai-corner").cfg, "9x16")
    ws = _words([("des", 0.0, 0.2), ("agents", 0.2, 0.6), ("mais", 0.7, 0.9), ("un", 1.0, 1.1), ("agent", 1.1, 1.4),
                 ("qui", 1.4, 1.5), ("va", 1.5, 1.6), ("faire", 1.6, 1.8), ("ton", 1.8, 1.9), ("processus", 1.9, 2.3),
                 ("de", 2.3, 2.4), ("procurement.", 2.4, 2.9),
                 ("et", 3.0, 3.1), ("donc", 3.1, 3.3), ("si", 3.3, 3.4), ("t'as", 3.4, 3.6), ("pas", 3.6, 3.7),
                 ("de", 3.7, 3.8), ("muscle", 3.8, 4.1), ("de", 4.12, 4.2), ("change", 4.2, 4.6), ("t'es", 4.7, 4.9),
                 ("mort.", 4.9, 5.2)])
    caps = group_words(ws, 0.0, 5.6, cfg, ["agents", "procurement", "process de travail", "muscle de change"],
                       breaks=[4.12])
    hl = [w["text"].lower() for c in caps for ln in c["lines"] for w in ln if w["hl"]]
    assert "processus" not in hl and "agent" not in hl, hl
    last = [w["text"].lower() for ln in caps[-1]["lines"] for w in ln]
    assert "muscle" in last and "change" in last, [[w["text"] for ln in c["lines"] for w in ln] for c in caps]


def test_raccord_a_2_ms_d_un_mot_ne_cree_pas_de_bloc_d_un_mot():
    """15/10/2026, short 1 E22 passé à 24 i/s : raccord à 17,542 s, mot « et » à 17,54 s -> le raccord coupait aussi avant « tu »
    et « ET » restait seul 0,14 s à l'écran (bloc illisible)."""
    cfg = cfg_for_format(Brand("ai-corner").cfg, "9x16")
    ws = _words([("fait", 17.16, 17.34), ("et", 17.54, 17.68), ("tu", 17.68, 17.78), ("vas", 17.78, 17.88),
                 ("avoir", 17.88, 18.06), ("besoin", 18.06, 18.3), ("que", 18.3, 18.4), ("tes", 18.4, 18.54)])
    caps = group_words(ws, 0.0, 19.0, cfg, [], breaks=[17.542])
    blocks = [[w["text"] for ln in c["lines"] for w in ln] for c in caps]
    assert not any(b[0] == "ET" and len(b) == 1 for b in blocks) and ["ET", "TU"] == blocks[-1][:2], blocks


def test_mot_coupe_avant_un_saut_de_passage():
    """15/10/2026, Thomas (short 1 E22) « à 0:07 le mot "métiers" est complètement croppé » : coupe à 1201,62 posée sur un
    changement de plan, dans un micro-creux du mot, juste avant un saut de passage (1204,95)."""
    from clipper.strict import join_flow_problems
    p = join_flow_problems([{"start": 1197.03, "end": 1201.62}, {"start": 1204.95, "end": 1208.2}], _e22())
    assert p and p[0].get("hard"), p


def test_derniere_image_sur_celui_qui_ecoute():
    """15/10/2026, Arthur (short 1 E22) « enlève le plan avec Thomas à la fin, ça n'apporte rien » : le montage passe sur
    Thomas à 1243,125, la dernière image du short (figée pendant le fondu vers l'outro) le montrait."""
    import json
    import subprocess
    import tempfile

    from clipper.ingest import host_reference
    from clipper.strict import listener_shown
    _e22()
    if not E22_MP4.exists():
        raise _Skip("vidéo E22 absente")
    words = json.loads((E22 / "travail" / "work" / "diarized_words.json").read_text(encoding="utf-8"))
    cut = Path(tempfile.gettempdir()) / "test_e22_fin.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1240", "-t", "3.3", "-i", str(E22_MP4), "-an", "-c:v", "libx264",
                    "-crf", "18", str(cut)], check=True)
    runs = listener_shown(cut, [{"start": 1240.0, "end": 1243.14}], words, host_reference(Brand("ai-corner")))
    end = [r for r in runs if r.get("end")]
    assert end and end[0]["shown"] == "host" and 1242.95 < end[0]["abs0"] < 1243.13, runs


def test_coupes_de_phrase_seulement():
    """19/10/2026, Arthur (comparatif du short 1 E22) « les cuts ne sont pas assez fluides, ça fait trop saccadé, il faudrait
    un entre-deux » puis « c'est mieux, ça saccade moins sans être trop long, généralise la règle » : sur les 7 morceaux de
    la version à 6 coupes, les 3 retraits d'hésitations courtes dans une phrase (0,32 / 1,01 / 1,36 s, dont le faux départ
    « sur ») sont recollés ; les coupes entre phrases (plans de Thomas, mots retirés) restent = la version validée."""
    import json

    from clipper.strict import merge_phrase_cuts
    wav = _e22()
    words = json.loads((E22 / "travail" / "work" / "diarized_words.json").read_text(encoding="utf-8"))
    a = [(1198.5, 1200.27), (1206.42, 1208.205), (1209.215, 1212.385), (1213.745, 1216.18), (1218.125, 1224.195),
         (1224.515, 1226.705), (1232.7, 1240.6)]
    out, _ = merge_phrase_cuts([{"start": s, "end": e, "duration": e - s} for s, e in a], words, wav)
    assert [(x["start"], x["end"]) for x in out] == [(1198.5, 1200.27), (1206.42, 1216.18), (1218.125, 1226.705),
                                                      (1232.7, 1240.6)], out


def test_rythme_des_coupes_juste_milieu():
    """19/10/2026, Arthur : « c'est le juste milieu entre trop de montage et pas assez, c'est bien fluide » (3 coupes / 28 s)
    contre « trop saccadé » (6 coupes / 25 s)."""
    from clipper.strict import cut_rhythm
    a = [(1198.5, 1200.27), (1206.42, 1208.205), (1209.215, 1212.385), (1213.745, 1216.18), (1218.125, 1224.195),
         (1224.515, 1226.705), (1232.7, 1240.6)]
    c = [(1198.5, 1200.27), (1206.42, 1216.18), (1218.125, 1226.705), (1232.7, 1240.6)]
    assert cut_rhythm([{"start": s, "end": e} for s, e in a])[0]
    assert not cut_rhythm([{"start": s, "end": e} for s, e in c])[0]


def test_mots_retires_au_milieu_d_une_phrase():
    """19/10/2026, relecture du short 2 E22 : « …à une entreprise. ‖ réalité de ce qui… », la reprise à 1488,485 avait perdu
    « c'est la » (dits à 1488,11–1488,39) ; contre-épreuve : la reprise avant « c'est » (1488,06) est propre."""
    import json

    from clipper.strict import words_cut_in_phrase
    wav = _e22()
    words = json.loads((E22 / "travail" / "work" / "diarized_words.json").read_text(encoding="utf-8"))
    bad = words_cut_in_phrase([{"start": 1484.98, "end": 1487.695}, {"start": 1488.485, "end": 1490.0}], words, wav)
    assert bad and "c'est" in bad[0], bad
    assert not words_cut_in_phrase([{"start": 1484.98, "end": 1487.695}, {"start": 1488.06, "end": 1490.0}], words, wav)


def test_sous_titre_recale_apres_une_hesitation_gardee():
    """19/10/2026, relecture du short 1 E22 (coupes de phrase seulement) : « pousser, euh… un agent » — Whisper rattachait
    le « euh » gardé au mot suivant, « UN » s'affichait 1,5 s avant d'être dit ; recalé sur le son (CTC)."""
    from clipper.caption_check import realign
    wav = _e22()
    caps = [{"w": w, "s": s, "e": s + 0.2} for w, s in
            [("TU", 1207.44), ("VAS", 1207.60), ("POUSSER", 1207.74), ("UN", 1208.1), ("AGENT", 1209.77), ("QUI", 1210.07)]]
    out, _ = realign(caps, wav, [1207.3, 1210.3])
    un = next(x for x in out if x["w"] == "UN")
    assert 1209.45 < un["s"] < 1209.75, out
    assert abs(next(x for x in out if x["w"] == "TU")["s"] - 1207.44) < 0.05, out   # petits écarts : inchangés


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
