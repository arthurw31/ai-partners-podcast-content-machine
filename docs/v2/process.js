// Contenu du schéma v2 (vue d'ensemble + détail de chaque process). SEULE source de la page docs/v2/index.html :
// ajouter, retirer ou modifier une étape = modifier ce fichier, la page suit.
// Acteurs : "claude" (Claude écrit ou juge), "equipe" (un humain choisit ou valide), "auto" (le code calcule tout seul),
// "entree" (ce qu'on dépose), "livrable" (ce qu'on obtient).
// Durées : ordres de grandeur mesurés sur E21 / E22 (épisode de ~52 min), calcul sur le PC sans carte graphique.
window.PROCESS = {
  title: "AI Partners Podcast Content Machine",
  tagline: "Un tournage déposé devient 5 shorts, l'épisode monté, son titre et sa miniature, un carrousel LinkedIn et un mail de Thomas.",
  input: { title: "Rushs du tournage", text: "3 caméras + le micro, déposés dans DEPOT/" },

  // Rendez-vous entre process : une validation de l'équipe qui débloque une étape ailleurs. Seule source des dépendances
  // (bande « Rendez-vous » de la vue d'ensemble, cadenas dans les vues détaillées). step = numéro d'étape à partir de 0.
  milestones: [
    { title: "Titre validé", from: { proc: "titre", step: 3 },
      unlocks: [{ proc: "episode", step: 4, what: "la description YouTube de l'épisode" }] },
    { title: "Miniature choisie", from: { proc: "titre", step: 5 },
      unlocks: [{ proc: "shorts", step: 10, what: "l'outro des shorts" }, { proc: "mail", step: 2, what: "la mise en page du mail" }] }
  ],

  processes: [
    {
      id: "preparation", num: 1, title: "Préparation", group: "start",
      pitch: "Les rushs sont reconnus, calés et transcrits mot à mot.",
      deliverable: "Transcription et « qui parle »",
      duration: "≈ 25 min pour 52 min d'épisode",
      status: { level: "ok", text: "En production depuis E22" },
      summary: "Tout part d'ici : les 5 process en dessous lisent la transcription et savent à chaque mot qui parle (Thomas ou l'invité).",
      improve: [
        "Premier épisode en 4K pas encore testé : surveiller la durée de l'analyse des visages.",
        "Décalage du micro E22 (-0,037 s mesuré contre +0,037 s dans le fichier) : à trancher."
      ],
      steps: [
        { actor: "entree", title: "Dépôt des rushs", short: "3 caméras (gros plan invité, plan large, gros plan Thomas) + 1 fichier son, dans DEPOT/.",
          details: ["Si les fichiers sont restés sur Dropbox : téléchargement avec reprise automatique (jamais par le navigateur, il coupe vers 50 min)."],
          cmd: "python -m clipper fetch \"<lien Dropbox>\"" },
        { actor: "auto", title: "Rushs reconnus et rangés", short: "Chaque caméra est identifiée et le son du micro est calé sur l'image.",
          details: ["Plan large = la caméra qui montre deux visages.",
                    "Caméra de Thomas = le visage qui ressemble le plus à sa photo de référence (empreinte de visage SFace).",
                    "Côté de Thomas dans le plan large mesuré (il change d'un épisode à l'autre).",
                    "Décalage du micro mesuré en comparant son son à celui des caméras.",
                    "Tout est rangé dans EPISODES/<marque>/<épisode>/rushs/."],
          checks: ["Fichier tronqué ou illisible : ignoré et signalé.", "Planche d'images rushes_<E>.jpg à regarder pour confirmer."],
          cmd: "python -m clipper rushes --brand ai-corner --episode E23 --guest \"Prénom Nom\" --company X",
          files: ["rushs/cameras/*.mp4", "rushs/<épisode>.multicam.json", "rushs/rushes_<E>.jpg"] },
        { actor: "auto", title: "Transcription mot à mot", short: "Whisper écrit chaque mot avec son instant exact.",
          details: ["Modèle Whisper large-v3-turbo, sur le PC.", "Noms de l'invité et de l'entreprise donnés à Whisper pour qu'il les écrive juste, puis table de corrections."],
          duration: "≈ 0,4 × la durée de l'épisode", cmd: "python -m clipper transcribe …", files: ["travail/transcript.json"] },
        { actor: "auto", title: "Qui parle", short: "Chaque mot est attribué à Thomas ou à l'invité, d'après les voix.",
          details: ["Empreintes vocales (WeSpeaker) regroupées en 2 voix, nommées grâce à l'intro de Thomas.", "Changements de voix recalés sur le silence le plus proche."],
          duration: "≈ 2 min", files: ["travail/work/diarized_words.json"] }
      ]
    },

    {
      id: "shorts", num: 2, title: "5 shorts", group: "main",
      pitch: "Claude propose 10 passages, l'équipe en garde 5, la machine monte et contrôle chaque short.",
      deliverable: "5 shorts verticaux + 5 posts LinkedIn",
      duration: "≈ 20 à 30 min de calcul par short",
      status: { level: "ok", text: "Validé sur E22, en cours sur E21" },
      summary: "Le process le plus contrôlé : chaque short passe par un nettoyage du son en plusieurs couches, puis une boucle de contrôle « intransigeante » qui corrige toute seule, avant que l'équipe ne le voie.",
      improve: [
        "Un « hmm » de Thomas prononcé PAR-DESSUS la voix de l'invité ne peut pas être retiré (micro unique).",
        "Épisodes déjà montés (E21) : l'image vient du monteur, les plans de réaction sont retirés à la main."
      ],
      steps: [
        { actor: "claude", title: "Claude propose ~10 passages", short: "Il lit l'épisode phrase par phrase et choisit les moments forts.",
          details: ["Chaque passage cite ses premiers et derniers mots exacts : les coupes sont calées sur ces mots.",
                    "Règle d'or : jamais couper une pensée (début de phrase, fin de phrase complète).",
                    "Plusieurs angles en parallèle, puis un jury de Claude garde les meilleurs."],
          cmd: "python -m clipper propose --brand ai-corner --input <épisode>.mp4", files: ["travail/candidates.md"] },
        { actor: "equipe", title: "L'équipe choisit 5 passages", short: "Plus d'éventuelles demandes : un passage précis, un autre découpage.",
          cmd: "python -m clipper pick … / find / check" },
        { actor: "auto", title: "Nettoyage du son", short: "Les hésitations sont retirées sans jamais couper un mot.",
          details: ["tighten : blancs et « euh » entre les mots (retraits de 0,6 s et plus).",
                    "verify : réécoute mot à mot, repère « euh », mots répétés, mots coupés.",
                    "fillers : « euh » collés aux mots (voyelle tenue), chaque coupe validée par une nouvelle écoute.",
                    "Réactions vides retirées (« super intéressant », « d'accord »).",
                    "ctc : alignement précis des syllabes, retire les « hmm » et les répétitions.",
                    "joins : chaque raccord recalé au point le plus silencieux."],
          origin: "Retours d'Arthur du 07 au 12/10/2026 : « enlève les euh », « des phrases coupées trop tôt »." },
        { actor: "auto", title: "Montage et sous-titres", short: "Gros plan sur celui qui parle, écran partagé de temps en temps, sous-titres de la charte.",
          details: ["Gros plan de la personne qui parle ; écran partagé (invité en haut, Thomas en bas) toutes les 7 à 9 s, seulement si celui qui écoute est calme.",
                    "Sous-titres « variante B » : capitales Metropolis + un mot-clé en italique jaune, choisi par Claude.",
                    "Sous-titres réécoutés deux fois : un mot entendu mais pas écrit est ajouté.",
                    "Son reconstruit en un seul passage, volume à -16 LUFS."],
          cmd: "python -m clipper polish --brand ai-corner --input <épisode>.mp4 --only N" },
        { actor: "auto", title: "Contrôle qualité automatique", short: "Chaque défaut trouvé est corrigé puis revérifié.",
          details: ["Fin de phrase : la voix doit être vraiment finie (modèle Smart Turn + énergie du son).",
                    "Raccords réécoutés deux fois, seuls et dans le short.",
                    "Pas de bruit de bouche à la fin, pas de sous-titres qui se chevauchent.",
                    "Son synchrone avec l'image à 15 ms près.",
                    "On voit celui qui parle (jamais Thomas qui écoute pendant que l'invité parle)."],
          checks: ["Résultat OK / ATTENTION / ÉCHEC.", "Un short en ÉCHEC n'a ni aperçu ni rendu."],
          loop: { to: 2, label: "à corriger : retour au nettoyage, jusqu'à 10 tours" },
          files: ["travail/qa/qa_NN.md", "travail/qa/moments_NN.mp4 (les raccords à risque, ~20 s)"] },
        { actor: "auto", title: "Aperçu MP4", short: "Un brouillon à regarder dans un lecteur normal.",
          duration: "≈ 2 min 30 pour un short de 50 s", cmd: "python -m clipper preview --mp4 --clip N", files: ["travail/apercus/*_apercu.mp4"] },
        { actor: "claude", title: "Relecture par un Claude sans contexte", short: "Un regard neuf et critique, qui n'a pas suivi la conversation.",
          details: ["Il voit une planche d'images, le texte entendu, le rapport de contrôle et les passages exacts de l'épisode.",
                    "Il juge le sens, le cadrage, la lisibilité et la fidélité à l'épisode."],
          loop: { to: 2, label: "à corriger : retour au nettoyage" }, cmd: "python -m clipper review …" },
        { actor: "equipe", title: "L'équipe valide les aperçus", short: "Rien n'est rendu en version finale sans ce feu vert.",
          loop: { to: 2, label: "retouche demandée : retour au nettoyage" } },
        { actor: "auto", title: "Rendu 1080p", short: "Version finale en haute qualité, puis contrôle du fichier.",
          duration: "≈ 12 × la durée du short (2 en parallèle)", cmd: "python -m clipper render --only N", files: ["travail/renders/*.mp4"] },
        { actor: "claude", title: "1 post LinkedIn par short", short: "En anglais, dans la voix de la page AI Partners, sans hashtags.",
          details: ["Méthode « post d'un short » tirée des posts déjà publiés : accroche, contraste, invité, développement, chute, lien.",
                    "Rien qui ne soit dit dans l'extrait."],
          cmd: "python -m clipper posts …", files: ["travail/posts/clip_NN_*.md"] },
        { actor: "auto", title: "Outro avec la miniature", short: "Carte « l'épisode complet » avec la miniature YouTube, collée à la fin de chaque short.",
          details: ["Rendue une seule fois, puis ajoutée à chaque short sans écran noir.", "Format vérifié pour être lisible partout (H.264 yuv420p)."],
          duration: "≈ 2 min 40 une fois, puis ≈ 1 min par short", cmd: "python -m clipper outro …", files: ["travail/livrables/clip_NN_*_9x16.mp4"] },
        { actor: "livrable", title: "5 shorts + 5 posts", short: "Prêts à publier." }
      ]
    },

    {
      id: "episode", num: 3, title: "Épisode + teaser", group: "main",
      pitch: "Claude dérushe, la machine monte comme le monteur et ajoute un teaser en ouverture.",
      deliverable: "Épisode 1080p, teaser, chapitres, description YouTube",
      duration: "≈ 15 min pour l'aperçu, plus le rendu final",
      status: { level: "ok", text: "Validé sur E22" },
      summary: "L'épisode n'est pas rendu par le même moteur que les shorts (ce serait 9 à 10 h) : le corps est assemblé plan par plan, seul le teaser passe par le moteur d'animation.",
      improve: ["Teaser : seule la carte invité est gardée en motion design (chiffres animés et sons désactivés le 09/10)."],
      steps: [
        { actor: "claude", title: "Dérushage par Claude", short: "Il repère ce qu'il faut retirer : fausses prises, hors antenne, questions reposées.",
          details: ["Garde la dernière prise de l'intro et l'au revoir.", "Chaque coupe est calée sur des mots exacts."],
          cmd: "python -m clipper episode-plan …", files: ["travail/episode_plan.md (à relire)"] },
        { actor: "auto", title: "Raccords nettoyés", short: "Aucune hésitation ni mot coupé aux raccords de dérushage.",
          details: ["Reprise reculée au creux du son qui précède.", "« Euh » ou mot répété en tête de reprise : retiré.", "Blanc de plus de 1,2 s au raccord : raccourci.", "Jamais de coupe pendant que quelqu'un parle."],
          origin: "Arthur, 08/10/2026 : « vérifie bien plusieurs fois qu'il n'y a pas de problème de coupure »." },
        { actor: "auto", title: "Plans façon monteur", short: "Les proportions du monteur d'AI Partners, et on voit toujours celui qui parle.",
          details: ["Gros plans 76 %, plan large 14 %, écran partagé 10 %, plan moyen de 10 s (mesuré sur E20 et E21).",
                    "Une réplique de l'autre de plus de 0,4 s passe sur son gros plan ou en écran partagé.",
                    "Pas de plan de réaction sur celui qui écoute.",
                    "Logo AI Partners en haut à droite."],
          origin: "Arthur, 09/10/2026 : « il faut qu'on voie toujours celui qui parle »." },
        { actor: "claude", title: "Teaser", short: "5 à 7 extraits forts, alternés entre Thomas et l'invité.",
          details: ["Script en rôles : thèse, développement, échange, histoire, conviction, chute.",
                    "Chaque extrait est réécouté ; seuls les extraits vérifiés sont gardés, puis Claude recompose l'ordre final.",
                    "Sous-titres de la charte, carte invité, musique très légère, fin sur l'animation du logo (7 s)."],
          duration: "≈ 10 min de rendu" },
        { actor: "auto", title: "Chapitres et description YouTube", short: "Aux temps exacts du montage, avec le titre validé.",
          files: ["travail/episode/description_youtube.md"] },
        { actor: "auto", title: "Aperçu 540p", short: "L'épisode complet en version légère.", duration: "≈ 15 min",
          cmd: "python -m clipper episode-render … --proxy", files: ["travail/episode/<E>_episode_apercu.mp4"] },
        { actor: "auto", title: "Contrôle qualité de l'épisode", short: "Raccords réécoutés, celui qui parle à l'image, volumes.",
          details: ["Qui parle à l'image vérifié deux fois : tours de parole et empreinte vocale de chaque gros plan.",
                    "Volume normalisé partie par partie (teaser et corps) à -16 LUFS."],
          loop: { to: 5, label: "à corriger : nouvel aperçu" }, cmd: "python -m clipper qa --episode", files: ["travail/qa/episode_apercu.md"] },
        { actor: "claude", title: "Relecture par un Claude sans contexte", short: "Regard neuf avant de montrer l'aperçu à l'équipe.",
          loop: { to: 5, label: "à corriger : nouvel aperçu" } },
        { actor: "equipe", title: "L'équipe valide l'aperçu", short: "Aucun MP4 final sans ce feu vert.", loop: { to: 5, label: "retouche : nouvel aperçu" } },
        { actor: "auto", title: "Rendu 1080p et contrôle final", short: "Version finale, fin sur l'animation AI Partners (8 s).",
          cmd: "python -m clipper episode-render …", files: ["travail/episode/<E>_episode.mp4"] },
        { actor: "livrable", title: "Épisode 1080p", short: "Avec son teaser, ses chapitres et sa description." }
      ]
    },

    {
      id: "titre", num: 4, title: "Titre puis miniature", group: "main",
      pitch: "Claude propose 5 titres en texte, l'équipe en choisit un, puis 4 miniatures avec ce titre.",
      deliverable: "Titre YouTube + miniature 1280×720",
      duration: "≈ 5 min pour le titre, ≈ 5 min pour les miniatures",
      status: { level: "wait", text: "E22 : titre en attente de validation" },
      summary: "Le titre débloque trois autres process : c'est la validation à faire en premier.",
      improve: ["Chaque remarque de l'équipe sur un titre devient une règle du brief (rubrique « À éviter »)."],
      steps: [
        { actor: "claude", title: "Claude écrit ~12 titres", short: "Chaque titre pose la question du spectateur, l'invité en est la preuve.",
          details: ["Brief tiré des 16 titres publiés (E06 à E21), 5 formules (comment, tension, promesse, enjeu, constat).",
                    "Chaque titre cite le passage exact de l'épisode qui le justifie."],
          cmd: "python -m clipper titles …" },
        { actor: "auto", title: "Contrôles", short: "Les titres hors règles sont écartés.",
          checks: ["2 lignes de 34 caractères maximum, titre complet de 80 maximum.", "Chiffres et noms présents dans l'épisode.", "Pas de nom d'invité, pas de mot racoleur.", "Pas de copie d'un titre déjà publié ou refusé."] },
        { actor: "claude", title: "Jury : 5 titres", short: "Un deuxième Claude garde les 5 meilleurs, avec une phrase d'explication.", files: ["travail/titres/propositions.md"] },
        { actor: "equipe", title: "L'équipe choisit 1 titre", short: "La validation qui débloque le reste.", cmd: "python -m clipper titles --pick N" },
        { actor: "auto", title: "4 miniatures", short: "Thomas et l'invité souriants, qui se regardent, sur le gabarit Canva de l'équipe.",
          details: ["Une image toutes les 3 s ; sourire mesuré (modèle FER+) et regard vers l'autre.",
                    "Un Claude regarde les planches de photos et choisit (jury visuel).",
                    "Détourage des personnes, logos en cubes 3D, titre sur le bandeau bleu.",
                    "Gabarit importé une fois depuis le design Canva de l'équipe (thumbnail-template) ; à refaire si le design change."],
          duration: "≈ 5 min", cmd: "python -m clipper thumbnail …", files: ["travail/miniatures/planche.jpg"] },
        { actor: "equipe", title: "L'équipe choisit la miniature", short: "Le fichier à téléverser sur YouTube.", cmd: "python -m clipper thumbnail --pick N" },
        { actor: "livrable", title: "Titre + miniature", short: "1280×720 et version HD." }
      ]
    },

    {
      id: "carrousel", num: 5, title: "Carrousel LinkedIn", group: "main",
      pitch: "Claude propose 3 angles, l'équipe en choisit un, Claude rédige les slides dans la charte.",
      deliverable: "PDF LinkedIn + son post",
      duration: "quelques minutes",
      status: { level: "ok", text: "Style choisi sur E22 (« mix »)" },
      summary: "Le carrousel donne de la valeur à la communauté et finit sur un appel à réserver un échange avec AI Partners.",
      improve: ["URL du CTA « réserver un échange » à confirmer."],
      steps: [
        { actor: "claude", title: "Claude propose 3 angles", short: "Chacun avec ses citations, retrouvées dans l'épisode.", cmd: "python -m clipper carousel …", files: ["travail/carrousel/angles.md"] },
        { actor: "equipe", title: "L'équipe choisit 1 angle", short: "Avec une remarque si besoin.", cmd: "python -m clipper carousel --pick N" },
        { actor: "claude", title: "Slides rédigées", short: "6 à 8 slides : couverture, introduction, points clés, chiffre, citation, récapitulatif, appel à l'action.",
          details: ["En français, promesse claire en couverture (pas d'accroche choc)."] },
        { actor: "auto", title: "Contrôles", short: "Rien d'inventé, rien de trop long.",
          checks: ["Citation affichée retrouvée à 90 % mot pour mot.", "Chiffres présents dans l'épisode.", "Titre de 60 caractères maximum, texte de 35 mots maximum."] },
        { actor: "claude", title: "Post LinkedIn", short: "3 à 5 lignes qui présentent le carrousel, avec le lien de réservation.",
          details: ["Le lien est dans le post : dans un PDF LinkedIn, rien n'est cliquable."] },
        { actor: "auto", title: "Rendu PDF", short: "Charte AI Partners : couverture avec la photo de l'invité, slides bleu nuit à cartes blanches.",
          files: ["travail/carrousel/*.pdf"] },
        { actor: "claude", title: "Relecture par un Claude sans contexte", short: "Fidélité à l'épisode, lisibilité.", loop: { to: 2, label: "à corriger : retour aux slides" } },
        { actor: "equipe", title: "L'équipe valide", short: "Le PDF final part dans le dossier de livraison.", cmd: "python -m clipper carousel --final mix" },
        { actor: "livrable", title: "Carrousel PDF + post", short: "Prêts à publier sur LinkedIn." }
      ]
    },

    {
      id: "mail", num: 6, title: "Mail de Thomas", group: "main",
      pitch: "Claude écrit le mail de l'épisode à la place de Thomas, mis en page dans la charte.",
      deliverable: "Mail envoyé depuis la boîte de Thomas",
      duration: "≈ 3 min de rédaction",
      status: { level: "wip", text: "Gabarit validé ; envoi à la liste à construire" },
      summary: "Le mail part au nom de Thomas, en plus de la newsletter d'AI Partners, pour valoriser chaque épisode.",
      improve: ["Envoi à la vraie liste à construire (n8n : paquets, suivi, désinscription).", "Version HubSpot faite à la main pour E21 : option --hubspot à prévoir."],
      steps: [
        { actor: "claude", title: "Claude écrit le mail", short: "À la première personne : objet, accroche, l'invité, 4 points du programme, mot de fin.",
          details: ["Vouvoiement, faits tirés de l'épisode.", "4 textes du programme de longueur égale (150 à 170 caractères)."], cmd: "python -m clipper newsletter …" },
        { actor: "auto", title: "Contrôles", short: "Faits et chiffres retrouvés dans l'épisode.",
          checks: ["Chaque fait a sa citation retrouvée dans la transcription.", "Chiffres présents dans l'épisode.", "Jamais de tiret « — »."] },
        { actor: "auto", title: "Mise en page « Duo »", short: "En-tête AI Corner by AI Partners, miniature, 4 cartes, logos YouTube, Spotify et Ausha.",
          files: ["travail/newsletter/email.html", "travail/newsletter/apercu.png"] },
        { actor: "claude", title: "Relecture par un Claude sans contexte", short: "Fidélité et ton.", loop: { to: 0, label: "à corriger : Claude réécrit" } },
        { actor: "equipe", title: "L'équipe valide le mail", short: "", cmd: "python -m clipper newsletter --final" },
        { actor: "auto", title: "Préparé pour l'envoi", short: "Images en ligne, « Bonjour {prénom} », lien de désinscription.",
          cmd: "python -m clipper newsletter --envoi", files: ["docs/newsletters/<E>/email.html"] },
        { actor: "auto", title: "Envoi par n8n", short: "Depuis la boîte Gmail de Thomas. Testé ; l'envoi à la liste reste à construire." },
        { actor: "livrable", title: "Mail de Thomas", short: "Dans la boîte de chaque contact." }
      ]
    },

    {
      id: "livraison", num: 7, title: "Livraison", group: "end",
      pitch: "Toutes les versions finales dans un seul dossier, avec l'état de chaque livrable.",
      deliverable: "Dossier LIVRABLES/ à copier sur le Drive",
      duration: "quelques secondes",
      status: { level: "ok", text: "En production" },
      summary: "Le pipeline n'écrit jamais dans LIVRABLES/ : on relance la livraison après chaque retouche.",
      steps: [
        { actor: "auto", title: "Copie des versions finales", short: "Noms clairs, et un LISEZMOI.md qui dit ce qui est prêt ou à revoir.",
          details: ["Pour chaque livrable : contrôle qualité OK, titre et miniature validés, et plus récent que ce dont il dépend."],
          cmd: "python -m clipper livraison …", files: ["EPISODES/<marque>/<épisode>/LIVRABLES/"] },
        { actor: "equipe", title: "Copie sur le Drive", short: "L'équipe récupère le dossier." }
      ]
    }
  ]
};
