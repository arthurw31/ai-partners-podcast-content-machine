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


def btn(label: str, href: str, bg: str, fg: str = "#FFFFFF") -> str:
    return (pill_open(bg, "0") + f'<a href="{esc(href)}" style="display:inline-block;padding:22px 46px;font-family:{FONT};font-size:21px;'
            f'font-weight:bold;letter-spacing:.02em;color:{fg};text-decoration:none">{esc(label)}</a>' + PILL_CLOSE)


def build(visuel: Path = VISUEL) -> Path:
    from PIL import Image, ImageDraw
    out = ROOT / "EPISODES" / "ai-corner" / "_communiques" / "select-partner"
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

    # --- maquette 3D du communiqué de presse (Arthur, 10/11/2026 : « à la place du bouton, une maquette du communiqué, une couverture un peu
    #     stylée, un peu en 3D ») : couverture inventée (dégradé bleu grainé, motif montagne, logos, titre, badge), posée en perspective sur
    #     deux feuilles, ombre portée au sol. L'image entière est le lien vers le communiqué.
    mont = _uri(ROOT / "MARQUES" / "ai-corner" / "assets" / "outro_bg.png")
    cover = (f"<div class='page' style=\"background:linear-gradient(150deg,#0B1450 0%,#1B2E8C 45%,#3E58B8 80%,#8F9AD3 100%)\">"
             f"<img src='{mont}' style='position:absolute;right:-260px;bottom:-90px;width:900px;mix-blend-mode:screen;opacity:.55'>"
             f"<div style='position:absolute;left:54px;top:54px;display:flex;align-items:center;gap:14px;color:#fff;font-weight:800;font-size:23px'>"
             f"<img src='{logo}' style='height:27px'><span style='font-weight:300;font-size:32px;opacity:.85'>/</span><span>ANTHROP\\C</span></div>"
             f"<div style='position:absolute;left:54px;top:190px;color:#fff;font-weight:800;font-size:19px;letter-spacing:.22em'>COMMUNIQUÉ DE PRESSE</div>"
             f"<div style='position:absolute;left:54px;top:228px;width:54px;height:4px;background:{ORANGE}'></div>"
             f"<div style='position:absolute;left:54px;top:268px;width:470px;color:#fff;font-weight:800;font-size:50px;line-height:1.1;letter-spacing:-.015em'>"
             f"AI Partners devient <span style='background:{ORANGE};padding:0 8px;-webkit-box-decoration-break:clone;box-decoration-break:clone'>partenaire Select</span> du Claude Partner Network</div>"
             f"<img src='{_uri(img / 'badge.png')}' style='position:absolute;right:50px;bottom:84px;height:205px;border-radius:9px;box-shadow:0 10px 30px rgba(5,7,40,.45)'>"
             f"<div style='position:absolute;left:54px;bottom:54px;color:#DDE2F5;font-weight:400;font-size:17px;letter-spacing:.04em'>Novembre 2026 · weareaipartners.com</div>"
             f"</div>")
    mock = (f"<html><head><style>{_fonts()}body{{margin:0;background:#fff}}"
            f".scene{{position:relative;width:1280px;height:860px;perspective:2600px;overflow:hidden;font-family:M}}"
            f".doc{{position:absolute;left:380px;top:40px;width:560px;height:720px;transform-style:preserve-3d;transform:rotateX(14deg) rotateY(-24deg) rotateZ(5deg)}}"
            f".page{{position:absolute;inset:0;border-radius:6px;overflow:hidden}}"
            f".sheet{{position:absolute;inset:0;border-radius:6px;background:#F7F8FC;box-shadow:0 1px 0 #D7DBE8 inset}}"
            f"</style></head><body><div class='scene'>"
            f"<div style='position:absolute;left:330px;top:770px;width:700px;height:80px;border-radius:50%;background:radial-gradient(closest-side,rgba(10,16,60,.35),rgba(10,16,60,0));filter:blur(6px)'></div>"
            f"<div class='doc'>"
            f"<div class='sheet' style='transform:translateZ(-36px) translate(26px,22px)'></div>"
            f"<div class='sheet' style='transform:translateZ(-18px) translate(13px,11px)'></div>"
            f"<div style='position:absolute;inset:0;box-shadow:-30px 40px 80px rgba(8,14,60,.35);border-radius:6px'></div>"
            f"{cover}"
            f"<div style='position:absolute;inset:0;border-radius:6px;background:linear-gradient(115deg,rgba(255,255,255,.22) 0%,rgba(255,255,255,0) 38%)'></div>"
            f"</div></div></body></html>")
    _render(mock, 1280, 860, img / "communique_3d.png")

    # --- forme « courrier » (retour d'Arthur, 10/11/2026 : « une forme traditionnelle de texte comme dans le doc ») : titres simples,
    #     paragraphes, vraies puces ; pas de cartes, de frise ni de bloc coloré autour du texte.
    def puces(items):
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

    # --- visuels (Arthur, 10/11/2026 : « trop texty », idées 1, 3 et 4 retenues) : pictogrammes Lucide (ISC, assets/icons/) rendus en PNG
    ICONS = ROOT / "MARQUES" / "ai-corner" / "assets" / "icons"

    def icone(nom: str, fg: str, bg: str, px: int, radius: int = 0, pad: int = 0) -> str:
        """Pictogramme Lucide en PNG à 2x : trait `fg`, fond `bg` (tuile arrondie si radius), marge intérieure `pad`."""
        svg = (ICONS / f"lucide_{nom}.svg").read_text(encoding="utf-8").replace('stroke="currentColor"', f'stroke="{fg}"')
        svg = svg.replace('width="24"', 'width="100%"').replace('height="24"', 'height="100%"').replace('stroke-width="2"', 'stroke-width="1.8"')
        page = (f"<html><body style='margin:0;background:{bg}'><div style='width:{px}px;height:{px}px;box-sizing:border-box;padding:{pad}px;"
                f"background:{bg};border-radius:{radius}px'>{svg}</div></body></html>")
        f = img / f"ico_{nom}_{fg.strip('#')}_{bg.strip('#')}.png"
        _render(page, px, px, f)
        return f.name

    # 1. les 3 critères : trois colonnes, tuile bleu nuit + pictogramme blanc, intitulé, phrase du Doc
    CRIT_ICO = [("badge-check", "Experts certifiés"), ("server", "Déploiements en production"), ("building-2", "Référence client publique")]
    cols = []
    for (ico, lab), x in zip(CRIT_ICO, CRITERES):
        texte = x[0].upper() + x[1:].rstrip(" ;.") + "."
        cols.append(f'<td valign="top" width="33%" style="width:33%;padding:0 8px">'
                    f'<img src="images/{icone(ico, "#FFFFFF", NAVY, 128, 30, 30)}" width="64" height="64" alt="" style="display:block;border:0;width:64px;height:64px">'
                    f'<div style="padding:14px 0 6px 0;font-family:{FONT};font-size:17px;line-height:1.3;font-weight:bold;color:{BLACK}">{esc(lab)}</div>'
                    f'<div style="font-family:{FONT};font-size:15px;line-height:1.55;color:{INK}">{esc(texte)}</div></td>')
    crit = f'<tr>{"".join(cols)}</tr>'

    # 4. « Ce que cela change » : un pictogramme bleu nuit devant chaque titre, dans la liste à barre latérale
    CHANGE_ICO = ["users", "rocket", "target", "layers"]
    change = puces([f'<img src="images/{icone(i, NAVY, "#FFFFFF", 56, 0, 2)}" width="28" height="28" alt="" style="display:inline-block;vertical-align:-7px;border:0;width:28px;height:28px;margin-right:8px">'
                    + titre(t, x, ".") for i, (t, x) in zip(CHANGE_ICO, CHANGE)])

    # 3. les offres : trois tuiles bleu nuit, pictogramme blanc, nom, phrase du Doc
    OFFRE_ICO = ["factory", "compass", "graduation-cap"]
    tiles = []
    for ico, (t, x) in zip(OFFRE_ICO, OFFRES):
        tiles.append(f'<td valign="top" width="32%" bgcolor="{NAVY}" style="width:32%;background-color:{NAVY};border-radius:16px;padding:22px 18px 24px 18px">'
                     f'<img src="images/{icone(ico, "#FFFFFF", NAVY, 112, 0, 4)}" width="56" height="56" alt="" style="display:block;border:0;width:56px;height:56px">'
                     f'<div style="padding:16px 0 8px 0;font-family:{FONT};font-size:18px;line-height:1.25;font-weight:bold;color:#FFFFFF">{esc(t)}</div>'
                     f'<div style="font-family:{FONT};font-size:15px;line-height:1.55;color:#D3DAF2">{esc(x[0].upper() + x[1:])}</div></td>')
    gap = '<td width="2%" style="width:2%;font-size:0;line-height:0">&nbsp;</td>'
    offres = f"<tr>{gap.join(tiles)}</tr>"
    h2 = f"margin:0;font-family:{FONT};font-size:22px;line-height:1.3;font-weight:bold;color:{BLACK}"
    p = f"font-family:{FONT};font-size:17px;line-height:1.7;color:{INK}"
    inner = f"""<tr><td style="padding:0"><a href="{esc(PRESSE)}"><img src="images/hero.png" width="640" alt="AI Partners est désormais partenaire Select du Claude Partner Network, le programme qui réunit les sociétés de services déployant Claude chez leurs clients" style="display:block;width:100%;max-width:640px;height:auto;border:0"></a></td></tr>
<tr><td style="padding:0 20px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr><td style="padding:34px 4px 14px 4px;{p}">Bonjour,</td></tr>
<tr><td style="padding:0 4px 14px 4px;{p}">Nous avons le plaisir de vous annoncer qu'AI Partners est désormais <strong style="color:{BLACK}">partenaire Select du Claude Partner Network</strong>, le programme qui réunit les sociétés de services déployant Claude, powered by Anthropic, chez leurs clients.</td></tr>
<tr><td style="padding:4px 0 0 0"><a href="{esc(PRESSE)}"><img src="images/communique_3d.png" width="592" alt="Lire le communiqué de presse : AI Partners devient partenaire Select du Claude Partner Network" style="display:block;width:100%;max-width:592px;height:auto;border:0"></a></td></tr>
<tr><td align="center" style="padding:0 4px 30px 4px;font-family:{FONT};font-size:19px;font-weight:bold"><a href="{esc(PRESSE)}" style="color:{NAVY};text-decoration:underline;text-underline-offset:4px">Lire le communiqué de presse &rarr;</a></td></tr>
<tr><td style="padding:0 4px 30px 4px;{p}">Plus qu'une annonce, nous voulions vous expliquer ce que ce statut signifie, et ce qu'il change pour les projets que nous menons ensemble.</td></tr>
<tr><td style="padding:0 4px 10px 4px"><h2 style="{h2}">Un statut qui se mérite</h2></td></tr>
<tr><td style="padding:0 4px 12px 4px;{p}">Le statut Select ne s'obtient pas sur simple adhésion. Anthropic l'attribue selon des critères précis, identiques pour tous les partenaires et réévalués régulièrement :</td></tr>
<tr><td style="padding:10px 0 0 0"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{crit}</table></td></tr>
<tr><td style="padding:26px 4px 34px 4px;{p}"><strong style="color:{BLACK}">En clair :</strong> il reconnaît une pratique de Claude déjà construite sur le terrain, pas une intention.</td></tr>
<tr><td style="padding:0 4px 12px 4px"><h2 style="{h2}">Ce que cela change pour vous</h2></td></tr>
<tr><td style="padding:0 4px 30px 4px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{change}</table></td></tr>
<tr><td style="padding:14px 4px 12px 4px"><h2 style="{h2}">Comment nous pouvons vous accompagner avec Claude</h2></td></tr>
<tr><td style="padding:4px 4px 34px 4px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:separate">{offres}</table></td></tr>
<tr><td style="padding:14px 4px 10px 4px"><h2 style="{h2}">Parlons de vos projets</h2></td></tr>
<tr><td style="padding:0 4px 22px 4px;{p}">Vous avez un pilote à faire passer en production, ou un cas d'usage à cadrer ? Nos experts certifiés vous proposent un échange de 30 minutes pour en discuter.</td></tr>
<tr><td style="padding:0 4px 38px 4px">{btn("Échanger avec un expert Claude", EXPERT, NAVY)}</td></tr>
<tr><td style="padding:0 4px"><table role="presentation" cellpadding="0" cellspacing="0"><tr>
<td valign="top" width="100" style="width:100px;padding:0 18px 0 0"><img src="images/thomas_portrait.jpg" width="84" height="84" alt="Thomas Spitz, CEO d'AI Partners" style="display:block;border:0;border-radius:42px;width:84px;height:84px"></td>
<td valign="middle" style="{p}">À très bientôt,<br><strong style="color:{BLACK}">Thomas Spitz</strong><br><span style="color:{MUTED}">CEO, AI Partners</span></td></tr></table></td></tr>
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
    print(preview(build(Path(sys.argv[sys.argv.index("--badge") + 1]) if "--badge" in sys.argv else VISUEL), 2850))
