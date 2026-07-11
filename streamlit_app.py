"""Point d'entrée Streamlit — VeilleIA. UI uniquement, aucune logique métier."""
from dotenv import load_dotenv
load_dotenv()

import logging

import plotly.graph_objects as go
import streamlit as st

from services.fiche_territoire import rechercher_parlementaire
from services.api_dole import rechercher_textes, CATEGORY_LABEL
from ui.style import inject_css
from ui.components import eyebrow, stat_card, texte_card, fiche_header, result_count
from ui.theme import COLORS
from utils.auth import require_login
from utils.config import AUTH_ENABLED

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("veilleia")

st.set_page_config(page_title="VeilleIA", page_icon="🏭", layout="wide")
inject_css()
require_login()

st.sidebar.markdown(
    '<div style="font-weight:800; font-size:1.2rem; margin-bottom:1rem;">🏭 VeilleIA</div>',
    unsafe_allow_html=True,
)
if not AUTH_ENABLED:
    st.sidebar.warning("Authentification désactivée — environnement de test.", icon="🔓")

PAGES = ["Accueil", "Fiche territoire", "Textes législatifs"]
PAGE_ICONS = {"Accueil": "🏠", "Fiche territoire": "📍", "Textes législatifs": "📜"}

if "pending_nav" in st.session_state:
    st.session_state["nav_page"] = st.session_state.pop("pending_nav")
st.session_state.setdefault("nav_page", "Accueil")
page = st.sidebar.radio(
    "Navigation", PAGES, key="nav_page",
    format_func=lambda p: f"{PAGE_ICONS[p]} {p}",
    label_visibility="collapsed",
)


def page_accueil() -> None:
    st.markdown(
        '<div class="uimm-section-dark">'
        '<div class="uimm-eyebrow">/ VeilleIA /</div>'
        "<h2>Veille territoriale et industrielle</h2>"
        "<p>Croisez le tissu économique local avec l'activité législative des élus — "
        "données publiques françaises, sans IA.</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    cols = st.columns(3)
    shortcuts = [
        ("Fiche territoire", "Élus, établissements industriels et effectifs par département.", "Fiche territoire"),
        ("Textes législatifs", "Lois, ordonnances et propositions filtrables par mots-clés.", "Textes législatifs"),
        ("Données publiques", "RNE, SIRENE (INSEE) et DOLE — actualisées toutes les 24 h.", None),
    ]
    for col, (titre, desc, target) in zip(cols, shortcuts):
        with col:
            icone = PAGE_ICONS.get(target, "📊")
            st.markdown(
                f'<div class="uimm-card"><h4>{icone} {titre}</h4>'
                f'<p class="uimm-card__muted">{desc}</p></div>',
                unsafe_allow_html=True,
            )
            if target:
                if st.button("Ouvrir →", key=f"home-goto-{target}", use_container_width=True):
                    st.session_state["pending_nav"] = target
                    st.rerun()


def _reset_fiche_territoire() -> None:
    st.session_state["ft_query"] = ""
    st.session_state["ft_chambre"] = "Les deux"


def page_fiche_territoire() -> None:
    eyebrow("Recherche")
    c_query, c_chambre, c_reset = st.columns([3, 1, 0.7])
    with c_query:
        query = st.text_input(
            "Nom, département ou code département",
            placeholder="ex : Dupont, 69, Rhône", key="ft_query",
        )
    with c_chambre:
        chambre = st.selectbox("Chambre", ["Les deux", "Sénat", "Assemblée nationale"], key="ft_chambre")
    with c_reset:
        st.markdown('<div style="height:1.85rem"></div>', unsafe_allow_html=True)
        st.button("Réinitialiser", key="ft_reset", on_click=_reset_fiche_territoire, use_container_width=True)
    if not query:
        return

    try:
        with st.spinner("Recherche en cours…"):
            fiches = rechercher_parlementaire(query)
    except Exception:
        logger.exception("Échec rechercher_parlementaire(query=%r)", query)
        st.error("Service RNE/SIRENE indisponible, réessayez plus tard.")
        return

    if chambre != "Les deux":
        fiches = [f for f in fiches if f["parlementaire"]["chambre"] == chambre]

    if not fiches:
        st.warning("Aucun résultat pour cette recherche.")
        return

    result_count(len(fiches), "résultat")
    for i, fiche in enumerate(fiches):
        parl, terr = fiche["parlementaire"], fiche["territoire"]
        fiche_header(
            parl["nom"], parl["prenom"], parl["chambre"],
            parl.get("libelle_dept"), parl.get("date_debut_mandat"),
        )
        c1, c2 = st.columns(2)
        with c1:
            stat_card(terr.get("nb_etablissements_industriels", 0), "Établissements industriels")
        with c2:
            stat_card(f'{terr.get("effectifs_estimes", 0):,}'.replace(",", " "), "Effectifs estimés")

        top_naf = terr.get("top_naf", [])
        if top_naf:
            fig = go.Figure(
                go.Bar(
                    x=[t["nb"] for t in top_naf],
                    y=[t["naf"] for t in top_naf],
                    orientation="h",
                    marker_color=COLORS["red_bright"],
                )
            )
            fig.update_layout(
                title="Top codes NAF (nb établissements)",
                height=280,
                margin=dict(l=10, r=10, t=40, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(autorange="reversed"),
            )
            st.plotly_chart(fig, use_container_width=True, key=f"naf-chart-{i}")
        st.divider()


def _reset_textes() -> None:
    st.session_state["tx_query"] = ""
    st.session_state["tx_cats"] = []
    st.session_state["tx_annee"] = 1990


def page_textes() -> None:
    eyebrow("Recherche")
    c_query, c_cats, c_annee, c_reset = st.columns([2, 2, 1, 0.8])
    with c_query:
        query = st.text_input(
            "Mots-clés", placeholder="ex : industrie automobile, décarbonation", key="tx_query",
        )
    with c_cats:
        cats = st.multiselect("Catégorie", options=list(CATEGORY_LABEL.keys()),
                               format_func=lambda k: CATEGORY_LABEL[k], key="tx_cats")
    with c_annee:
        annee_min = st.number_input("Année min.", min_value=1990, max_value=2030, step=1, key="tx_annee")
    with c_reset:
        st.markdown('<div style="height:1.85rem"></div>', unsafe_allow_html=True)
        st.button("Réinitialiser", key="tx_reset", on_click=_reset_textes, use_container_width=True)
    if not query:
        return

    try:
        with st.spinner("Recherche en cours…"):
            results = rechercher_textes(query, categories=cats or None, annee_min=annee_min)
    except Exception:
        logger.exception("Échec rechercher_textes(query=%r)", query)
        st.error("Service DOLE indisponible, réessayez plus tard.")
        return

    if results.empty:
        st.warning("Aucun texte trouvé.")
        return

    result_count(len(results), "texte trouvé", "textes trouvés")

    par_annee = results.dropna(subset=["annee"]).groupby("annee").size().sort_index()
    if len(par_annee) > 1:
        fig = go.Figure(go.Bar(x=par_annee.index.astype(str), y=par_annee.values,
                                marker_color=COLORS["red_bright"]))
        fig.update_layout(
            title="Évolution du nombre de textes par année",
            height=220,
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

    cols = st.columns(3)
    for i, row in results.iterrows():
        with cols[i % 3]:
            texte_card(row["title"], row["category_label"], row["annee"], row["article_synthesis"])


PAGES_MAP = {
    "Accueil": page_accueil,
    "Fiche territoire": page_fiche_territoire,
    "Textes législatifs": page_textes,
}
PAGES_MAP[page]()
