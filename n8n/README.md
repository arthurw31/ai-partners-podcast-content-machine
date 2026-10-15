# Workflows n8n

Exports des workflows n8n du projet (instance : aipartners.app.n8n.cloud), pour ne jamais repartir de zéro.
Import : n8n -> *Workflows* -> *Import from File*, puis reconnecter les comptes (les connexions ne sont pas exportées).

| Fichier | Rôle | État |
|---|---|---|
| `newsletter_test.workflow.json` | envoie UNE fois la newsletter d'un épisode (HTML + images publiés sur GitHub Pages par `python -m clipper newsletter --envoi`) à un destinataire de test, via Gmail, avec prénom et lien de désinscription | testé et validé par Arthur le 13/10/2026 (envoi à soi-même) |

Changer d'épisode : dans le nœud « Paramètres du test », mettre `episode` à `E22`, `E23`… (le dossier `docs/newsletters/<E>/` doit
être publié : `newsletter --envoi`, puis `git push`). Test du 14/10/2026 : E23 au nouveau gabarit, validé sur PC et téléphone.

À faire pour l'envoi réel (plus tard) : brancher le compte Google de Thomas, lire la liste des contacts (Google Sheet :
prénom, e-mail, statut), envoyer par paquets avec une pause entre deux mails (limite Google Workspace ≈ 2 000 / jour),
noter « envoyé / erreur / désinscrit » dans le Sheet, et une page de désinscription (webhook n8n) à la place du mailto.
