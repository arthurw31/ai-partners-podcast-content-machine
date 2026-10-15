# EPISODES — un dossier par épisode

```
EPISODES/<marque>/<épisode>/          ex. EPISODES/ai-corner/E23_nicolas-comestaz_coty/
├── LIVRABLES/   ← à copier sur le Drive (rempli par `python -m clipper livraison`)
├── rushs/       ← sources : <épisode>.mp4 (plan large ou master), <épisode>.wav, <épisode>.multicam.json, cameras/
├── travail/     ← fichiers du pipeline (transcription, clips, rendus, contrôles qualité, aperçus) : ne pas modifier à la main
└── archives/    ← sauvegardes et anciennes versions (supprimables pour gagner de la place)
```

Un nouvel épisode est créé par `python -m clipper rushes …` à partir des fichiers déposés dans `DEPOT/`.
Les épisodes ne sont pas versionnés (fichiers lourds) : seul ce README l'est.
