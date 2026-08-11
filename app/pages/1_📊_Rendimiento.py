"""Vista de rendimiento de equipos: goles, puntos y forma reciente (pregunta de negocio 2)."""
import numpy as np
import pandas as pd
import streamlit as st

from utils.charts import bar_by_team
from utils.data_loader import load_mart
from utils.branding import apply_branding

st.set_page_config(page_title="Rendimiento", page_icon="📊", layout="wide")
apply_branding()
st.title("📊 Rendimiento de Equipos")

fixtures = load_mart("fixtures_features")
if fixtures.empty:
    st.stop()

# --- Filtros ---
st.sidebar.header("Filtros")
league = st.sidebar.selectbox("Liga", options=["Todas"] + sorted(fixtures["league_name"].unique().tolist()))

# Equipo(s) depende de la liga elegida: evita combinaciones imposibles (ej. equipo danés + liga escocesa)
fixtures_by_league = fixtures if league == "Todas" else fixtures[fixtures["league_name"] == league]
teams_available = sorted(pd.concat([fixtures_by_league["home_team"], fixtures_by_league["away_team"]]).unique().tolist())
teams = st.sidebar.multiselect("Equipo(s)", options=teams_available, default=[])

date_min, date_max = fixtures["starting_at"].min().date(), fixtures["starting_at"].max().date()
date_range = st.sidebar.slider("Rango de fechas", min_value=date_min, max_value=date_max, value=(date_min, date_max))

df = fixtures_by_league.copy()
df = df[(df["starting_at"].dt.date >= date_range[0]) & (df["starting_at"].dt.date <= date_range[1])]
if teams:
    df = df[df["home_team"].isin(teams) | df["away_team"].isin(teams)]

if df.empty:
    st.warning("No hay partidos para los filtros seleccionados.")
    st.stop()

# --- Unificar perspectiva local/visitante para stats por equipo ---
if len(teams) == 1:
    # Un solo equipo seleccionado: desglose por rival enfrentado (su propio rendimiento en cada cruce),
    # no el listado de rivales con sus propios números.
    selected_team = teams[0]
    matches = df[(df["home_team"] == selected_team) | (df["away_team"] == selected_team)]
    is_home = (matches["home_team"] == selected_team).to_numpy()

    team_stats = pd.DataFrame({
        "team": np.where(is_home, matches["away_team"], matches["home_team"]),          # rival
        "goals_for": np.where(is_home, matches["home_goals"], matches["away_goals"]),    # goles del seleccionado
        "points": np.where(is_home, matches["points_home"], matches["points_away"]),     # puntos del seleccionado
    })
    goals_title = f"Goles a favor de {selected_team} por rival"
    points_title = f"Puntos obtenidos por {selected_team} por rival"
else:
    home = df[["home_team", "home_goals", "away_goals", "points_home"]].rename(
        columns={"home_team": "team", "home_goals": "goals_for", "away_goals": "goals_against", "points_home": "points"})
    away = df[["away_team", "away_goals", "home_goals", "points_away"]].rename(
        columns={"away_team": "team", "away_goals": "goals_for", "home_goals": "goals_against", "points_away": "points"})
    team_stats = pd.concat([home, away], ignore_index=True)
    if teams:
        team_stats = team_stats[team_stats["team"].isin(teams)]
    goals_title = "Goles a favor (total)"
    points_title = "Puntos acumulados"

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(bar_by_team(team_stats, "team", "goals_for", goals_title, y_label="Goles", agg="sum"), use_container_width=True)
with col2:
    st.plotly_chart(bar_by_team(team_stats, "team", "points", points_title, y_label="Puntos", agg="sum"), use_container_width=True)

st.divider()
st.subheader("Detalle de partidos")

if len(teams) == 1:
    # Un partido por fila desde la perspectiva del equipo seleccionado: rival, condición, goles y puntos propios.
    detail = pd.DataFrame({
        "Fecha": matches["starting_at"],
        "Rival": np.where(is_home, matches["away_team"], matches["home_team"]),
        "Condición": np.where(is_home, "Local", "Visitante"),
        "Goles a favor": np.where(is_home, matches["home_goals"], matches["away_goals"]),
        "Goles en contra": np.where(is_home, matches["away_goals"], matches["home_goals"]),
        "Puntos": np.where(is_home, matches["points_home"], matches["points_away"]),
    }).sort_values("Fecha")
else:
    detail = df.copy()
    detail["home_team"] = detail["home_team"].astype(str)
    detail["away_team"] = detail["away_team"].astype(str)
    detail["Marcador"] = (
        detail["home_team"] + "  " + detail["home_goals"].astype(str)
        + " - " + detail["away_goals"].astype(str) + "  " + detail["away_team"]
    )
    cols = ["starting_at", "league_name", "Marcador"] if league == "Todas" else ["starting_at", "Marcador"]
    detail = detail[cols].rename(columns={"starting_at": "Fecha", "league_name": "Liga"}).sort_values("Fecha")

detail = detail.reset_index(drop=True)
detail["Fecha"] = pd.to_datetime(detail["Fecha"]).dt.strftime("%d-%m-%Y")

if detail.empty:
    st.info("No hay partidos que coincidan con los filtros seleccionados.")
else:
    st.dataframe(detail, use_container_width=True, hide_index=True)