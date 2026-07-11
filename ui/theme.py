"""
Design tokens — charte visuelle inspirée du design Figma UIMM
(https://www.figma.com/design/kB0qKLjaoTlYsuAsukfPQt/OK).
Source unique de vérité pour ui/style.py et ui/components.py.
"""

COLORS: dict[str, str] = {
    "red":          "#E63C46",   # accent principal (CTA, icônes)
    "red_dark":     "#C6303A",   # hover
    "navy":         "#171A1F",   # sections sombres, texte
    "bg":           "#F2F7FA",   # fond de page
    "white":        "#FFFFFF",   # cartes
    "badge":        "#5B86B1",   # tag plein
    "badge_light":  "#B8CADE",   # tag secondaire
    "muted":        "#6B7280",   # texte secondaire
    "border":       "#E2E8F0",
}

FONT_IMPORT_URL = (
    "https://fonts.googleapis.com/css2"
    "?family=Inter:wght@400;500;600;700;800&display=swap"
)
FONT_FAMILY = "'Inter', sans-serif"
