---
name: podcast-clips
description: Pilote tout le process AI Corner avec le framework « clipper » de ce dépôt, des rushs d'un tournage (3 caméras MP4 + audio WAV déposés dans DEPOT/) jusqu'à tous les livrables, en cinq colonnes parallèles — 5 shorts verticaux montés + leur post LinkedIn (10 passages proposés, l'équipe en choisit 5, contrôle qualité, validation, rendu, outro avec la miniature), l'épisode complet monté avec son teaser (dérushage, aperçu, contrôle qualité, validation, rendu 1080p), le titre puis la miniature YouTube (5 titres en texte, l'équipe en choisit un, puis 4 miniatures, l'équipe en choisit une), le carrousel LinkedIn (3 angles proposés, l'équipe en choisit un, slides rédigées et rendues dans la charte AI Partners, CTA « réserver un échange »), le mail podcast de Thomas (newsletter écrite à la 1re personne, mise en page, validée par l'équipe). Déclencher sur « clip », « short », « reel », « découpe mon podcast », « fais des extraits », « nouveau podcast », « monte l'épisode », « teaser », « titre de l'épisode », « miniature », « carrousel », « carousel LinkedIn », « newsletter », « mail de Thomas », « /podcast-clips », ou dès que des rushs ou un épisode sont déposés dans DEPOT/.
---

# Podcast → shorts, épisode complet, titre et miniature, carrousel, mail de Thomas

Tu pilotes le framework `clipper` (voir [CLAUDE.md](../../../CLAUDE.md), le schéma du process dans
[README.md](../../../README.md) et le guide pratique [docs/FRAMEWORK.md](../../../docs/FRAMEWORK.md) : délais, quel fichier modifier). **Lis d'abord [docs/BONNES_PRATIQUES.md](../../../docs/BONNES_PRATIQUES.md)** :
ce qui a été validé sur E22 (le résultat de référence) et ce qu'il ne faut plus jamais faire. L'utilisateur est un membre de l'équipe marketing :
il ne tape aucune commande, tu fais tout et tu lui parles simplement (pas de jargon technique).

**Le process (schéma de référence : « Vue d'ensemble » du README, sur GitHub)** : dépôt des rushs -> `rushes` ->
`transcribe`, puis **cinq colonnes lancées en parallèle**, sans s'attendre :

| Colonne | Étapes | Section |
| --- | --- | --- |
| 5 shorts 9:16 | `propose` -> l'équipe choisit 5 passages -> `polish` (+ `qa`, boucle « à corriger ») -> l'équipe valide les aperçus -> `render` + `posts` -> **`outro`** | 2 à 5 |
| Épisode + teaser | `episode-plan` -> `episode-render --proxy` (+ `qa`, boucle « à corriger ») -> l'équipe valide l'aperçu -> `episode-render` 1080p | « Épisode complet » |
| Titre puis miniature | `titles` (5 titres en texte) -> l'équipe en choisit un -> `thumbnail` (4 miniatures) -> l'équipe en choisit une | « Titre et miniature » |
| Mail de Thomas | `newsletter` (mail écrit + mis en page) -> l'équipe valide -> `newsletter --youtube-url … --final` | « Mail podcast de Thomas » |
| Carrousel LinkedIn | `carousel` (3 angles) -> l'équipe en choisit un -> `carousel --pick N` (slides + post, rendu PDF) -> l'équipe valide -> `carousel --final STYLE` | « Carrousel LinkedIn » |

**Deux seules dépendances entre colonnes** (flèches en pointillés du schéma) :
- **A** — la description YouTube de l'épisode prend le titre validé (`titles --pick`). Si l'épisode est rendu avant, la
  description porte « (titre à valider…) » et `titles --pick` la corrige ensuite : rien n'est bloqué.
- **B** — l'outro des shorts montre la miniature choisie : `outro` ne tourne qu'après `thumbnail --pick`. Le montage, la
  validation et le rendu des shorts, eux, n'attendent pas.

Dès que la transcription est prête, lance donc `propose`, `titles` ET `carousel` (en arrière-plan) et, si l'épisode complet est
demandé, `episode-plan` : l'équipe peut choisir les passages et le titre pendant que le reste tourne.

**Relecture critique avant chaque validation** (Arthur, 12/10/2026) : une fois le contrôle `qa` propre, et AVANT de montrer
un livrable à l'équipe, lance `python -m clipper review --brand <m> --input <E>.mp4 --only N | --episode | --carousel |
--newsletter` : un Claude Opus SANS le contexte de la conversation relit le livrable contre `config/review_checklist.md`.
Défaut ÉCHEC -> corrige (boucle « à corriger ») puis relance ; ATTENTION et remarques de goût -> dis-les à Arthur avec le
livrable. Une seule relecture par version (un livrable inchangé n'est pas relu deux fois) : ne la lance qu'une fois tous
les défauts mesurables corrigés, pour ne pas payer plusieurs relectures.

**Huit moments où l'humain décide** (rien ne passe sans) : les 5 passages, la validation des aperçus des shorts, la
validation de l'aperçu de l'épisode, le titre, la miniature, l'angle du carrousel, la validation du carrousel, la
validation du mail de Thomas. Avant chaque aperçu, la vidéo passe le contrôle
automatique (`qa`) ; tant qu'il montre un défaut, tu corriges et tu recommences (boucle « à corriger ») avant de la
montrer.

## 0. Environnement (une fois par machine)

```bash
python -m clipper doctor
```

Si un point est KO : suis les indications (`-> …`), ou lance `scripts\setup.ps1` (Windows) / `scripts/setup.sh`
(macOS). Ne lance jamais une transcription sur une machine qui n'a pas passé le doctor.

## 1. Récupérer et ranger l'épisode

0. **Rushs déposés dans `DEPOT/`** (cas habituel depuis octobre 2026 : 3 caméras de 13–14 Go + l'audio WAV) :

   ```bash
   python -m clipper rushes --brand <marque> --episode <E-numéro> --guest "Prénom Nom" --company "Entreprise" --dry-run
   ```

   Regarde la planche `rushes_<E>.jpg` (invité / plan large / animateur bien attribués ?), puis relance sans
   `--dry-run` (ajoute `--host <morceau du nom>` si l'animateur est mal reconnu). La commande range et renomme les
   fichiers, mesure le décalage du micro et écrit `<E>_<invité>_<entreprise>.multicam.json` ; elle donne le
   `--input` et le `--host-side` à utiliser ensuite. Un fichier illisible (téléchargement tronqué) est signalé : le
   faire redéposer.

   **Lien Dropbox** (si les rushs n'ont pas été déposés) : ne demande jamais de
   télécharger dans le navigateur — il coupe les gros fichiers au bout d'environ 50 min et garde un fichier tronqué
   illisible (« moov atom not found »). Lance toi-même, en arrière-plan (≈ 40 Go en 1 h 30) :

   ```bash
   python -m clipper fetch "<lien Dropbox>" --dest DEPOT
   ```

   Reprise automatique après coupure (y compris d'un fichier partiel déjà présent : `--dest` vers son dossier),
   fichier déclaré complet seulement à la taille exacte annoncée par Dropbox ; si un fichier reste incomplet, relancer
   la même commande. Puis range-les avec `rushes` comme ci-dessus.
1. Regarde `DEPOT/` (sinon les fichiers récents de Téléchargements). Vérifie toujours qu'une vidéo s'ouvre
   (`ffprobe`) : « moov atom not found » = téléchargement tronqué -> `fetch` (avec le lien) pour la compléter. Range chaque fichier et dis où tu l'as mis :
   épisode → `EPISODES/<marque>/<épisode>/rushs/<E-numéro>_<invite>_<entreprise>.mp4` ; logo de l'entreprise invitée →
   `MARQUES/<marque>/assets/guests/<entreprise>.svg|png` ; clips de référence → `references/` ; logos/polices → `assets/`.
2. Cas normal : les rushs (3 caméras 1080p + WAV), rangés par `rushes`. Si on te donne au contraire un épisode déjà
   monté, prends la **version 4K** si elle existe (bien plus nette en vertical ; `ffprobe` : 3840×2160) ; en 1080p,
   signale-le en une phrase et continue.
3. Demande en UNE salve (AskUserQuestion) uniquement ce qui manque :
   - la marque (`python -m clipper brands` ; par défaut `ai-corner`) ;
   - l'invité : prénom nom, **rôle**, entreprise, et son **logo** (SVG ou PNG transparent) s'il n'est pas déposé ;
   - le côté de l'animateur dans le plan large (gauche / droite) : donné par `rushes` (`--host-side`) ; pour un épisode
     déjà monté, regarde une image (`ffmpeg -ss 600 -i … -frames:v 1`) pour le déduire toi-même avant de demander ;
   - le lien de l'épisode complet (YouTube) s'il existe déjà — sinon les posts finiront par « Link in the comments ».
4. Lance la transcription **en arrière-plan** (≈ 20 min pour 50 min d'épisode sur CPU) :

```bash
python -m clipper transcribe --brand <marque> --input <fichier> --guest "Prénom Nom" --company "Entreprise"
```

   `--guest` / `--company` sont donnés à Whisper (avec le lexique de la marque, `transcribe.vocabulary`) pour qu'il
   écrive correctement les noms propres ; les quasi-homonymes restants sont corrigés automatiquement
   (`transcribe.corrections`). Jette quand même un œil aux noms dans les 10 propositions ; si un terme revient mal
   écrit, ajoute-le au lexique de la marque dans `brand.yaml`.

## 1 bis. Les passages sont déjà choisis (fournis par l'équipe)

Si l'utilisateur colle une liste de passages (timecodes + « De … jusqu'à … »), saute les étapes 2 et 3 :
écris un fichier `EPISODES/<marque>/<épisode>/travail/passages.yaml` puis lance `passages` :

```yaml
- start: "00:18:17:09"          # HH:MM:SS(:images à 24 i/s) ou MM:SS ; « ~ » accepté
  end: "00:18:50:19"
  start_text: "Et donc, il y a un aspect humain qui est énorme"
  end_text: "ils ont pas le temps et l'envie de le faire"
  hook_title: "Pourquoi les équipes n'adoptent pas l'IA ?"   # à écrire s'il n'est pas fourni (style de la marque)
  turns: [{at: "00:18:17", speaker: guest}]                  # qui parle : host (animateur) / guest (invité)
```

```bash
python -m clipper passages --brand <marque> --input <fichier> --file EPISODES/<marque>/<épisode>/travail/passages.yaml --guest "…" --company "…" --guest-role "<Rôle> at <Entreprise>" --host-side left|right
python -m clipper check    --brand <marque> --input <fichier>
```

- **Qui parle** : les `turns` servent au cadrage ET à l'attribution dans les posts (sans eux, le post attribue tout à
  l'invité). Vérifie-le sur des images de l'épisode (`ffmpeg -ss <t> -i … -frames:v 1`, la source montre en général
  celui qui parle) et complète `turns` dans `clips.json`.
- Si la fin citée tombe au milieu d'une phrase, prolonge jusqu'à la fin de la phrase (règle absolue) et dis-le.
- Si une phrase citée est introuvable, Whisper l'a peut-être ratée (deux personnes qui parlent en même temps) :
  re-transcris 20 s autour (faster-whisper, `word_timestamps=True`) et insère les mots manquants dans
  `transcript.json` à leurs horaires, puis coupe juste avant que l'autre personne enchaîne.

Puis reprends à l'étape 4.

## 2. Proposer une dizaine de passages

```bash
python -m clipper propose --brand <marque> --input <fichier> --guest "…" --company "…" --host-side left|right --n 10 [--instructions "…"]
```

Trois lectures de l'épisode en parallèle (une par angle éditorial de la marque), puis un « jury » garde les 10
meilleurs, variés. Sortie : `EPISODES/<marque>/<épisode>/travail/candidates.md` (+ `candidates.json`).

Présente-les à l'utilisateur dans le chat, numérotés, chacun en 3 lignes : **le titre de la bulle** (la question),
le thème + timecodes + durée, et une phrase-clé de ce qu'on entend. Puis demande :
« Lesquels gardez-vous ? (5 numéros, ex. 1, 3, 4, 7, 9) — et y a-t-il un passage précis que vous voulez
absolument, ou quelque chose à éviter ? »

## 3. Choix de l'utilisateur et demandes particulières

```bash
python -m clipper pick --brand <marque> --input <fichier> --ids 1,3,4,7,9
```

Pour chaque demande particulière :
- « il faut absolument le passage où il dit … » → `python -m clipper find --brand … --input … "mots de la phrase"`
  donne le timecode et le contexte. Intègre ce passage au short le plus proche par le thème (comme accroche ou
  conclusion), ou remplace un candidat — en éditant `segments` dans `EPISODES/…/travail/clips.json` (début = début d'une
  phrase, fin = fin d'une phrase) ; dis à l'utilisateur ce que tu as fait.
- « pas ce sujet / pas ce chiffre » → retire ou recoupe le segment concerné.
- un changement de titre de bulle → `hook_title` dans `clips.json`.

Puis **vérifie chaque coupe mot à mot** (règle absolue : ne jamais couper une pensée) :

```bash
python -m clipper check --brand <marque> --input <fichier>
```

Chaque passage doit commencer au début d'une phrase et finir sur une fin de phrase complète ; jamais de mot du
passage suivant. Corrige dans `clips.json` et relance `check`.

## 4. Nettoyer, monter et contrôler — `polish` (une seule commande, contrôles à chaque étape)

```bash
python -m clipper polish --brand <marque> --input <fichier> --only 1,2,3,4,5      # arrière-plan, ≈ 6–8 min/short
```

`polish` enchaîne, pour chaque short, dans UN seul processus (Whisper chargé une fois). Process **validé par Arthur le
12/10/2026** (« c'est clean, le process a l'air de fonctionner ») — l'équipe marketing exige mieux que le monteur actuel :

1. `tighten` — blancs et « euh » entre les mots (trous > 0,6 s ; en dessous = respiration, on garde) ;
2. `verify --fix` — vraies fins de phrase (ponctuation stable + vraie pause), bords recalés sur la voix, « euh » isolés
   retirés, chaque fin attend la fin de la voix + ~0,35 s de respiration sans entendre la phrase suivante (`pad_end`) ;
3. `fillers` — « euh » collés aux mots (voyelles tenues) ; jamais un mot perdu, jamais un raccord dans un mot ;
4. réactions vides retirées (« super intéressant »…) ;
5. `joins` — retraits coupés en pleine voix recalés : la fin du mot et l'attaque du suivant sont gardées ;
6. `ctc` — **mots alignés sur le son** (wav2vec2 français) : toute voix sans mot ≥ 0,35 s entre deux mots est retirée
   (« euh » que `fillers` n'a pas pu couper, « hmm » d'acquiescement de l'animateur) ; mots élidés (« qu'il ») jamais coupés ;
7. `build` — montage ; **son reconstruit en un seul passage** depuis le micro (à l'échantillon près, fondus de 6 ms, un seul
   réglage de volume ; jamais de son recollé morceau par morceau : il dérivait de ~25 ms par raccord) ; sous-titres
   contrôlés à l'écoute (2 écoutes) ; flash lumineux seulement quand l'angle de caméra change ;
8. `qa` — **contrôle intransigeant** (rapport `qa/clip_NN.md`) : raccords à l'écoute (mot coupé), fins jamais pendant la
   voix, bords de phrase stricts (voix retombée sous 10 % pendant 0,12 s), **pensée finie** (Smart Turn : fin du short
   < 0,5 = ÉCHEC), synchro du **fichier** monté (± 15 ms par morceau), sous-titres jamais superposés, composition, durée ;
9. **boucle de correction automatique, 6 tours** : bord de phrase dans la voix -> recalé dans le silence ; raccord entendu
   dans un mot -> ce retrait est annulé ; puis remontage et nouveau contrôle. Ce qui reste en ÉCHEC n'a ni aperçu ni rendu ;
10. aperçus **MP4** (12 i/s) dans `EPISODES/…/travail/apercus/` ;
11. `qa --render` — 2e contrôle sur l'aperçu : format, durée, volume -16 LUFS, **aucun écran noir**, une **planche d'images**
    (`qa/qa_images_NN.png`, à REGARDER avant d'envoyer le lien) et le **film des moments à risque** (`qa/moments_NN.mp4` :
    chaque raccord ± 1,5 s + la fin, ~20–40 s), à donner avec chaque short.

Les étapes 1–6 déjà faites sont sautées (`checks` dans `clips.json`) ; `--redo` repart des passages d'origine
(`clips_before_tighten.json`). Sauvegardes : `clips_before_fillers.json`, `clips_before_ctc.json`.

**Après tout changement de code** du nettoyage ou des contrôles : `python scripts/test_qualite.py` (cas réels E22, tous
OK attendus). **Chaque défaut signalé par l'équipe** (short + seconde) -> corrigé ET ajouté comme test dans ce script.

**Boucle « à corriger » (Arthur, 09/10/2026)** : lis chaque rapport `qa/clip_NN.md` et regarde chaque planche. Ce que la
boucle automatique n'a pas réglé (ÉCHEC restant, ATTENTION qui s'entend ou se voit) -> corrige toi-même (`clips.json` :
passages, coupes, `hook_title` ; ou la config) et relance `polish --only N`. Pour un passage difficile (hésitations en
cascade), place les coupes d'après l'alignement (`clipper.endpoint.align`) et l'énergie du son, pas d'après Whisper.
Seuls les shorts propres partent en validation ; dis ce que tu as corrigé.

Puis le **3e contrôle, humain** : envoie à l'utilisateur les liens cliquables vers les MP4 (jamais seulement le
Studio HyperFrames, qui bugue chez Arthur), un par short, avec le titre de la bulle, plus ce que le rapport `qa`
signale (ATTENTION) et les instants à écouter de près :

> 1. [Short 1 : <titre de la bulle>](EPISODES/<marque>/<épisode>/travail/apercus/clip_01_…_9x16_apercu.mp4)
> 2. [Short 2 : <titre de la bulle>](EPISODES/<marque>/<épisode>/travail/apercus/clip_02_…_9x16_apercu.mp4)
> …
>
> Aperçus rapides (image un peu saccadée, normal) : dites-moi ce que vous voulez changer.

Pendant qu'il regarde, rédige les posts (ils ne dépendent pas du rendu) :

```bash
python -m clipper posts --brand <marque> --input <fichier> --guest-role "<Rôle> at <Entreprise>" [--episode-url URL]
```

Les posts suivent `MARQUES/<marque>/posts.md` (méthode « post d'un short » : accroche-thèse, contraste, invité,
développement concret, chute, CTA ; anglais pour AI Corner, sans hashtags). Relis-les : rien d'inventé (chiffre,
exemple, citation absents du short), deux posts ne commencent pas pareil.

Retouches : modifie `clips.json` (passages, `hook_title`) ou la config de la marque, puis `polish --only N`. **Chaque
retour qui vaut pour la suite devient une règle durable** (code ou config + CLAUDE.md + mémoire), avec la date et
la phrase de l'utilisateur. Recommence jusqu'à ce que l'utilisateur valide **tous** les shorts. Jamais de rendu
final avant cette validation explicite.

## 5. Rendu final, dernier contrôle et livraison

```bash
python -m clipper render --brand <marque> --input <fichier> --formats 9x16 --only N    # ≈ 10 min/short, 2 en parallèle : arrière-plan
python -m clipper qa     --brand <marque> --input <fichier> --only N --render          # contrôle du MP4 final + planche d'images
```

- Ne réécrase jamais un MP4 déjà livré : renomme l'ancien (`…_v1_<date>.mp4`) avant le rendu (un fichier ouvert
  dans le lecteur de l'utilisateur bloque l'écriture).
- `qa --render` doit être OK (ou ATTENTION expliquée) ; regarde la planche d'images du MP4 final.
- `outro` vérifie chaque livrable : H.264 `yuv420p` (sinon illisible sur Windows / téléphone), aucun écran noir entre le
  short et l'outro. Miniature pas encore choisie : `outro --thumb <image>` -> `livrables_provisoires/` (provisoire).
- Les shorts sont rendus SANS carte de fin. Dès que l'équipe a choisi la miniature (`thumbnail --pick`, section « Titre et
  miniature »), lance `python -m clipper outro --brand <marque> --input <fichier>` : l'outro « carte YouTube » avec la
  miniature est rendue une fois et collée à chaque short -> `EPISODES/<marque>/<épisode>/travail/livrables/`. Un short signalé
  « À REFAIRE » a encore l'ancienne carte intégrée : `build --only N --force` puis `render --only N`, puis relance `outro`.
- Envoie les MP4 de `livrables/` (pas `renders/`) avec SendUserFile, dans l'ordre ; colle pour chaque short le titre, la
  durée et son **post LinkedIn** prêt à copier ; donne le chemin du dossier.

## Envoi de la newsletter : `newsletter --envoi` puis n8n (validé par Arthur le 13/10/2026)

Après la validation du mail (`newsletter --final`) : `python -m clipper newsletter … --envoi` publie les images et le mail
sur GitHub Pages (`docs/newsletters/<E>/`, à pousser avec git) avec « Bonjour {{prenom}}, » et un lien de désinscription.
Envoi : workflow n8n « AI Corner — test newsletter » (export : `n8n/newsletter_test.workflow.json`) — paramètres
(destinataire, prénom, épisode) -> lit le mail en ligne -> Gmail au nom de Thomas Spitz. Toujours un envoi de TEST à
soi-même d'abord ; l'envoi à la liste (Sheet de contacts, paquets, compte de Thomas) est à construire : voir `n8n/README.md`.
Ne jamais supprimer `docs/newsletters/<E>/` d'une newsletter envoyée.

## Livraison : `livraison` (Arthur, 13/10/2026 : « un dossier avec toutes les versions finales, à copier dans le Drive »)

```bash
python -m clipper livraison --brand <marque> --input <fichier>
```

Copie les versions finales dans `EPISODES/<marque>/<épisode>/LIVRABLES/` (épisode + miniature + titre et description,
shorts + posts, carrousel, newsletter, teaser) et écrit `LISEZMOI.md` : l'état de chaque livrable (✅ / ⚠️ À REVOIR /
❌ MANQUANT, avec la commande pour corriger). Relance-la après chaque retouche et donne à l'utilisateur le lien vers
`LIVRABLES/` et ce qui reste ⚠️ ou ❌. Arborescence complète : CLAUDE.md, « Arborescence ».

## Épisode complet (rushs multicam -> épisode monté + teaser)

Sur demande (« monte l'épisode en entier »), dès la transcription prête :

1. `python -m clipper episode-plan --brand <m> --input <ep>.mp4 --guest … --company … --host "…"` : dérushage par Claude
   (dernière prise de l'intro, hors antenne, questions reposées, au revoir), qui parle quand, raccords nettoyés, liste de
   plans façon monteur (on voit toujours celui qui parle), teaser scripté puis vérifié à l'écoute, chapitres. Relis
   `episode_plan.md` toi-même (coupes, teaser, % de plans) : c'est ta matière pour l'étape 3.
2. `episode-render … --proxy` (aperçu 540p, ~15 min) : il enchaîne le contrôle qualité (`qa/episode_apercu.md` : raccords
   réécoutés, celui qui parle à l'image, volumes, images). **Boucle « à corriger »** : ÉCHEC ou point à corriger ->
   retouche (`episode_plan.json`, coupes, teaser) et nouvel aperçu, jusqu'à un contrôle propre.
3. ALORS seulement envoie l'aperçu (SendUserFile) avec le résumé de `episode_plan.md` (durée, coupes, extraits du
   teaser) : l'équipe valide ou demande une retouche (retour à l'étape 2).
4. Après validation seulement : `episode-render …` (1080p, ~1 h, arrière-plan ; pour juger seulement teaser + raccord +
   volumes : `episode-render … --proxy --minutes 2`, ~5 min). Le contrôle du MP4 final est enchaîné automatiquement
   (`qa/episode.md` : chaque raccord réécouté, aucun « euh », aucun mot coupé, volumes teaser / épisode à ±1,5 LUFS,
   planche d'images à regarder). Joins `episode/description_youtube.md` (titre validé + chapitres ; dépendance A).

Teaser et corps sont rendus séparément : retoucher le teaser ne refait pas le corps (~15 min au lieu d'1 h).

## Titre et miniature de l'épisode (rushs multicam)

Le titre de l'épisode est validé par l'équipe marketing AVANT les miniatures. À lancer après `transcribe`, en parallèle des
shorts (aucune attente mutuelle) :

1. `python -m clipper titles --brand <marque> --input <E>.mp4` : 5 titres contrôlés, en TEXTE (chacun prouvé par un passage
   de l'épisode, format `AI Corner E<n> | …`, brief `MARQUES/<marque>/titles.md`). Donne les 5 titres à Arthur pour l'équipe
   marketing, avec le lien vers `titres/propositions.md`. Aucune miniature à ce stade.
2. L'équipe répond par un numéro (ou corrige une ligne) : `titles … --pick N [--lines "ligne 1 | *ligne 2"] --by <prénom>
   --note "<remarque>"`. Toute remarque de fond devient une ligne « À éviter » ou une règle dans `titles.md`.
3. `python -m clipper thumbnail --brand <marque> --input <E>.mp4` : planche numérotée de 4 miniatures avec le titre validé (photos
   où les deux sourient en se regardant). Regarde `miniatures/planche.jpg` avant de l'envoyer à Arthur pour l'équipe.
4. L'équipe répond par le numéro de sa préférée : `python -m clipper thumbnail … --pick N --by <prénom>` -> `miniatures/
   miniature_finale.jpg` (+ `_HD.png`) : le livrable à téléverser sur YouTube avec le titre validé.

`thumbnail` s'arrête s'il n'y a pas de titre validé ; la description YouTube de l'épisode reprend le même titre. Dès la
miniature choisie, lance `outro` (étape 5, dépendance B) si des shorts sont déjà rendus.

## Carrousel LinkedIn (donner de la valeur à la communauté, CTA « réserver un échange »)

Demande d'Arthur (12/10/2026). En français, charte AI Partners, 1080 × 1350, PDF à publier comme « document » LinkedIn.
Brief éditorial : `MARQUES/<marque>/carousel.md` ; CTA final : `carousel.cta` de `brand.yaml` (jamais écrit par Claude).
À lancer après `transcribe`, en parallèle de tout le reste :

1. `python -m clipper carousel --brand <marque> --input <E>.mp4` : 3 angles de types différents (méthode, leçons, idées
   reçues, erreurs, cas, chiffres), chacun prouvé par des citations retrouvées dans l'épisode -> `carrousel/angles.md`.
   Donne les 3 angles à Arthur pour l'équipe marketing.
2. L'équipe choisit : `carousel … --pick N [--note "précision"]` : Claude rédige 6 à 8 slides + le post, contrôlés (citations
   mot pour mot, chiffres présents dans l'épisode, longueurs), puis rendu PNG + PDF dans le style de la marque
   (`carousel.style` ; AI Corner : `mix`, couverture photo de l'invité + slides navy à cartes blanches) avec une planche
   (`carrousel/planche.jpg`). Style vide = tous les styles rendus pour que l'équipe choisisse. REGARDE la planche et au moins la couverture, une slide de contenu et le CTA en grand avant
   d'envoyer : texte qui déborde (cadre rouge), photo sur le titre, logo invisible.
3. Contrôle ÉCHEC ou retouche demandée : corrige `carrousel/contenu.json` toi-même puis `carousel … --render` (aucun appel à
   Claude) ; boucle jusqu'à un contrôle propre.
   Le post LinkedIn (`carrousel/post_linkedin.md`) présente le carrousel en 3 à 5 lignes et finit par le lien de
   réservation (`carousel.cta.booking_url`, ajouté par le framework) : le lien n'est cliquable QUE dans le texte du post,
   LinkedIn affiche les pages d'un carrousel comme des images ; la dernière slide dit donc « Lien dans le post 👇 ».
4. L'équipe valide le texte, le post et le style : `carousel … --final STYLE --by <prénom>` -> `carrousel/final/` (PDF +
   PNG + `post_linkedin.md`, à publier ensemble : post + document). Au 1er choix de style, écris `carousel.style: <style>` dans brand.yaml (les épisodes suivants
   n'ont plus qu'un style). Toute remarque de fond devient une règle dans `carousel.md` (« À éviter »).

## Mail podcast de Thomas (idée de Thomas, 08/10/2026)

Un mail qui part de Thomas (fondateur), en plus de la newsletter d'AI Partners, pour valoriser chaque épisode. Modèle :
le mail « Nostra » d'On Train. Mis en page, en français, vouvoiement. Brief : `MARQUES/<marque>/newsletter.md`.

1. `python -m clipper newsletter --brand <marque> --input <E>.mp4` (après `episode-plan` pour les chapitres ; idéalement
   après `thumbnail --pick`) : Claude écrit le mail à la 1re personne (objet, aperçu, accroche, l'invité, « Au programme »
   en 4 points, mot de fin) ; faits et chiffres contrôlés ; rendu `newsletter/email.html` + `images/` + `apercu.png`.
   REGARDE `apercu.png` (bandeau, photo, miniature) avant de l'envoyer à Arthur. Titre ou miniature encore provisoires :
   le dire.
2. Retouche : `newsletter/contenu.json`, puis `newsletter … --render` (sans nouvel appel à Claude).
3. Une fois l'épisode publié : `newsletter … --youtube-url <lien> --render`, puis après validation de l'équipe
   `newsletter … --final --by <prénom>` -> `newsletter/final/` (HTML + images à importer dans l'outil d'envoi, objet,
   version texte). `--final` refuse sans lien YouTube, sans titre validé ou sans miniature choisie.

## Retouches courantes

| Demande | Action |
| --- | --- |
| « coupe trop tôt / trop tard » | ajuster `segments` dans `clips.json`, `check`, `polish --only N` ; après livraison : renommer l'ancien MP4, `render --only N`, `qa --render --only N` |
| « autre titre dans la bulle » | `hook_title` dans `clips.json`, `polish --only N` ; après livraison : idem |
| « il reste des euh » | `polish --only N --redo` ; si un « euh » précis reste, le signaler (instant) : seuil de `fillers.held_vowels` |
| « il manque des mots dans les sous-titres » | lire `clips/<clip>/captions_check.txt` (RESTE = écart) ; `captions.double_check` doit être actif |
| « c'est saccadé » | ne pas ajouter de coupes : voir `framing` (max_shot_len, min_reframe_len) dans `brand.yaml` |
| « refais le post » | `posts --only N --force` (ajouter une consigne dans `posts.md` si c'est un défaut récurrent) |
| « autre titre d'épisode » | `titles … --pick M` (ou `--lines`), puis `thumbnail` (nouvelle planche), choix, `thumbnail --pick N`, puis `outro` |
| « autre miniature » | `thumbnail … --pick N` (autre numéro), puis `outro` : l'outro est re-rendue avec la nouvelle miniature |
| « un autre angle de carrousel » | `carousel … --pick M` (angle déjà proposé) ou `carousel` (3 nouveaux angles) |
| « change le texte d'une slide » | `carrousel/contenu.json`, puis `carousel … --render` |
| « l'outro ne va pas » | réglages `short_outro:` de `brand.yaml` (texte du bouton, titre), puis `outro --force` |
| « nouvelle marque / autre podcast » | `python -m clipper new-brand <slug>`, puis brand.yaml, guidelines.md, posts.md (voir README) |

## Garde-fous

- Jamais de montage sans le choix explicite de l'utilisateur (étape 3), jamais de rendu final sans sa validation
  sur l'aperçu (étape 4) ; jamais de miniature avant le titre choisi, jamais d'outro avant la miniature choisie, jamais
  de shorts livrés depuis `renders/` (sans outro) : toujours depuis `livrables/`.
- Jamais d'aperçu montré à l'équipe tant que le contrôle `qa` signale un défaut que tu peux corriger.
- Un short qui dépasse un peu la durée cible pour finir une idée est correct ; un short coupé au milieu ne l'est pas.
- Ne modifie pas `config/defaults.yaml` pour un besoin propre à une marque : passe par `MARQUES/<marque>/brand.yaml`.
- Un retour de l'utilisateur sur le style qui vaut pour la suite (« moins de coupes », « logos plus grands »)
  se règle dans la config de la marque ou le preset, pas seulement sur ce short — et se note dans CLAUDE.md.
- Toute modification du PROCESS (étape ajoutée, retirée, déplacée, nouvelle validation, nouvelle dépendance) : mets à
  jour le schéma de GitHub (`docs/schema.mmd` puis `python scripts/render_schema.py`, `docs/ARCHITECTURE.md`), ce skill,
  lance `python scripts/check_schema.py`, puis pousse (CLAUDE.md, « Règle de maintenance »).
