"""
Design tokens — charte visuelle inspirée du design Figma UIMM
(https://www.figma.com/design/kB0qKLjaoTlYsuAsukfPQt/OK).
Source unique de vérité pour ui/style.py et ui/components.py.
"""

COLORS: dict[str, str] = {
    # Rouge texte-safe (boutons, valeurs stats) — 5.4:1 sur blanc, conforme WCAG AA
    "red":          "#C6303A",
    "red_hover":    "#A82833",
    # Rouge vif d'origine (Figma) — réservé aux éléments non-textuels (barres de graphique)
    "red_bright":   "#E63C46",
    "navy":         "#171A1F",   # sections sombres, texte
    "bg":           "#F2F7FA",   # fond de page
    "white":        "#FFFFFF",   # cartes
    "badge":        "#3D5F82",   # tag plein — 6.6:1 sur blanc (remplace #5B86B1, 3.8:1, non conforme)
    "badge_light":  "#B8CADE",   # tag secondaire
    "muted":        "#565F6E",   # texte secondaire — 5.9-6.4:1 (remplace #6B7280, sous le seuil sur fond gris)
    "border":       "#E2E8F0",
}

FONT_IMPORT_URL = (
    "https://fonts.googleapis.com/css2"
    "?family=Inter:wght@400;500;600;700;800&display=swap"
)
FONT_FAMILY = "'Inter', sans-serif"
