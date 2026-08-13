"""Página principal: resumen general del Observatorio de Analítica Deportiva."""
import pandas as pd
import streamlit as st

from utils.branding import apply_branding
from utils.data_loader import load_mart

st.set_page_config(page_title="Observatorio de Analítica Deportiva", page_icon="⚽", layout="wide")
apply_branding()

st.title("⚽ Observatorio de Analítica Deportiva")
st.caption("Superliga Danesa y Premiership Escocesa — Temporada 2025/2026 (temporada finalizada)")

fixtures = load_mart("fixtures_features")
if fixtures.empty:
    st.stop()  # data_loader ya mostró el st.error correspondiente

fixtures = fixtures.copy()
fixtures["home_team"] = fixtures["home_team"].astype(str)
fixtures["away_team"] = fixtures["away_team"].astype(str)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Partidos totales", len(fixtures))
col2.metric("Ligas", fixtures["league_name"].nunique())
col3.metric("Equipos", pd.concat([fixtures["home_team"], fixtures["away_team"]]).nunique())
col4.metric("Con datos de cuotas", f"{fixtures['has_odds'].mean():.0%}")
st.caption(
    f"Cobertura: {fixtures['starting_at'].min().strftime('%d-%m-%Y')} "
    f"→ {fixtures['starting_at'].max().strftime('%d-%m-%Y')}"
)

st.divider()

# ============================================================
# Panorama por liga: campeón de cada una (temporada ya finalizada)
# ============================================================
st.subheader("🏆 Campeones de la temporada", anchor=False)

standings = load_mart("standings_clean")
if not standings.empty:
    standings = standings.copy()
    league_map = fixtures[["league_id", "league_name"]].drop_duplicates().set_index("league_id")["league_name"].to_dict()
    standings["league_name"] = standings["league_id"].map(league_map)
    standings["team_name"] = standings["team_name"].astype(str)

    # misma lógica que la vista Posiciones: se toma la etapa de mayor puntaje por equipo
    standings_final = standings.sort_values("points", ascending=False).drop_duplicates(subset=["team_name", "league_id"], keep="first")
    champions = standings_final.sort_values("points", ascending=False).groupby("league_name").head(1)

    champ_cols = st.columns(len(champions))
    for col, (_, row) in zip(champ_cols, champions.iterrows()):
        with col:
            with st.container(border=True):
                st.markdown(f"**{row['league_name']}**")
                st.markdown(f"### {row['team_name']}")
                st.caption(f"{int(row['points'])} puntos en su mejor etapa")

st.divider()

# ============================================================
# Lo más destacado: sorpresa de mercado y partido con más goles
# ============================================================
st.subheader("📌 Datos destacados por liga", anchor=False)

market = load_mart("market_gap")
leagues = sorted(fixtures["league_name"].unique().tolist())
league_cols = st.columns(len(leagues))

for col, liga in zip(league_cols, leagues):
    league_fixtures = fixtures[fixtures["league_name"] == liga]

    with col:
        with st.container(border=True):
            st.markdown(f"<h4 style='margin:0 0 0.4rem 0'>{liga}</h4>", unsafe_allow_html=True)

            # --- Partido más sorprendente y con más goles ---
            if not market.empty:
                league_market = market[market["league_name"] == liga]
                if not league_market.empty:
                    top_surprise = league_market.sort_values("market_surprise", ascending=False).iloc[0]
                    st.markdown(
                        f"**Resultado más sorprendente:** {top_surprise['home_team']} "
                        f"{int(top_surprise['home_goals'])} - {int(top_surprise['away_goals'])} {top_surprise['away_team']} "
                        f"({top_surprise['market_surprise']:.0%} de sorpresa)"
                    )

            top_goals_match = league_fixtures.sort_values("total_goals", ascending=False).iloc[0]
            st.markdown(
                f"**Partido con más goles:** {top_goals_match['home_team']} "
                f"{int(top_goals_match['home_goals'])} - {int(top_goals_match['away_goals'])} {top_goals_match['away_team']} "
                f"({int(top_goals_match['total_goals'])} goles)"
            )

            st.divider()

            # --- Top 3 sorpresas de mercado ---
            st.markdown("**Top 3 sorpresas de mercado**")
            if not market.empty and not league_market.empty:
                top3 = league_market.sort_values("market_surprise", ascending=False).head(3)
                for i, (_, row) in enumerate(top3.iterrows(), start=1):
                    st.caption(
                        f"{i}. {row['home_team']} {int(row['home_goals'])}-{int(row['away_goals'])} "
                        f"{row['away_team']} · {row['market_surprise']:.0%}"
                    )
            else:
                st.caption("Sin datos de mercado disponibles.")

            st.divider()

            # --- Top 5 equipos goleadores ---
            st.markdown("**Top 5 equipos goleadores**")
            goals_home = league_fixtures.groupby("home_team")["home_goals"].sum()
            goals_away = league_fixtures.groupby("away_team")["away_goals"].sum()
            top_scorers = goals_home.add(goals_away, fill_value=0).sort_values(ascending=False).head(5)
            for i, (equipo, goles) in enumerate(top_scorers.items(), start=1):
                st.caption(f"{i}. {equipo} — {int(goles)} goles")
st.divider()

# ============================================================
# Navegación con teaser de datos reales por vista
# ============================================================
st.subheader("Explora el observatorio", anchor=False)

# Encabezados de tarjeta con HTML plano: st.markdown("#### ...") agrega un ancla de sección al pasar el mouse,
# que aquí no aporta nada (la tarjeta ya enlaza a la página vía st.page_link).
CARD_TITLE_HTML = "<h4 style='margin:0 0 0.4rem 0'>{icon} {title}</h4>"

home_stats = fixtures.groupby("home_team")["home_goals"].sum()
away_stats = fixtures.groupby("away_team")["away_goals"].sum()
top_scorer_team = (home_stats.add(away_stats, fill_value=0)).idxmax()
top_scorer_goals = int((home_stats.add(away_stats, fill_value=0)).max())
matchdays = fixtures["starting_at"].dt.date.nunique()
home_win_rate = fixtures["home_win"].mean()

nav1, nav2 = st.columns(2)
nav3, nav4 = st.columns(2)

with nav1:
    with st.container(border=True):
        st.markdown(CARD_TITLE_HTML.format(icon="📊", title="Rendimiento"), unsafe_allow_html=True)
        st.caption("Goles, puntos y forma reciente por equipo.")
        st.caption(f"Máximo goleador de la temporada: **{top_scorer_team}** ({top_scorer_goals} goles)")
        st.page_link("pages/1_📊_Rendimiento.py", label="Ver Rendimiento →")

with nav2:
    with st.container(border=True):
        st.markdown(CARD_TITLE_HTML.format(icon="📈", title="Posiciones"), unsafe_allow_html=True)
        st.caption("Evolución de la tabla y puntos acumulados a lo largo de la temporada.")
        st.caption(f"**{matchdays}** fechas de juego registradas en la temporada")
        st.page_link("pages/2_📈_Posiciones.py", label="Ver Posiciones →")

with nav3:
    with st.container(border=True):
        st.markdown(CARD_TITLE_HTML.format(icon="💰", title="Mercado"), unsafe_allow_html=True)
        st.caption("Brecha entre resultado real y probabilidad implícita de las cuotas.")
        if not market.empty:
            st.caption(f"Nivel de sorpresa promedio de la temporada: **{market['market_surprise'].mean():.0%}**")
        else:
            st.caption("Sin datos de mercado disponibles.")
        st.page_link("pages/3_💰_Mercado.py", label="Ver Mercado →")

with nav4:
    with st.container(border=True):
        st.markdown(CARD_TITLE_HTML.format(icon="🆚", title="Comparativa"), unsafe_allow_html=True)
        st.caption("Patrones de localía/visita y enfrentamientos directos (H2H) entre ligas.")
        st.caption(f"El equipo local gana **{home_win_rate:.0%}** de los partidos, en promedio")
        st.page_link("pages/4_🆚_Comparativa.py", label="Ver Comparativa →")

st.divider()
st.caption("Datos: Sportmonks Football API v3 · Alcance descriptivo y diagnóstico (sin modelos predictivos)")