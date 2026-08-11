"""Evolución de posición en tabla y forma reciente (pregunta de negocio 2)."""
import pandas as pd
import streamlit as st

from utils.charts import line_over_time
from utils.data_loader import load_mart, validate_filters
from utils.branding import apply_branding

st.set_page_config(page_title="Posiciones", page_icon="📈", layout="wide")
apply_branding()
st.title("📈 Evolución de Posiciones")

fixtures = load_mart("fixtures_features")
standings = load_mart("standings_clean")
if fixtures.empty or standings.empty:
    st.stop()

# standings_clean no trae league_name (solo league_id); se deriva desde fixtures_features
league_map = fixtures[["league_id", "league_name"]].drop_duplicates().set_index("league_id")["league_name"].to_dict()
standings = standings.copy()
standings["league_name"] = standings["league_id"].map(league_map)

# --- Filtros ---
st.sidebar.header("Filtros")
league = st.sidebar.selectbox("Liga", options=["Todas"] + sorted(fixtures["league_name"].unique().tolist()))
teams_available = sorted(pd.concat([fixtures["home_team"], fixtures["away_team"]]).unique().tolist())
teams = st.sidebar.multiselect("Equipo(s)", options=teams_available, default=teams_available[:5])

df = fixtures.copy()
standings_df = standings.copy()
if league != "Todas":
    df = validate_filters(df, league_name=league)
    standings_df = validate_filters(standings_df, league_name=league)

if df.empty or standings_df.empty:
    st.stop()

# --- Tabla final ---
# Supuesto: un equipo aparece en varias etapas (fase regular + campeonato/descenso, ver doc §5.4).
# Se toma la etapa de mayor `points` como representativa de la clasificación final.
# Aviso: `position` es relativa a esa etapa (ej. top-6), no necesariamente la posición oficial de liga.
st.subheader("Tabla de posiciones (etapa final por equipo)")
standings_final = (
    standings_df.sort_values("points", ascending=False)
    .drop_duplicates(subset=["team_name", "league_id"], keep="first")
)
# `position` original es relativo a la etapa (fase regular vs. campeonato/descenso) y se repite
# entre equipos de distintas etapas. Se calcula una posición general propia, por puntos, dentro de cada liga.
standings_final["Posición general"] = (
    standings_final.groupby("league_name")["points"].rank(method="first", ascending=False).astype(int)
)
standings_final = standings_final.sort_values(["league_name", "Posición general"])
COLUMN_LABELS = {"Posición general": "Pos.", "team_name": "Equipo", "points": "Puntos"}
COLUMN_CONFIG = {
    "Pos.": st.column_config.NumberColumn(width="small"),
    "Equipo": st.column_config.TextColumn(width="medium"),
    "Puntos": st.column_config.ProgressColumn(width="medium", min_value=0,
                                               max_value=int(standings_final["points"].max()), format="%d"),
}

if league == "Todas":
    for liga_nombre in sorted(standings_final["league_name"].unique()):
        st.markdown(f"**{liga_nombre}**")
        tabla_liga = standings_final[standings_final["league_name"] == liga_nombre]
        tabla_liga = tabla_liga[["Posición general", "team_name", "points"]].rename(columns=COLUMN_LABELS)
        st.dataframe(tabla_liga.reset_index(drop=True), use_container_width=True, hide_index=True,
                     column_config=COLUMN_CONFIG)
else:
    tabla = standings_final[["Posición general", "team_name", "points"]].rename(columns=COLUMN_LABELS)
    st.dataframe(tabla.reset_index(drop=True), use_container_width=True, hide_index=True,
                 column_config=COLUMN_CONFIG)

st.caption("Posición general calculada por puntos totales de la etapa con mayor puntaje de cada equipo; puede no coincidir con la tabla oficial final de liga, ya que ambas ligas dividen la temporada en fase regular y fase de campeonato/descenso.")

st.divider()

# --- Evolución de puntos acumulados ---
# standings_clean es un snapshot final, no serie temporal. La evolución se calcula
# agregando points_home/points_away de fixtures_features de forma acumulada por fecha.
st.subheader("Evolución de puntos acumulados")
home = df[["starting_at", "home_team", "points_home"]].rename(columns={"home_team": "team", "points_home": "points"})
away = df[["starting_at", "away_team", "points_away"]].rename(columns={"away_team": "team", "points_away": "points"})
long_df = pd.concat([home, away]).sort_values("starting_at")
long_df["cum_points"] = long_df.groupby("team")["points"].cumsum()

if teams:
    plot_df = long_df[long_df["team"].isin(teams)]
    st.plotly_chart(line_over_time(plot_df, "starting_at", "cum_points", "team", "Puntos acumulados en el tiempo", y_label="Puntos acumulados"), use_container_width=True)
else:
    st.info("Selecciona uno o más equipos en el filtro lateral.")

st.divider()

# --- Forma reciente ---
st.subheader("Forma reciente")
st.caption("Media móvil de puntos de los últimos 5 partidos previos (shift(1), sin fuga de información).")
if teams:
    form_home = df[["starting_at", "home_team", "home_form"]].rename(columns={"home_team": "team", "home_form": "form"})
    form_away = df[["starting_at", "away_team", "away_form"]].rename(columns={"away_team": "team", "away_form": "form"})
    form_df = pd.concat([form_home, form_away])
    form_df = form_df[form_df["team"].isin(teams)]
    st.plotly_chart(line_over_time(form_df, "starting_at", "form", "team", "Forma reciente (últimos 5 partidos)", y_label="Puntos promedio (últimos 5)"), use_container_width=True)