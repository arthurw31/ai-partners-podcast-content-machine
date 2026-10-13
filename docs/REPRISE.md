# Reprise de session — état au 12/10/2026

À lire par une nouvelle session Claude Code qui reprend le projet (changement de compte Claude : même PC, mêmes
dossiers). Les règles durables sont dans [CLAUDE.md](../CLAUDE.md) ; ce fichier dit **où on en est** et **ce qui reste**.

## Contexte en 5 lignes

- Projet : framework `clipper` qui transforme un podcast en shorts verticaux + posts LinkedIn, et désormais en
  **épisode complet monté** + **teaser** à partir des **rushs multicam** (3 caméras + 1 WAV).
- Utilisateur : Arthur (AI Partners), non-développeur ; il parle en français, veut des explications simples, des liens
  cliquables vers les aperçus, et que **chaque retour devienne une règle durable** (code/config + CLAUDE.md).
- Marque en cours : `ai-corner` (podcast AI Corner d'AI Partners). Épisode en cours : **E22**, Thomas Spitz (CEO AI
  Partners, animateur, à gauche dans le plan large) reçoit **Nicolas Comestaz**, VP Global Data & AI CoE chez **Coty**.
- Règle d'or : **ne jamais produire un MP4 final sans validation d'Arthur sur l'aperçu** (HyperFrames Studio pour
  shorts/teaser, aperçu 540p pour l'épisode complet).
- Économie de tokens : Arthur conçoit avec Opus et fait tourner avec Sonnet.

## Fichiers de E22

| Quoi | Où |
|---|---|
| Rushs (40 Go, non versionnés) | `brands/ai-corner/episodes/rushes/E22/cam1_nicolas.mp4`, `cam2_large.mp4`, `cam3_thomas.mp4` |
| Audio micro | `brands/ai-corner/episodes/E22_nicolas-comestaz_coty.wav` |
| « Épisode » (lien dur vers le plan large) + description des caméras | `E22_nicolas-comestaz_coty.mp4` + `E22_nicolas-comestaz_coty.multicam.json` |
| Tout le travail généré | `output/ai-corner/e22-nicolas-comestaz-coty/` (transcript, clips.json, teaser_*, episode_plan.*, work/) |

Commande de base : `python -m clipper <commande> --brand ai-corner --input E22_nicolas-comestaz_coty.mp4`
(+ `--guest "Nicolas Comestaz" --company Coty --host "Thomas Spitz (CEO AI Partners)"` pour `episode-*`).

## Où on en est (12/10/2026)

1. **Process des shorts validé par Arthur le 12/10/2026** (« c'est clean, le process a l'air de fonctionner ») :
   `polish` = nettoyage (tighten, verify, fillers, réactions, joins, **ctc** : « euh » / « hmm » retirés d'après les mots
   alignés sur le son) -> montage (**son reconstruit en un passage**, plus de dérive par raccord) -> **contrôle
   intransigeant** (`strict.py` + `endpoint.py` : bords de phrase stricts, pensée finie par Smart Turn, synchro du fichier,
   sous-titres jamais superposés, aucun écran noir) -> **boucle de correction auto, 6 tours** -> aperçus -> 2e contrôle +
   film des moments à risque. Tests : `python scripts/test_qualite.py` (11/11). Détails : CLAUDE.md « Boucle de
   vérification intransigeante », skill `podcast-clips` § 4.
2. **Shorts 1 et 2 E22 refaits avec ce process, rendus 1080p + outro** (miniature PROVISOIRE, variante 1, l'équipe n'a pas
   encore choisi) : `livrables_provisoires/clip_01_…_9x16.mp4` (55,2 s) et `clip_02_…_9x16.mp4` (40,7 s). Anciennes
   versions gardées dans `renders/` (suffixes `_v…_1110` / `_1210`).
3. **Teaser + épisode complet : rendus finaux validés le 09/10/2026** — `episode/E22_teaser_final.mp4` et
   `episode/E22_nicolas-comestaz_coty_episode.mp4`. Depuis : fin du teaser = animation logo AI Partners (règle permanente,
   aperçu `apercus/E22_teaser_fin-logo_apercu.mp4`) et liste de plans « on voit toujours celui qui parle » (aperçu
   `episode/E22_nicolas-comestaz_coty_episode_apercu.mp4`, QA OK) : **rendu final 1080p en attente de validation**. Le
   teaser a été monté avec l'ANCIEN assemblage du son : probablement la même dérive par raccord -> à refaire avec le
   nouveau (`episode-render` le reconstruit, puis `qa`).

## Aperçus

Toujours en MP4 (le Studio HyperFrames bugue chez Arthur) : `preview --mp4 --clip N` (12 i/s, ~2–3 min) ou via
`polish` ; épisode : `episode-render … --proxy [--minutes 2]`. Donner des liens cliquables vers les fichiers.

## Ce qui reste à faire (dans l'ordre probable)

1. FAIT le 13/10/2026 : shorts 3, 4, 5 avec le process validé, rendus 1080p + outro -> `livrables/` (les 5 shorts E22
   sont livrés). Posts LinkedIn des shorts 1 à 5 à relire / régénérer (`posts --force`) si les passages ont changé.
2. FAIT le 13/10/2026 : teaser reconstruit avec le nouveau son (synchro OK) + épisode complet rendu en 1080p
   (`episode/E22_nicolas-comestaz_coty_episode.mp4`, 47 min, QA OK ; anciennes versions `_v3_0910`).
3. FAIT le 12/10/2026 : titre validé par Arthur (proposition 4 de la 2e série : « AI Corner E22 | Réinventer ses processus
   métier pour intégrer vraiment l'IA »), miniature = même photo que la variante 1 avec ce titre (`miniatures/miniature_finale.jpg`),
   shorts 1 et 2 livrés avec l'outro définitive dans `livrables/`. Shorts 3–5 : `outro --only N` après leur rendu.
4. CTA « bosser avec nous » dans les descriptions YouTube / posts LinkedIn : prêt mais désactivé (attendre Arthur).
5. Les anciens fichiers (`renders/*_v…`, `E22_teaser_v2/_v3`) peuvent être supprimés par Arthur (pas par Claude).

## Points techniques à connaître (détails dans CLAUDE.md)

- Chemin normal d'un short : `polish` puis `render` puis `qa --render` (skill + CLAUDE.md, « Workflow double /
  triple check »). Commandes : `fetch`, `tighten`, `verify`, `fillers`, `polish`, `qa`, `episode-plan`, `episode-render`. Modules : `multicam.py`, `diarize.py`, `episode.py`, `verify.py`, `fetch.py`, `tighten.py`, `fillers.py`,
  `caption_check.py`, `qa.py`.
- `claude -p` (utilisé par l'outil pour choisir les extraits et écrire les posts) a sa propre connexion : si elle a
  expiré (« OAuth session expired »), lancer `claude auth login` dans un terminal et valider dans le navigateur
  (avec le NOUVEAU compte). Le teaser utilise Opus via ce canal (`episode.teaser_model`).
- Le PC n'a pas de GPU : transcription ≈ 0,4× la durée, rendu HyperFrames ≈ 12× la durée du clip. Garder le PC branché.
- Windows bloque certaines DLL (sherpa-onnx) : ne pas toucher au réglage de sécurité.
