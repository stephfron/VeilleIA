"""Point d'entrée Streamlit — VeilleIA. UI uniquement, aucune logique métier."""
from dotenv import load_dotenv
load_dotenv()

import plotly.graph_objects as go
import streamlit as st

from services.fiche_territoire import rechercher_parlementaire
from services.api_dole import rechercher_textes, CATEGORY_LABEL
from ui.style import inject_css
from ui.components import eyebrow, stat_card, texte_card, fiche_header
from ui.theme import COLORS

st.set_page_config(page_title="VeilleIA", page_icon="🏭", layout="wide")
inject_css()

PAGES = ["Accueil", "Fiche territoire", "Textes législatifs"]
page = st.sidebar.radio("Navigation", PAGES, label_visibility="collapsed")


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
        ("Fiche territoire", "Élus, établissements industriels et effectifs par département."),
        ("Textes législatifs", "Lois, ordonnances et propositions filtrables par mots-clés."),
        ("Données publiques", "RNE, SIRENE (INSEE) et DOLE — actualisées toutes les 24 h."),
    ]
    for col, (titre, desc) in zip(cols, shortcuts):
        with col:
            st.markdown(
                f'<div class="uimm-card"><h4>{titre}</h4>'
                f'<p class="uimm-card__muted">{desc}</p></div>',
                unsafe_allow_html=True,
            )


def page_fiche_territoire() -> None:
    eyebrow("Recherche")
    query = st.text_input("Nom, département ou code département", placeholder="ex : Dupont, 69, Rhône")
    if not query:
        return

    with st.spinner("Recherche en cours…"):
        fiches = rechercher_parlementaire(query)

    if not fiches:
        st.warning("Aucun résultat pour cette recherche.")
        return

    for fiche in fiches:
        parl, terr = fiche["parlementaire"], fiche["territoire"]
        fiche_header(
            parl["nom"], parl["prenom"], parl["chambre"],
            parl.get("libelle_dept"), parl.get("date_debut_mandat"),
        )
        c1, c2 = st.columns(2)
        with c1:
            stat_card(terr["nb_etablissements_industriels"], "Établissements industriels")
        with c2:
            stat_card(f'{terr["effectifs_estimes"]:,}'.replace(",", " "), "Effectifs estimés")

        top_naf = terr["top_naf"]
        if top_naf:
            fig = go.Figure(
                go.Bar(
                    x=[t["nb"] for t in top_naf],
                    y=[t["naf"] for t in top_naf],
                    orientation="h",
                    marker_color=COLORS["red"],
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
            st.plotly_chart(fig, use_container_width=True)
        st.divider()


def page_textes() -> None:
    eyebrow("Recherche")
    query = st.text_input("Mots-clés", placeholder="ex : industrie automobile, décarbonation")
    cats = st.multiselect("Catégorie", options=list(CATEGORY_LABEL.keys()),
                           format_func=lambda k: CATEGORY_LABEL[k])
    if not query:
        return

    with st.spinner("Recherche en cours…"):
        results = rechercher_textes(query, categories=cats or None)

    if results.empty:
        st.warning("Aucun texte trouvé.")
        return

    cols = st.columns(3)
    for i, row in results.iterrows():
        with cols[i % 3]:
            texte_card(row["title"], row["category_label"], row["annee"], row["article_synthesis"])


{"Accueil": page_accueil, "Fiche territoire": page_fiche_territoire, "Textes législatifs": page_textes}[page]()
