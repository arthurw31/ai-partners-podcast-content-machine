"""Newsletter « communiqué » du labo (10/11/2026) : AI Partners devient partenaire Select du Claude Partner Network (services track).

Texte : le Google Doc « Partner Anthropic - Newsletter » (fourni par l'équipe, repris tel quel). Design : même famille que « Lumière » (page
blanche, bleu nuit, frise à points, bloc de réservation), avec l'ouverture inspirée du visuel LinkedIn de l'équipe : dégradé bleu grainé, carte du
badge « Select Services Partner » à gauche, logos AI PARTNERS / ANTHROPIC, titre blanc avec une expression surlignée en orange.
Badge : recadré dans le visuel LinkedIn fourni (basse définition : à remplacer par le fichier d'origine d'Anthropic).
Placeholders à remplacer : lien du communiqué de presse, lien du bouton « Échanger avec un expert Claude ».

EXPLORATION : non branchée sur la production. Sortie : EPISODES/ai-corner/_communiques/select-partner/.
Lancer : python -m clipper.newsletter_lab.piste_select [--badge chemin_du_visuel]
"""
from __future__ import annotations

import sys
from pathlib import Path

from ..newsletter_templates import FONT, NAVY, PILL_CLOSE, esc, pill_open
from .piste_nouveau import _fonts, _render, _uri, preview

ROOT = Path(__file__).resolve().parents[2]
BLACK, INK, MUTED, RULE = "#05070F", "#141B45", "#4A5683", "#D9DEEE"
ORANGE = "#D8843C"          # surlignage du visuel de l'équipe (couleur Claude / Anthropic)
VISUEL = Path(r"C:\Users\arthu\AppData\Local\Temp\claude\4f2b225def50f385\97d4e06a-96f5-4c6b-aae2-472258e11062\images\4.webp")
PRESSE = "https://www.weareaipartners.com/"          # PLACEHOLDER : lien du communiqué de presse
EXPERT = "https://calendly.com/"                      # PLACEHOLDER : lien « Échanger avec un expert Claude »

OBJET = "AI Partners devient partenaire Select du Claude Partner Network"
CRITERES = ["des experts certifiés par l'Anthropic Partner Academy, qui utilisent activement Claude ;",
            "des déploiements clients réellement en production, au-delà des POC et des expérimentations ;",
            "au moins une référence client publique."]
CHANGE = [("Des équipes certifiées.", "12 consultants et ingénieurs AI Partners sont certifiés sur Claude et l'utilisent au quotidien, y compris Claude Code dans notre propre travail d'ingénierie."),
          ("Une expérience de la production.", "Nous avons déjà mis Claude en production chez nos clients : nous connaissons les questions d'intégration, de sécurité, d'évaluation et de gouvernance qui se posent après le pilote."),
          ("Le bon outil au bon endroit.", "Tous les usages ne nécessitent pas un agent. Nous vous aidons à identifier les cas où Claude apporte réellement de la valeur, avant d'engager les développements."),
          ("Une architecture qui dure.", "Nos systèmes sont conçus pour que les modèles puissent évoluer sans reconstruire vos agents. Partenaires de plusieurs éditeurs, nous choisissons avec vous la technologie la plus adaptée à chaque contexte.")]
OFFRES = [("AI Factory", "concevoir et mettre en production des agents Claude au cœur de vos processus métier."),
          ("AI First Organization", "définir la stratégie, la gouvernance et le cadre de sécurité de vos usages de Claude."),
          ("AI Academy", "former vos équipes, et industrialiser Claude Code dans vos équipes de développement.")]


CENTRE = False      # version « textes centrés » (retour d'Arthur, 10/11/2026) : sortie dans select-partner-centre/


def btn(label: str, href: str, bg: str, fg: str = "#FFFFFF") -> str:
    return (pill_open(bg, "0 auto" if CENTRE else "0") + f'<a href="{esc(href)}" style="display:inline-block;padding:22px 46px;font-family:{FONT};font-size:21px;'
            f'font-weight:bold;letter-spacing:.02em;color:{fg};text-decoration:none">{esc(label)}</a>' + PILL_CLOSE)


def build(visuel: Path = VISUEL, centre: bool = False) -> Path:
    global CENTRE
    CENTRE = centre
    from PIL import Image, ImageDraw
    out = ROOT / "EPISODES" / "ai-corner" / "_communiques" / ("select-partner-centre" if centre else "select-partner")
    img = out / "images"
    img.mkdir(parents=True, exist_ok=True)
    # --- badge recadré dans le visuel fourni, coins arrondis
    b = Image.open(visuel).convert("RGB").crop((134, 98, 360, 549))
    mask = Image.new("L", b.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, b.size[0] - 1, b.size[1] - 1], 12, fill=255)
    b = b.convert("RGBA")
    b.putalpha(mask)
    b.save(img / "badge.png")
    thomas = ROOT / "EPISODES" / "ai-corner" / "E23_nicolas-comestaz_coty" / "travail" / "photos_profil_thomas" / "profil_large_04.png"
    Image.open(thomas).convert("RGB").crop((180, 20, 920, 760)).resize((280, 280), Image.Resampling.LANCZOS).save(img / "thomas_portrait.jpg", quality=92)
    logo = _uri(ROOT / "MARQUES" / "ai-corner" / "assets" / "logo.png")
    # --- ouverture : le visuel LinkedIn de l'équipe, STRICTEMENT inchangé (Arthur, 10/11/2026 : « laisse le screen inchangé même s'il est en
    #     anglais ») ; simple conversion en PNG.
    Image.open(visuel).convert("RGB").save(img / "hero.png")

    # --- forme « courrier » (retour d'Arthur, 10/11/2026 : « une forme traditionnelle de texte comme dans le doc ») : titres simples,
    #     paragraphes, vraies puces ; pas de cartes, de frise ni de bloc coloré autour du texte.
    al = "center" if centre else "left"

    def puces(items):
        if centre:      # centré : plus de barre latérale, un court filet bleu nuit centré entre les éléments
            sep = f'<div style="width:44px;height:4px;background:{NAVY};margin:0 auto 18px auto;font-size:0;line-height:0">&nbsp;</div>'
            body = sep.join(f'<div style="padding:0 0 18px 0">{x}</div>' for x in items)
            return (f'<tr><td align="center" style="padding:2px 0;text-align:center;font-family:{FONT};font-size:17px;line-height:1.65;color:{INK}">{body}</td></tr>')
        """UNE barre verticale bleu nuit continue sur le côté gauche de la liste, les éléments empilés à droite (aucun point à aligner)."""
        body = "".join(f'<div style="padding:0 0 {0 if i == len(items) - 1 else 18}px 0">{x}</div>' for i, x in enumerate(items))
        return (f'<tr><td style="border-left:4px solid {NAVY};padding:2px 0 2px 22px;font-family:{FONT};font-size:17px;line-height:1.65;color:{INK}">{body}</td></tr>')
    PETITS = {"de", "du", "des", "la", "le", "les", "au", "aux", "en", "et", "ou", "qui", "que", "à", "par", "pour", "sur", "dans", "avec", "sans"}

    def capitales(t: str) -> str:
        """Majuscule seulement au début des mots importants (articles et petits mots restent en minuscules, sauf en tête de phrase)."""
        mots = t.split(" ")
        return " ".join(m if (m.isupper() and len(m) > 1) else (m[:1].upper() + m[1:] if (i == 0 or m.lower() not in PETITS) else m.lower())
                        for i, m in enumerate(mots))

    def debut(x: str, n: int = 3) -> str:
        """Début de puce homogène (Arthur, 10/11/2026) : les 3 premiers mots en GRAS, majuscule au début des mots importants seulement."""
        mots = x.split(" ")
        return f'<strong style="color:{BLACK}">{esc(capitales(" ".join(mots[:n])))}</strong> {esc(" ".join(mots[n:]))}'

    def titre(t: str, suite: str, sep: str = "") -> str:
        return f'<strong style="color:{BLACK}">{esc(capitales(t.rstrip(".:")))}</strong>{sep} {esc(suite)}'

    crit = puces([debut(x) for x in CRITERES])
    change = puces([titre(t, x, ".") for t, x in CHANGE])
    offres = puces([titre(t, x, " :") for t, x in OFFRES])
    h2 = f"margin:0;font-family:{FONT};font-size:22px;line-height:1.3;font-weight:bold;color:{BLACK};text-align:{al}"
    p = f"font-family:{FONT};font-size:17px;line-height:1.7;color:{INK};text-align:{al}"
    if centre:
        sig = (f'<tr><td align="center" style="padding:0 4px;text-align:center"><img src="images/thomas_portrait.jpg" width="84" height="84" alt="Thomas Spitz, CEO d&#39;AI Partners" '
               f'style="display:block;border:0;border-radius:42px;width:84px;height:84px;margin:0 auto 14px auto"><div style="{p}">À très bientôt,<br><strong style="color:{BLACK}">Thomas Spitz</strong><br>'
               f'<span style="color:{MUTED}">CEO, AI Partners</span></div></td></tr>')
    else:
        sig = (f'<tr><td style="padding:0 4px"><table role="presentation" cellpadding="0" cellspacing="0"><tr>'
               f'<td valign="top" width="100" style="width:100px;padding:0 18px 0 0"><img src="images/thomas_portrait.jpg" width="84" height="84" alt="Thomas Spitz, CEO d&#39;AI Partners" style="display:block;border:0;border-radius:42px;width:84px;height:84px"></td>'
               f'<td valign="middle" style="{p}">À très bientôt,<br><strong style="color:{BLACK}">Thomas Spitz</strong><br><span style="color:{MUTED}">CEO, AI Partners</span></td></tr></table></td></tr>')
    inner = f"""<tr><td style="padding:0"><a href="{esc(PRESSE)}"><img src="images/hero.png" width="640" alt="AI Partners est désormais partenaire Select du Claude Partner Network, le programme qui réunit les sociétés de services déployant Claude chez leurs clients" style="display:block;width:100%;max-width:640px;height:auto;border:0"></a></td></tr>
<tr><td style="padding:0 20px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr><td style="padding:34px 4px 14px 4px;{p}">Bonjour,</td></tr>
<tr><td style="padding:0 4px 14px 4px;{p}">Nous avons le plaisir de vous annoncer qu'AI Partners est désormais <strong style="color:{BLACK}">partenaire Select du Claude Partner Network</strong>, le programme qui réunit les sociétés de services déployant Claude, powered by Anthropic, chez leurs clients.</td></tr>
<tr><td align="{al}" style="padding:6px 4px 26px 4px;text-align:{al}">{btn("Lire le communiqué de presse", PRESSE, NAVY)}</td></tr>
<tr><td style="padding:0 4px 30px 4px;{p}">Plus qu'une annonce, nous voulions vous expliquer ce que ce statut signifie, et ce qu'il change pour les projets que nous menons ensemble.</td></tr>
<tr><td style="padding:0 4px 10px 4px"><h2 style="{h2}">Un statut qui se mérite</h2></td></tr>
<tr><td style="padding:0 4px 12px 4px;{p}">Le statut Select ne s'obtient pas sur simple adhésion. Anthropic l'attribue selon des critères précis, identiques pour tous les partenaires et réévalués régulièrement :</td></tr>
<tr><td style="padding:0 4px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{crit}</table></td></tr>
<tr><td style="padding:26px 4px 34px 4px;{p}"><strong style="color:{BLACK}">En clair :</strong> il reconnaît une pratique de Claude déjà construite sur le terrain, pas une intention.</td></tr>
<tr><td style="padding:0 4px 12px 4px"><h2 style="{h2}">Ce que cela change pour vous</h2></td></tr>
<tr><td style="padding:0 4px 30px 4px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{change}</table></td></tr>
<tr><td style="padding:14px 4px 12px 4px"><h2 style="{h2}">Comment nous pouvons vous accompagner avec Claude</h2></td></tr>
<tr><td style="padding:0 4px 30px 4px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{offres}</table></td></tr>
<tr><td style="padding:14px 4px 10px 4px"><h2 style="{h2}">Parlons de vos projets</h2></td></tr>
<tr><td style="padding:0 4px 22px 4px;{p}">Vous avez un pilote à faire passer en production, ou un cas d'usage à cadrer ? Nos experts certifiés vous proposent un échange de 30 minutes pour en discuter.</td></tr>
<tr><td align="{al}" style="padding:0 4px 38px 4px;text-align:{al}">{btn("Échanger avec un expert Claude", EXPERT, NAVY)}</td></tr>
{sig}
</table></td></tr>
<tr><td height="56" style="font-size:0;line-height:0">&nbsp;</td></tr>"""
    page = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light"><title>{esc(OBJET)}</title></head>
<body style="margin:0;padding:0;background:#FFFFFF">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">Plus qu'une annonce : ce que ce statut signifie, et ce qu'il change pour vos projets.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#FFFFFF"><tr><td align="center" style="padding:0">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="width:100%;max-width:640px;text-align:left">
{inner}
</table></td></tr></table></body></html>"""
    page = page.replace(" ?", "&nbsp;?").replace(" :", "&nbsp;:")      # typographie française : pas de ? ni de : orphelin en début de ligne
    (out / "email.html").write_text(page, encoding="utf-8")
    (out / "objet.txt").write_text(OBJET, encoding="utf-8")
    return out


if __name__ == "__main__":
    _badge = Path(sys.argv[sys.argv.index("--badge") + 1]) if "--badge" in sys.argv else VISUEL
    print(preview(build(_badge), 2500))
    print(preview(build(_badge, centre=True), 2750))
