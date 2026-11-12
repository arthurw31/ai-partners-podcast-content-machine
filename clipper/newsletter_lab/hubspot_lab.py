"""Version HubSpot d'un mail du labo (12/11/2026) : mêmes règles que `newsletter.hubspot_module` de la production.

- images copiées dans docs/newsletters/<E>/<piste>/ (publiées par GitHub Pages au push) et liens réécrits en ABSOLU ;
- `email_a_envoyer.html` = la page complète en liens absolus ;
- `email_hubspot_module.html` = seulement le contenu (HubSpot refuse html / head / body / style dans un module « Modifier HTML »), sans texte
  d'aperçu caché ; le pied de page de désinscription est celui, standard, de HubSpot.
Ne jamais supprimer un dossier docs/newsletters/<E>/ d'un mail envoyé.

python -m clipper.newsletter_lab.hubspot_lab <dossier_du_mail> <E23> <piste>
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGES = "https://arthurw31.github.io/ai-partners-podcast-content-machine"


def publish(mail_dir: Path, episode: str, piste: str) -> tuple[Path, Path]:
    html = (mail_dir / "email.html").read_text(encoding="utf-8")
    used = sorted(set(re.findall(r'src="images/([^"]+)"', html)))
    pub = ROOT / "docs" / "newsletters" / episode / piste
    (pub / "images").mkdir(parents=True, exist_ok=True)
    for n in used:
        shutil.copy2(mail_dir / "images" / n, pub / "images" / n)
    base = f"{PAGES}/newsletters/{episode}/{piste}/images/"
    full = html.replace('src="images/', f'src="{base}')
    (mail_dir / "email_a_envoyer.html").write_text(full, encoding="utf-8")
    (pub / "email.html").write_text(full, encoding="utf-8")
    body = re.search(r"<body[^>]*>(.*)</body>", full, re.S).group(1)
    body = re.sub(r'<div style="display:none;max-height:0;overflow:hidden;opacity:0">.*?</div>', "", body, flags=re.S).strip()
    assert not re.search(r"<(html|head|body|style)\b", body), "balise refusée par HubSpot"
    module = mail_dir / "email_hubspot_module.html"
    module.write_text(body, encoding="utf-8")
    return module, pub


if __name__ == "__main__":
    m, pub = publish(Path(sys.argv[1]), sys.argv[2], sys.argv[3])
    print(m)
    print(pub)
