"""Patrones de localía/visita y enfrentamientos directos (H2H) entre ligas (pregunta de negocio 3)."""
import pandas as pd
import streamlit as st

from utils.charts import grouped_bar
from utils.data_loader import load_mart
from utils.branding import apply_branding

st.set_page_config(page_title="Comparativa", page_icon="🆚", layout="wide")
apply_branding()

st.title("🆚 Comparativa entre Ligas")

fixtures = load_mart("fixtures_features")
if fixtures.empty:
    st.stop()

fixtures = fixtures.copy()
fixtures["league_name"] = fixtures["league_name"].astype(str)
fixtures["home_team"] = fixtures["home_team"].astype(str)
fixtures["away_team"] = fixtures["away_team"].astype(str)

with st.expander("¿Cómo leer este panel? (glosario rápido)"):
    st.markdown("""
- **Ventaja de local**: qué tan seguido gana el equipo que juega en casa, en cada liga.
- **Ambos anotan (BTTS)**: porcentaje de partidos donde los dos equipos marcaron al menos un gol.
- **H2H**: historial de enfrentamientos directos entre dos equipos específicos.
""")

# ============================================================
# Sección 1: Patrones de localía/visita por liga
# ============================================================
st.subheader("¿La localía pesa igual en ambas ligas?")
st.caption("Porcentaje de partidos según quién ganó, comparando la Superliga Danesa contra la Premiership Escocesa.")

outcome_pct = pd.crosstab(fixtures["league_name"], fixtures["result_1x2"], normalize="index") * 100
outcome_pct = outcome_pct.rename(columns={"H": "Gana el local", "D": "Empate", "A": "Gana el visitante"})
outcome_long = outcome_pct.reset_index().melt(id_vars="league_name", var_name="Resultado", value_name="pct")

st.plotly_chart(
    grouped_bar(outcome_long, "league_name", "pct", "Resultado", "Resultados por liga", y_label="% de partidos"),
    use_container_width=True,
)

st.divider()

# ============================================================
# Sección 2: Estilo de juego por liga (goles y BTTS)
# ============================================================
st.subheader("¿Qué liga ofrece más goles?")

liga_stats = fixtures.groupby("league_name").agg(
    partidos=("fixture_id", "count"),
    promedio_goles=("total_goals", "mean"),
    pct_ambos_anotan=("btts", "mean"),
).reset_index()

cols = st.columns(len(liga_stats))
for col, (_, row) in zip(cols, liga_stats.iterrows()):
    with col:
        st.markdown(f"**{row['league_name']}**")
        st.metric("Partidos analizados", int(row["partidos"]))
        st.metric("Goles promedio por partido", f"{row['promedio_goles']:.2f}")
        st.metric("Partidos con ambos equipos anotando", f"{row['pct_ambos_anotan']:.0%}")

st.divider()

# ============================================================
# Sección 3: Enfrentamientos directos (H2H)
# ============================================================
st.subheader("Enfrentamientos directos (H2H)")
st.caption("Elige una liga y dos equipos para ver su historial de cruces en la temporada.")

st.sidebar.header("Filtros H2H")
league_h2h = st.sidebar.selectbox("Liga", options=sorted(fixtures["league_name"].unique().tolist()))
teams_in_league = sorted(pd.concat([
    fixtures.loc[fixtures["league_name"] == league_h2h, "home_team"],
    fixtures.loc[fixtures["league_name"] == league_h2h, "away_team"],
]).unique().tolist())

if len(teams_in_league) < 2:
    st.warning("No hay suficientes equipos en esta liga para comparar.")
    st.stop()

col1, col2 = st.sidebar.columns(2)
team_a = col1.selectbox("Equipo A", options=teams_in_league, index=0)

# Equipo B excluye al ya elegido en Equipo A: evita la combinación imposible de comparar un equipo consigo mismo.
teams_for_b = [t for t in teams_in_league if t != team_a]
team_b = col2.selectbox("Equipo B", options=teams_for_b, index=0)

h2h = fixtures[
    (fixtures["league_name"] == league_h2h)
    & (((fixtures["home_team"] == team_a) & (fixtures["away_team"] == team_b))
       | ((fixtures["home_team"] == team_b) & (fixtures["away_team"] == team_a)))
].sort_values("starting_at")

if h2h.empty:
    st.info(f"{team_a} y {team_b} no se han enfrentado esta temporada.")
    st.stop()

wins_a = ((h2h["home_team"] == team_a) & (h2h["result_1x2"] == "H")).sum() + \
         ((h2h["away_team"] == team_a) & (h2h["result_1x2"] == "A")).sum()
wins_b = ((h2h["home_team"] == team_b) & (h2h["result_1x2"] == "H")).sum() + \
         ((h2h["away_team"] == team_b) & (h2h["result_1x2"] == "A")).sum()
draws = (h2h["result_1x2"] == "D").sum()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Enfrentamientos", len(h2h))
m2.metric(f"Victorias {team_a}", int(wins_a))
m3.metric(f"Victorias {team_b}", int(wins_b))
m4.metric("Empates", int(draws))

for _, row in h2h.iterrows():
    with st.container(border=True):
        fecha = row["starting_at"].strftime("%d-%m-%Y")
        marcador = f"{row['home_team']}  {int(row['home_goals'])} - {int(row['away_goals'])}  {row['away_team']}"
        st.markdown(f"**{marcador}**  ·  {fecha}")