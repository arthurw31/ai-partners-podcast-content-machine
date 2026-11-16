# Carrousel de podcast : le format standard (validé le 16/11/2026)

Arthur, 16/11/2026 : « l'équipe a bien aimé cette version, donc à partir de maintenant jusqu'à nouvel ordre, quand je te
demanderai un carrousel de podcast, tu feras dans ce style et cette forme-là ». Modèle vivant : le carrousel E23 Coty
(`MARQUES/ai-corner/references/carrousel_E23/` : `contenu.json` + `planche.jpg`). Brief injecté dans Claude : `MARQUES/ai-corner/carousel.md`.

## Comment on y est arrivé (les retours qui ont défini les règles)

| Essai | Retour de l'équipe | Règle |
|---|---|---|
| Version du 12/10 (récap, accroche générale) | « très ancienne » | Refaire avec le titre validé de l'épisode et la miniature choisie |
| Sujet « comment on automatise avec Claude » | « tu n'as rien compris, il faut parler du podcast de Coty » | Le carrousel parle du CONTENU de l'épisode, jamais de la machine ; source = newsletter + transcription |
| Fond bleu clair en couverture et CTA | « on n'utilise plus le bleu clair dans la charte » | Bleu nuit partout, accents `#24317F`, blanc sur fond sombre |
| Citations en minuscule | « mets une majuscule » | Majuscule en tête de toute citation (`_cap`) |
| Slide « contexte » qui redit le titre | amélioration validée | Le chiffre en accroche (slide `stat`) |
| Texte seul | « très visuel, schématiser, logos » | Un schéma par point (`flow`, `stairs`, `hub`) |
| Rangée d'agents robots | « trop enfantin » | Aucun pictogramme d'agents sur la slide du chiffre |
| Récapitulatif des 4 points | refusé | Pas de slide récapitulatif |
| Citations en fragments | amélioration validée | Phrases entières et fortes |
| Logos Copilot | un logo exact par marche | Logos officiels uniquement (`assets/logos/`, `SOURCES.md`), pastille blanche, jamais tracés à la main |
| Bleus clairs, textes serrés | « le moins possible de bleu clair, textes aérés » | Palette bleu nuit, marges agrandies dans les cartes |

## Le format

1. **Couverture** : promesse claire (version courte du titre YouTube validé), 1 à 3 mots clés en pavé blanc, sous-titre ≤ 6 mots, photo détourée de l'invité, carte logo entreprise + ligne invité, « AI CORNER · E<n> ».
2. **Chiffre en accroche** (`stat`, « Le constat ») : très grand chiffre (« 3 000+ »), libellé, revers, enjeu. Aucun pictogramme.
3. **3 à 4 points** (`point`) : titre-action ≤ 45 car. avec un mot clé, « Idée n », carte blanche = schéma + phrase ≤ 22 mots + « À retenir » ≤ 16 mots + citation entière (8 à 28 mots) en encadré.
4. **Citation forte** (`quote`) : libellé de contexte + pictogramme.
5. **CTA** (automatique) : « Vos équipes testent l'IA. Et après ? », bouton « Réserver un échange », « Lien dans le post 👇 », miniature + titre validé.
6. **Post LinkedIn** : question ou promesse, invité + programme, enjeu, « Les points clés dans le carrousel 👇 », puis le code ajoute « 🎙️ L'épisode complet : <lien YouTube de l'épisode> » et la ligne de réservation. Pas de hashtags, jamais de tiret cadratin.

## Bonnes pratiques de fabrication

- **Matière d'abord** : lire `newsletter/contenu.json` (thème, points, chiffre, preuves), le titre validé et la miniature choisie ; ne rien ajouter qui ne soit dans la transcription.
- **Une preuve par slide** : `evidence` = passage exact de l'épisode ; citations retrouvées ≥ 90 % mot pour mot, chiffres présents dans la transcription.
- **Un schéma ne montre que ce que l'invité dit** : pas de nom, nombre ou étape non cités ; un logo de marque seulement quand le produit est le sujet de la slide.
- **Contrôles automatiques** (`check_slides`) : citations, chiffres, longueurs, et depuis le 16/11 le format (pas de récapitulatif, « À retenir » présent, schéma valide, icônes et logos existants, citation entière, libellé de la slide citation). Un ATTENTION se corrige ou se justifie.
- **Regarder** la planche, la couverture, un point avec schéma, la citation et le CTA en grand : débordements (cadre rouge), photo sur le titre, logo illisible, textes serrés.
- **Livraison** : `livraison` copie PDF + post dans `LIVRABLES/` ; validation par l'équipe = `carousel --final mix --by <prénom>` ; les anciennes versions vont dans `archives/`.
- Un retour de l'équipe change la règle ici, dans `carousel.md` et dans `check_slides` (+ test), pas seulement le carrousel en cours.
