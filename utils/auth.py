"""Authentification de l'app — gate l'accès avant toute page."""
import streamlit as st
import streamlit_authenticator as stauth
from utils.config import AUTH_USERNAME, AUTH_PASSWORD_HASH, AUTH_COOKIE_KEY


def require_login() -> None:
    """
    Affiche un formulaire de connexion et arrête le script (st.stop()) tant que
    l'utilisateur n'est pas authentifié. Credentials attendus en variables d'env
    (AUTH_USERNAME, AUTH_PASSWORD_HASH, AUTH_COOKIE_KEY) — voir render.yaml.
    """
    if not (AUTH_USERNAME and AUTH_PASSWORD_HASH and AUTH_COOKIE_KEY):
        st.error(
            "Authentification non configurée : AUTH_USERNAME, AUTH_PASSWORD_HASH "
            "et AUTH_COOKIE_KEY doivent être définies (voir .env / Render)."
        )
        st.stop()

    credentials = {
        "usernames": {
            AUTH_USERNAME: {
                "name": AUTH_USERNAME,
                "password": AUTH_PASSWORD_HASH,
                "email": "",
            }
        }
    }
    authenticator = stauth.Authenticate(
        credentials,
        cookie_name="veilleia_auth",
        cookie_key=AUTH_COOKIE_KEY,
        cookie_expiry_days=7,
        auto_hash=False,
    )
    authenticator.login(location="main")

    auth_status = st.session_state.get("authentication_status")
    if auth_status is False:
        st.error("Identifiants incorrects.")
        st.stop()
    if auth_status is None:
        st.stop()

    authenticator.logout("Se déconnecter", location="sidebar")
