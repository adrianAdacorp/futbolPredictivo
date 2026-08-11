"""Branding compartido: logo del proyecto en la barra lateral, común a todas las páginas."""
import streamlit as st

LOGO_PATH = "app/assets/logo.png"
ICON_PATH = "app/assets/icon.png"


def apply_branding():
    """Muestra el logo en el sidebar (expandido) y el icono (colapsado)."""
    st.logo(LOGO_PATH, icon_image=ICON_PATH, size="large")