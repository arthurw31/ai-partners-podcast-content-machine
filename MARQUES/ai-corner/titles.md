# Titres des épisodes AI Corner

Brief injecté tel quel dans le prompt des titres (`clipper/titles.py`), comme `posts.md` pour les posts. Un SEUL titre
par épisode, validé par l'équipe marketing parmi 5 propositions ; le même sert pour YouTube et pour la vignette.
Relevé sur les 16 épisodes publiés (E06 à E21), captures d'Arthur du 09/10/2026.

## Format

- **YouTube** : `AI Corner E<n> | <titre>`. Le nom de l'invité n'y figure plus depuis E16 (E06 à E15 l'ajoutaient à la fin).
- **Vignette** : le MÊME titre coupé en 2 lignes, sans le préfixe, 34 caractères maximum par ligne (3 lignes publiées
  dépassent : 37, 37 et 39). Une des 2 lignes est sur le bandeau bleu : le bandeau porte le SUJET (« GEO en 2026 », « les métiers
  créatifs ? », « de l'IA en entreprise ? »), l'autre ligne le cadrage (« Comment favoriser l'adoption »). Bandeau sur
  la 2e ligne dans 12 cas sur 16.
- **Ponctuation** : 6 titres sur 16 sont des questions (« ? »), 4 finissent par « ! », 6 n'ont pas de ponctuation
  finale. Jamais de deux-points ni d'emoji dans la vignette.
- Le logo de l'invité est déjà sur la vignette : son nom d'entreprise n'a pas besoin d'être dans le titre, sauf s'il porte
  le sujet. 4 vignettes sur 16 la citent (MAIF, Groupe Schmidt, Club Med, Brut) ; les 12 autres ne la montrent que par
  son logo.

## Ce que font les titres publiés

1. **Ils posent LA question du spectateur** (un professionnel qui déploie l'IA dans son entreprise), pas un fait sur
   l'invité : « Comment favoriser l'adoption de l'IA en entreprise ? », « Combien vous coûte vraiment votre IA ? ».
   L'invité et son entreprise sont la preuve, pas le sujet.
2. **Le sujet est un mot du métier** : IA, adoption, transformation, stratégie, GEO, agents, entreprise. 13 titres sur
   16 contiennent « IA » (ou « AI ») ; les 3 autres portent le sujet lui-même (GEO, Digital Twins, futur du travail).
3. **Cinq formules reviennent**, à varier d'un épisode à l'autre :
   - `comment` : « Comment … ? » / « Voici comment … ! » (E20, E13, E11, E09) ;
   - `tension` : question qui met une idée reçue à l'épreuve ou parle au spectateur : « … vraiment … ? », « Et si … ? »,
     « Quel est l'impact … ? », « Combien vous coûte … ? » (E21, E14, E08, E07) ;
   - `promesse` : infinitif et bénéfice concret : « Maîtriser le GEO pour apparaître dans les réponses IA »,
     « Construire sa stratégie GEO en 2026 ! » (E19, E18) ;
   - `enjeu` : opposition, chiffre, coulisses ou trajectoire : « Europe Vs États-Unis la guerre économique de l'IA »,
     « Les coulisses de la transformation IA du Groupe Schmidt », « De Smart Follower à Leader, la stratégie AI First de
     Club Med », « Deux décennies d'IA pour comprendre l'accélération actuelle » (E10, E17, E16, E15) ;
   - `constat` : affirmation nette : « Les "Digital Twins", la nouvelle arme des équipes marketing ! », « Le futur du
     travail est déjà là ! » (E12, E06).
4. **Ton sobre et professionnel** : aucun superlatif, aucun « incroyable / choquant / secret », aucune promesse que
   l'épisode ne tient pas. Une phrase, lisible en 2 secondes.
5. **Longueur** : titre de 33 à 62 caractères (49 à 78 avec le préfixe `AI Corner E<n> | `). Une seule phrase, lisible
   en 2 secondes.

## Titres publiés (référence : s'en inspirer, ne jamais recopier)

- E21 | Combien vous coûte vraiment votre IA ? | Combien vous coûte / [vraiment votre IA ?]
- E20 | Comment la MAIF place l'humain au cœur de sa transformation IA | [Comment la MAIF place l'humain] / au cœur de sa transformation IA
- E19 | Maîtriser le GEO pour apparaître dans les réponses IA | [Maîtriser le GEO pour] / apparaître dans les réponses IA
- E18 | Construire sa stratégie GEO en 2026 ! | Construire sa stratégie / [GEO en 2026]
- E17 | Les coulisses de la transformation IA du Groupe Schmidt | Les coulisses de la transformation IA / [du Groupe Schmidt]
- E16 | De Smart Follower à Leader, la stratégie AI First de Club Med | De Smart Follower à Leader, / [la stratégie AI First de Club Med]
- E15 | Deux décennies d'IA pour comprendre l'accélération actuelle | [Deux décennies d'IA] / pour comprendre l'accélération actuelle
- E14 | L'IA menace-t-elle vraiment les métiers créatifs ? | L'IA menace-t-elle vraiment / [les métiers créatifs ?]
- E13 | Comment la France veut-elle accélérer l'adoption de l'IA ? | Comment la France veut-elle / [accélérer l'adoption de l'IA ?]
- E12 | Les "Digital Twins", la nouvelle arme des équipes marketing ! | Les "Digital Twins", la nouvelle / [arme des équipes marketing]
- E11 | Comment favoriser l'adoption de l'IA en entreprise ? | Comment favoriser l'adoption / [de l'IA en entreprise ?]
- E10 | Europe Vs États-Unis la guerre économique de l'IA | Europe Vs États-Unis / [la guerre économique de l'IA]
- E09 | Voici comment Brut transforme le journalisme avec l'IA ! | Voici comment Brut transforme / [le journalisme avec l'IA !]
- E08 | Et si le chatbot n'était pas la bonne interface pour les IA ? | Et si le chatbot n'était pas / [la bonne interface pour les IA ?]
- E07 | Quel est l'impact de l'IA sur la recherche en ligne ? | Quel est l'impact de l'IA / [sur la recherche en ligne ?]
- E06 | Le futur du travail est déjà là ! | [L'automatisation de l'automatisation,] / le futur du travail est déjà là !

## À éviter

Titres générés avant ce brief (E23, Coty), jugés « pas ouf » par l'équipe le 09/10/2026 :

- `IA en entreprise chez Coty : 3000 agents, Microsoft Copilot et la vraie transformation | AI Corner` : liste de mots-clés
  avec deux-points, pas de préfixe `AI Corner E23 |`, trois sujets à la fois.
- `Chez Coty il y a / 3000 agents IA actifs` : un fait sur l'entreprise, pas une question du spectateur.
- `Pourquoi Coty a / 10 fois le même agent ?` : anecdote interne, tournure bancale.
- `Le vrai métier du / Head of AI selon Coty` : jargon, « selon X » qui ne dit rien.
- `De 1000 licences / à 3000 agents chez Coty` : chiffres de l'entreprise sans enjeu pour le spectateur.

2e série (propositions du 09/10/2026), jugée « pas fou » par Arthur le 12/10/2026 — justes mais PLATES :

- `Passer de l'expérimentation / [à l'impact avec l'IA]` : formule de consultant, abstraite, déjà lue partout.
- `Faut-il laisser chacun / [créer ses propres agents IA ?]` : la bonne question, mais tournure molle (« faut-il », « chacun »).
- `Le Head of AI, architecte / [ou traducteur ?]` : débat d'initiés, le spectateur ne sait pas pourquoi c'est important pour lui.
- `La transformation IA devient / [avant tout humaine]` : constat attendu, aucune surprise.
- `Comment éviter les pièges / [du marché de l'IA ?]` : « pièges » vague, l'image forte de l'épisode (« un marché de vendeurs ») perdue.

Ce qui manquait : du CONCRET qui accroche (un chiffre frappant, une image de l'invité, un mot qu'on retient : « 3 000
agents », « marché de vendeurs », « 10 agents qui font la même chose ») mis au service d'une question du spectateur, et
une TENSION (un risque, une surprise, une idée reçue renversée), comme « Combien vous coûte vraiment votre IA ? ».

Règles qui en découlent : pas de fait interne présenté comme un titre, pas de jargon seul, pas de liste séparée par des
virgules, pas de « selon <entreprise> », pas de nom d'invité, un seul sujet par titre.

## Ponctuation

Jamais de tiret cadratin « — » ni demi-cadratin « – » (Arthur, 14/10/2026 : « ça fait bizarre »). Une virgule, deux-points, des parenthèses ou deux phrases.
