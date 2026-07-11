"""Composants UI réutilisables — charte visuelle UIMM (badges, cards, stats)."""
import html
import streamlit as st


def _esc(value: object) -> str:
    """Échappe toute valeur issue des services externes avant injection HTML."""
    return html.escape(str(value))


def eyebrow(label: str) -> None:
    st.markdown(f'<div class="uimm-eyebrow">/ {_esc(label)} /</div>', unsafe_allow_html=True)


def _badge_html(text: str, light: bool = False) -> str:
    cls = "uimm-badge uimm-badge--light" if light else "uimm-badge"
    return f'<span class="{cls}">{_esc(text)}</span>'


def stat_card(value: str | int, label: str) -> None:
    st.markdown(
        f'<div class="uimm-stat">'
        f'<div class="uimm-stat__value">{_esc(value)}</div>'
        f'<div class="uimm-stat__label">{_esc(label)}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def texte_card(titre: str, categorie: str, annee: int | None, synthese: str | None) -> None:
    badges = _badge_html(categorie) + (_badge_html(str(annee), light=True) if annee else "")
    extrait = (synthese or "")[:180]
    extrait += "…" if synthese and len(synthese) > 180 else ""
    st.markdown(
        f'<div class="uimm-card">{badges}<h4>{_esc(titre)}</h4>'
        f'<p class="uimm-card__muted">{_esc(extrait)}</p></div>',
        unsafe_allow_html=True,
    )


def fiche_header(nom: str, prenom: str, chambre: str, dept: str | None, mandat: str | None) -> None:
    dept_txt = f" — {_esc(dept)}" if dept else ""
    mandat_txt = f"Mandat depuis {_esc(mandat)}" if mandat else "Date de mandat inconnue"
    st.markdown(
        f'<div class="uimm-section-dark">'
        f'<div class="uimm-eyebrow">/ Fiche territoire /</div>'
        f"<h2>{_esc(prenom)} {_esc(nom)}</h2>"
        f"<p>{_esc(chambre)}{dept_txt} · {mandat_txt}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )
