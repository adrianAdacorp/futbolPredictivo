"""Página principal: resumen general del Observatorio de Analítica Deportiva."""
import pandas as pd
import streamlit as st

from utils.branding import apply_branding
from utils.data_loader import load_mart

st.set_page_config(page_title="Observatorio de Analítica Deportiva", page_icon="⚽", layout="wide")
apply_branding()

st.title("⚽ Observatorio de Analítica Deportiva")
st.caption("Superliga Danesa y Premiership Escocesa — Temporada 2025/2026")

fixtures = load_mart("fixtures_features")
if fixtures.empty:
    st.stop()  # data_loader ya mostró el st.error correspondiente

col1, col2, col3, col4 = st.columns(4)
col1.metric("Partidos totales", len(fixtures))
col2.metric("Ligas", fixtures["league_name"].nunique())
col3.metric("Equipos", pd.concat([fixtures["home_team"], fixtures["away_team"]]).nunique())
col4.metric("Con datos de cuotas", f"{fixtures['has_odds'].mean():.0%}")

st.divider()
st.markdown("""
### Navegación
- **Rendimiento**: goles, puntos y forma reciente por equipo.
- **Posiciones**: evolución de la tabla a lo largo de la temporada.
- **Mercado**: brecha entre resultado real y probabilidad implícita de las cuotas.
- **Comparativa**: patrones localía/visita y H2H entre ligas.
""")
st.divider()
st.caption("Datos: Sportmonks Football API v3 · Alcance descriptivo y diagnóstico (sin modelos predictivos)")