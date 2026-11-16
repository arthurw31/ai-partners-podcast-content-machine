# Carrousels LinkedIn — brief AI Corner (AI Partners)

Demande d'Arthur (12/10/2026) : « créer des carrousels LinkedIn à partir des podcasts, pour donner de la valeur à la
communauté qui nous suit sur LinkedIn, et sur la dernière slide un call to action pour inciter les gens à bosser avec nous ».
Ce fichier est injecté tel quel dans le prompt de Claude (`clipper/carousel.py`) : le compléter à chaque retour de l'équipe.

## Objectif

Le lecteur doit repartir avec quelque chose d'UTILE pour son entreprise, même s'il ne regarde jamais l'épisode. Le
carrousel n'est pas une bande-annonce : c'est le meilleur de l'épisode, rendu actionnable. La dernière slide propose de
travailler avec AI Partners (réserver un échange) : elle est crédible parce que les slides précédentes ont prouvé
qu'on sait de quoi on parle.

## Public

Dirigeants, directeurs data / IA / transformation, managers de grandes entreprises et d'ETI françaises qui suivent la
page AI Partners. Ils veulent savoir ce qui marche VRAIMENT dans les entreprises (pas de théorie, pas de buzz).

## Règles d'écriture

- En français, voix de la page AI Partners : sobre, concrète, experte, jamais racoleuse. Pas de « 🚀 », pas de
  « Révolution », pas de « Vous n'allez pas y croire ». Vouvoiement si on s'adresse au lecteur.
- UNE idée par slide. Titre de slide ≤ 60 caractères. Texte ≤ 35 mots. Si ça ne tient pas, couper l'idée en deux slides.
- Chaque idée vient de l'épisode : on cite le passage (horodatage + citation EXACTE) qui la prouve. Aucun chiffre, nom
  d'outil ou fait qui ne soit pas dans la transcription.
- L'invité est la preuve, pas le sujet : « Chez Coty, … » ; on le présente une fois (Prénom Nom, rôle, entreprise).
- Les citations de l'invité sont reprises mot pour mot (on peut couper avec « […] », jamais reformuler entre guillemets).
  On retire les tics oraux (« euh », « en fait », « voilà ») d'une citation seulement en coupant avec « […] ».
- Pas de nom de l'animateur dans les slides de contenu (Thomas Spitz n'apparaît que si sa question est l'idée).

## FORMAT STANDARD (validé par l'équipe le 16/11/2026, « jusqu'à nouvel ordre » : tout carrousel de podcast suit ce modèle)

Référence vivante : le carrousel E23 Coty (`references/carrousel_E23/`). Règles détaillées : `docs/CARROUSEL_STANDARD.md`.

**Le carrousel parle du CONTENU de l'épisode, jamais de la machine** (pas de « comment on a monté ce podcast avec Claude »).
Source : le contenu validé de la newsletter de l'épisode (thème, points du programme, chiffre) + la transcription pour les preuves.

Structure (format 1080 × 1350, 6 à 8 slides + la slide CTA ajoutée par le framework) :
1. **Couverture** : la promesse claire (≤ 8 mots, version courte du titre YouTube validé), 1 à 3 mots clés en évidence, sous-titre ≤ 6 mots
   (« Ce que Coty a mis en place »), photo détourée de l'invité, carte logo de l'entreprise invitée + ligne invité, « AI CORNER · E<n> ».
2. **Le chiffre en accroche** (slide `stat`, titre « Le constat ») : le chiffre marquant en très grand (« 3 000+ »), libellé court, 1 phrase
   sur son revers, puis l'enjeu de l'invité. AUCUN pictogramme ici (les rangées de robots / d'agents ont été refusées : « trop enfantin »).
   Sans chiffre marquant : une slide `intro`.
3. **3 à 4 slides « point »** (les points du programme de la newsletter), chacune = titre-action (≤ 45 car., ce que le lecteur doit faire ou
   décider) + « Idée n » + carte blanche contenant un **schéma** (flow, stairs ou hub) + 1 phrase (≤ 22 mots) + **« À retenir »** (≤ 16 mots,
   la leçon, tirée de ce que dit l'invité) + une **citation entière et forte** de l'invité (8 à 28 mots, mot pour mot, `[…]` pour couper).
4. **Une slide citation** (l'idée la plus marquante de l'invité) avec un libellé de contexte (« Le rôle du Head of AI ») et un pictogramme.
5. **CTA** (framework) : « Vos équipes testent l'IA. Et après ? », bouton « Réserver un échange », « Lien dans le post 👇 », miniature
   de l'épisode + son titre validé (`miniatures/miniature_finale.jpg`, `titres/titre_valide.json`).
PAS de slide récapitulatif (refusée par l'équipe, 16/11/2026).

Schémas (un par point, `visual`) : ils montrent QUE ce que l'épisode dit. `flow` = 3 à 5 étapes reliées (un parcours), `stairs` = 3 à 4
marches de plus en plus hautes (une gamme, un écosystème), `hub` = un noyau et ses relais. Pictogrammes : Lucide (`assets/icons/`).
Logos de marque : uniquement les fichiers officiels déposés dans `assets/logos/` (sources dans `SOURCES.md`), en pastille blanche, et
seulement quand le produit est le sujet de la slide (pas de logo Copilot sur un chiffre dont l'épisode ne dit pas qu'il concerne Copilot).

Charte visuelle (style `mix`) : fond bleu nuit partout (couverture et CTA comme les autres slides, plus de bleu clair `#258AF3`), accents
`#24317F`, blanc sur fond sombre, aucun décor ni filet ni filigrane, textes aérés dans les cadres, Metropolis. Majuscule en tête de toute citation.

## Angles possibles (Claude en propose 3, l'équipe en choisit un)

- `lecons` : « N leçons de <entreprise> pour … » — ce qu'on peut appliquer demain.
- `methode` : « Comment <entreprise> a … : la méthode en N étapes ».
- `idees_recues` : « N idées reçues sur … que <invité> démonte ».
- `cas` : avant / ce qui a été fait / résultats (comme le carrousel Bouygues de l'équipe).
- `erreurs` : « Les N erreurs à éviter quand … ».
- `chiffres` : l'épisode raconté par ses chiffres (seulement si l'épisode en donne au moins 4).

## Post LinkedIn qui accompagne le carrousel

Il présente VITE le carrousel (Arthur, 12/10/2026 : « le texte LinkedIn qui présente vite fait le carrousel et qui donne
le lien ») : 3 à 5 lignes courtes — l'accroche (la promesse de la couverture, reformulée), l'invité nommé (Prénom Nom,
rôle, entreprise), l'enjeu de l'invité, « Les points clés dans le carrousel 👇 ». Pas de hashtags. Ajoutés AUTOMATIQUEMENT à la fin : « 🎙️ L'épisode
complet : <lien YouTube de l'épisode> » (jamais la playlist) puis « 📅 Réserver un échange avec nous : <lien> » (`carousel.cta`).
Emojis autorisés : 👇 🎙️ 📅 seulement.

## À éviter

(à compléter avec les retours de l'équipe)

## Ponctuation

Jamais de tiret cadratin « — » ni demi-cadratin « – » (Arthur, 14/10/2026 : « ça fait bizarre »). Une virgule, deux-points, des parenthèses ou deux phrases.
