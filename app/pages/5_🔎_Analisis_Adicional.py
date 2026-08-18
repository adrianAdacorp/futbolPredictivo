"""Consenso del mercado de cuotas y estacionalidad de goles (preguntas de negocio 4 y 5)."""
import pandas as pd
import streamlit as st

from utils.branding import apply_branding
from utils.charts import grouped_bar, scatter_gap
from utils.data_loader import load_mart

st.set_page_config(page_title="Análisis Adicional", page_icon="🔎", layout="wide")
apply_branding()

st.title("🔎 Análisis Adicional")
st.caption("Dos preguntas complementarias: qué tan de acuerdo están las casas de apuestas, y cuándo se concentran los goles en la temporada.")

market = load_mart("market_gap")
if market.empty:
    st.stop()

market = market.copy()
market["home_team"] = market["home_team"].astype(str)
market["away_team"] = market["away_team"].astype(str)

# --- Filtros (compartidos por ambas secciones) ---
st.sidebar.header("Filtros")
league = st.sidebar.selectbox("Liga", options=["Todas"] + sorted(market["league_name"].unique().tolist()))
metric_choice = st.sidebar.selectbox(
    "Mercado a analizar (dispersión)",
    options=["Promedio de los 3 resultados", "Solo victoria local", "Solo empate", "Solo victoria visitante"],
)
date_min, date_max = market["starting_at"].min().date(), market["starting_at"].max().date()
date_range = st.sidebar.slider("Rango de fechas", min_value=date_min, max_value=date_max, value=(date_min, date_max))

df = market.copy()
if league != "Todas":
    df = df[df["league_name"] == league]
df = df[(df["starting_at"].dt.date >= date_range[0]) & (df["starting_at"].dt.date <= date_range[1])]

if df.empty:
    st.warning("No hay partidos para los filtros seleccionados.")
    st.stop()

# ============================================================
# Sección 1 — Pregunta de negocio 4: Consenso del mercado
# ============================================================
st.header("1. ¿Qué tan de acuerdo están las casas de apuestas entre sí?")
st.caption(
    "Pregunta de negocio: ¿existe relación entre el desacuerdo de las casas de apuestas sobre un partido "
    "y la probabilidad de que el resultado termine siendo una sorpresa?"
)

with st.expander("¿Cómo leer este gráfico?", expanded=True):
    st.markdown("""
Cada **punto es un partido**. Mientras más a la derecha, mayor fue el desacuerdo entre las casas de apuestas
sobre ese resultado; mientras más arriba, más sorprendente fue lo que realmente ocurrió.
Si los puntos tienden a subir de izquierda a derecha, significa que el desacuerdo del mercado anticipa sorpresas.

- **Dispersión (spread)**: diferencia entre la cuota más alta y la más baja para un mismo resultado.
- **Nivel de sorpresa**: qué tan inesperado fue el resultado real frente a la probabilidad de mercado.
""")

metric_map = {
    "Promedio de los 3 resultados": None,
    "Solo victoria local": "spread_home",
    "Solo empate": "spread_draw",
    "Solo victoria visitante": "spread_away",
}
spread_col = metric_map[metric_choice]
if spread_col is None:
    df["dispersion"] = df[["spread_home", "spread_draw", "spread_away"]].mean(axis=1)
else:
    df["dispersion"] = df[spread_col]

corr = df["dispersion"].corr(df["market_surprise"])

k1, k2, k3 = st.columns(3)
k1.metric("Correlación dispersión ↔ sorpresa", f"{corr:.2f}",
           help="Va de -1 a 1. Cerca de 0 = sin relación clara. Positivo = a mayor desacuerdo entre casas, mayor sorpresa.")
k2.metric("Casas de apuestas promedio consultadas", f"{df['n_bookmakers'].mean():.0f}")
k3.metric("Comisión promedio del mercado", f"{df['overround'].mean():.1%}")

st.plotly_chart(
    scatter_gap(df, "dispersion", "market_surprise", "league_name", "name",
                "Dispersión entre casas de apuestas vs. nivel de sorpresa",
                x_label="Dispersión entre casas de apuestas", y_label="Nivel de sorpresa"),
    use_container_width=True,
)

st.divider()

# ============================================================
# Sección 2 — Pregunta de negocio 5: Estacionalidad de goles
# ============================================================
st.header("2. ¿Cuándo se concentran los partidos de más goles en la temporada?")
st.caption(
    "Pregunta de negocio: ¿el nivel de goles varía según el tramo de la temporada, y ese patrón es distinto entre ligas?"
)

# Se agrupa en 3 tramos cronológicos por liga, no por mes calendario: con ~40 partidos por mes
# el promedio mensual es muy ruidoso y zigzaguea sin mostrar una tendencia real. Agrupar en tercios
# da una muestra más grande por punto y una tendencia legible.
TRAMOS = ["Inicio de temporada", "Mitad de temporada", "Tramo final"]
df["tramo_temporada"] = df.groupby("league_name")["starting_at"].transform(
    lambda s: pd.qcut(s.rank(method="first"), 3, labels=TRAMOS)
)
by_tramo = df.groupby(["tramo_temporada", "league_name"], as_index=False)["total_goals"].mean()

with st.expander("¿Cómo leer este gráfico?", expanded=True):
    st.markdown("""
Cada barra es el **promedio de goles por partido** en ese tramo de la temporada, separado por liga.
Se agrupó en 3 tramos (no por mes) porque con pocos partidos por mes el promedio salta mucho de un mes
a otro sin mostrar una tendencia real — agrupar en tercios da una lectura más confiable.
""")

st.plotly_chart(
    grouped_bar(by_tramo, "tramo_temporada", "total_goals", "league_name",
                "Goles promedio por partido según el tramo de la temporada", y_label="Goles promedio por partido",
                decimals=2),
    use_container_width=True,
)

st.divider()
st.subheader("Distribución de partidos por nivel de goles")

goals_bin_pct = pd.crosstab(df["league_name"], df["goals_bin"], normalize="index") * 100
goals_bin_long = goals_bin_pct.reset_index().melt(id_vars="league_name", var_name="Nivel de goles", value_name="pct")

st.plotly_chart(
    grouped_bar(goals_bin_long, "league_name", "pct", "Nivel de goles",
                "Partidos por nivel de goles y liga", y_label="% de partidos"),
    use_container_width=True,
)