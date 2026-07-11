"""CSS global — reskin des composants Streamlit natifs + classes réutilisables."""
import streamlit as st
from ui.theme import COLORS, FONT_IMPORT_URL, FONT_FAMILY


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        @import url('{FONT_IMPORT_URL}');

        html, body, [class*="css"] {{
            font-family: {FONT_FAMILY};
        }}
        h1, h2, h3, h4 {{
            font-weight: 800;
            letter-spacing: -0.02em;
            color: {COLORS['navy']};
        }}

        /* --- eyebrow "/ Label /" --- */
        .uimm-eyebrow {{
            font-size: 0.85rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: {COLORS['muted']};
            border-bottom: 1px solid {COLORS['border']};
            padding-bottom: 0.6rem;
            margin-bottom: 1rem;
        }}

        /* --- badges / tags --- */
        .uimm-badge {{
            display: inline-block;
            background: {COLORS['badge']};
            color: #fff;
            font-size: 0.72rem;
            font-weight: 600;
            padding: 0.25rem 0.65rem;
            border-radius: 999px;
            margin-right: 0.4rem;
            margin-bottom: 0.4rem;
        }}
        .uimm-badge--light {{
            background: {COLORS['badge_light']};
            color: {COLORS['navy']};
        }}

        /* --- cards --- */
        .uimm-card {{
            background: {COLORS['white']};
            border: 1px solid {COLORS['border']};
            border-radius: 1rem;
            padding: 1.25rem 1.4rem;
            height: 100%;
            box-shadow: 0 1px 2px rgba(23,26,31,0.04);
        }}
        .uimm-card h4 {{ margin: 0.5rem 0 0.35rem 0; font-size: 1.05rem; }}
        .uimm-card__muted {{ color: {COLORS['muted']}; font-size: 0.9rem; }}

        /* --- dark section (hero / header fiche) --- */
        .uimm-section-dark {{
            background: {COLORS['navy']};
            color: #fff;
            border-radius: 1.25rem;
            padding: 1.75rem 2rem;
            margin-bottom: 1.5rem;
        }}
        .uimm-section-dark h2, .uimm-section-dark p {{ color: #fff; }}
        .uimm-section-dark .uimm-eyebrow {{ color: #A8B3C2; border-color: #333945; }}

        /* --- stat block --- */
        .uimm-stat {{
            background: {COLORS['white']};
            border: 1px solid {COLORS['border']};
            border-radius: 1rem;
            padding: 1rem 1.2rem;
            text-align: left;
        }}
        .uimm-stat__value {{
            font-size: 1.8rem;
            font-weight: 800;
            color: {COLORS['red']};
            line-height: 1.1;
        }}
        .uimm-stat__label {{
            font-size: 0.85rem;
            color: {COLORS['muted']};
            margin-top: 0.15rem;
        }}

        /* --- boutons Streamlit natifs --- */
        .stButton > button, .stLinkButton > a {{
            border-radius: 999px !important;
            font-weight: 700 !important;
            border: none !important;
        }}
        .stButton > button[kind="primary"], .stLinkButton > a[kind="primary"] {{
            background: {COLORS['red']} !important;
            color: #fff !important;
        }}
        .stButton > button[kind="primary"]:hover {{
            background: {COLORS['red_dark']} !important;
        }}
        .stButton > button[kind="secondary"] {{
            background: transparent !important;
            color: {COLORS['navy']} !important;
            border: 1.5px solid {COLORS['navy']} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
