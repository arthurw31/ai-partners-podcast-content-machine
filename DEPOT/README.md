# Dépôt

Déposez ici tout ce que vous donnez à Claude (épisodes, clips de référence, logos, posts publiés…).
Claude les range ensuite au bon endroit :

- rushs (3 caméras + audio) → `EPISODES/<marque>/<épisode>/rushs/rushes/<E>/` + `episodes/<E>_<invité>_<entreprise>.wav`
- épisode de podcast déjà monté → `EPISODES/<marque>/<épisode>/rushs/`
- clips de référence (montages existants) → `MARQUES/<marque>/references/`
- logos, polices, musiques de la marque → `MARQUES/<marque>/assets/` (logos d'invités : `assets/guests/`)
- posts LinkedIn déjà publiés → `MARQUES/<marque>/posts.md`

**Rushs d'un tournage** : déposez ici les 3 vidéos MP4 (gros plan invité, plan large, gros plan animateur) et
l'audio WAV du micro, tels quels. Claude les range avec `python -m clipper rushes` : il reconnaît chaque caméra,
synchronise le micro et renomme les fichiers d'après l'invité (`EPISODES/<marque>/<épisode>/rushs/rushes/<E>/`).

Rushs restés sur Dropbox : envoyez le lien à Claude plutôt que de les télécharger dans le navigateur, qui coupe les
gros fichiers en cours de route (`python -m clipper fetch "<lien>"` : reprise automatique, taille vérifiée).

Le contenu de ce dossier n'est pas versionné.
