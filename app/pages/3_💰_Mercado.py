"""Eficiencia del mercado de cuotas: sobre/sub-rendimiento vs. probabilidad implícita (pregunta de negocio 1)."""
import numpy as np
import pandas as pd
import streamlit as st

from utils.charts import diverging_bar_by_team, distribution_hist
from utils.data_loader import load_mart, validate_filters
from utils.branding import apply_branding

st.set_page_config(page_title="Mercado", page_icon="💰", layout="wide")
apply_branding()

st.title("💰 Eficiencia del Mercado de Cuotas")
st.caption(
    "Compara lo que el mercado de apuestas esperaba (probabilidad implícita) con lo que realmente ocurrió. "
    "Un equipo con **sobre-rendimiento** consigue más puntos de los que el mercado anticipaba; "
    "uno con **sub-rendimiento**, menos."
)

with st.expander("¿Cómo leer este panel? (glosario rápido)"):
    st.markdown("""
- **Probabilidad implícita**: lo que las cuotas de apuestas sugieren que va a pasar, en porcentaje.
- **Sorpresa de mercado**: qué tan inesperado fue el resultado real frente a esa probabilidad. 0% = resultado totalmente esperado; 100% = resultado que el mercado casi descartaba.
- **Sobre-rendimiento**: el equipo sumó más puntos de los que las cuotas "predecían".
- **Sub-rendimiento**: el equipo sumó menos puntos de los que las cuotas predecían.
""")

df_full = load_mart("market_gap")
if df_full.empty:
    st.stop()

# --- Filtros ---
st.sidebar.header("Filtros")
league = st.sidebar.selectbox("Liga", options=["Todas"] + sorted(df_full["league_name"].unique().tolist()))
teams_available = sorted(pd.concat([df_full["home_team"], df_full["away_team"]]).unique().tolist())
teams = st.sidebar.multiselect("Equipo(s) — resaltar en tabla de sorpresas", options=teams_available, default=[])
date_min, date_max = df_full["starting_at"].min().date(), df_full["starting_at"].max().date()
date_range = st.sidebar.slider("Rango de fechas", min_value=date_min, max_value=date_max, value=(date_min, date_max))

df = df_full.copy()
if league != "Todas":
    df = validate_filters(df, league_name=league)
df = df[(df["starting_at"].dt.date >= date_range[0]) & (df["starting_at"].dt.date <= date_range[1])]

if df.empty:
    st.stop()

# --- KPIs ---
col1, col2, col3 = st.columns(3)
col1.metric("Comisión de las casas de apuestas", f"{df['overround'].mean():.1%}",
            help="Es como el margen de una tienda: lo que ganan las casas de apuestas por partido, más allá de acertar el resultado. Ya está descontado de las probabilidades de este panel.")
col2.metric("Nivel de sorpresa promedio", f"{df['market_surprise'].mean():.1%}",
            help="Qué tan seguido gana 'el que no era favorito'. Cerca de 0% = casi siempre gana el favorito de las cuotas. Cerca de 100% = casi siempre gana el menos favorito.")
col3.metric("Casas de apuestas consultadas por partido", f"{df['n_bookmakers'].mean():.0f}",
            help="Cuántas casas de apuestas distintas se promediaron para calcular la probabilidad de cada partido. Más casas = dato más confiable.")

st.divider()

# --- Sobre / sub-rendimiento por equipo ---
st.subheader("¿Qué equipos superan o decepcionan frente al mercado?")
st.caption(
    "Compara los puntos que cada equipo realmente sumó contra los puntos que las cuotas de apuestas anticipaban. "
    "🟩 Verde = rindió mejor de lo esperado. 🟥 Rojo = rindió peor de lo esperado."
)

home_perf = df[["home_team", "imp_home", "imp_draw", "points_home"]].copy()
home_perf["expected_points"] = home_perf["imp_home"] * 3 + home_perf["imp_draw"] * 1
home_perf["gap"] = home_perf["points_home"] - home_perf["expected_points"]
home_perf = home_perf.rename(columns={"home_team": "team"})

away_perf = df[["away_team", "imp_away", "imp_draw", "points_away"]].copy()
away_perf["expected_points"] = away_perf["imp_away"] * 3 + away_perf["imp_draw"] * 1
away_perf["gap"] = away_perf["points_away"] - away_perf["expected_points"]
away_perf = away_perf.rename(columns={"away_team": "team"})

perf = pd.concat([home_perf[["team", "gap"]], away_perf[["team", "gap"]]], ignore_index=True)

st.plotly_chart(
    diverging_bar_by_team(perf, "team", "gap", "Sobre / sub-rendimiento vs. mercado (puntos por partido)",
                           x_label="Diferencia promedio de puntos (real − esperado)"),
    use_container_width=True,
)

st.divider()

# --- Distribución de sorpresas ---
st.subheader("¿Qué tan predecible es cada liga?")
st.caption(
    "Cada barra agrupa partidos según su nivel de sorpresa. Muchas barras a la izquierda = liga predecible "
    "(ganan los favoritos). Barras repartidas hacia la derecha = liga con más resultados inesperados."
)
st.plotly_chart(
    distribution_hist(df, "market_surprise", "Distribución de sorpresas de mercado",
                       x_label="Nivel de sorpresa (0% = resultado esperado, 100% = resultado inesperado)"),
    use_container_width=True,
)

st.divider()

# --- Top partidos más sorprendentes ---
st.subheader("Partidos más sorprendentes")
top_surprises = df.sort_values("market_surprise", ascending=False).head(15)
if teams:
    top_surprises = top_surprises[top_surprises["home_team"].isin(teams) | top_surprises["away_team"].isin(teams)]

top_surprises = top_surprises.copy()
top_surprises["home_team"] = top_surprises["home_team"].astype(str)
top_surprises["away_team"] = top_surprises["away_team"].astype(str)

top_surprises["Marcador"] = (
    top_surprises["home_team"] + "  " + top_surprises["home_goals"].astype(str)
    + " - " + top_surprises["away_goals"].astype(str) + "  " + top_surprises["away_team"]
)

outcome_cols = ["imp_home", "imp_draw", "imp_away"]
outcome_to_code = {"imp_home": "H", "imp_draw": "D", "imp_away": "A"}
top_surprises["imp_favorito"] = top_surprises[outcome_cols].max(axis=1)
top_surprises["outcome_favorito"] = top_surprises[outcome_cols].idxmax(axis=1).map(outcome_to_code)
top_surprises["equipo_favorito"] = np.select(
    [top_surprises["outcome_favorito"] == "H", top_surprises["outcome_favorito"] == "A"],
    [top_surprises["home_team"], top_surprises["away_team"]],
    default="el empate",
)


def describe_match(row):
    """Narrativa enriquecida del partido: qué esperaba el mercado vs. qué pasó realmente en la cancha."""
    home, away = row["home_team"], row["away_team"]
    hg, ag = int(row["home_goals"]), int(row["away_goals"])
    result, fav_team, fav_prob = row["result_1x2"], row["equipo_favorito"], row["imp_favorito"] * 100
    marcador = f"{home} {hg}-{ag} {away}"

    diff, total = abs(hg - ag), hg + ag
    if diff >= 3:
        flavor = "una auténtica goleada"
    elif total >= 4:
        flavor = "un festival de goles"
    elif total == 0:
        flavor = "un cero a cero sin concesiones"
    else:
        flavor = "un partido cerrado hasta el final"

    if result == "D":
        actual = "el marcador terminó parejo"
    elif result == "H":
        actual = f"fue {home} quien se llevó los 3 puntos"
    else:
        actual = f"fue {away} quien se llevó los 3 puntos"

    gano_favorito = row["outcome_favorito"] == result
    fav_prep = "al empate" if fav_team == "el empate" else f"a {fav_team}"

    if gano_favorito:
        return (f"Ni el propio mercado tenía un favorito claro: la opción más probable apenas llegaba "
                f"{fav_prob:.0f}% ({fav_team}), y aun así se cumplió, en {flavor} ({marcador}).")
    return (f"El mercado le daba {fav_prep} un {fav_prob:.0f}% de probabilidad, pero {actual} "
            f"en {flavor} ({marcador}).")


top_surprises["Por qué interesa"] = top_surprises.apply(describe_match, axis=1)

top_surprises["Fecha_fmt"] = top_surprises["starting_at"].dt.strftime("%d-%m-%Y")

if top_surprises.empty and teams:
    st.info("Ningún partido del top 15 de sorpresas involucra a los equipos seleccionados.")
else:
    for _, row in top_surprises.iterrows():
        with st.container(border=True):
            col_a, col_b = st.columns([3, 1])
            col_a.markdown(f"**{row['Marcador']}**  ·  {row['Fecha_fmt']}")
            col_b.markdown(f"Sorpresa: **{row['market_surprise']:.0%}**")
            st.caption(row["Por qué interesa"])