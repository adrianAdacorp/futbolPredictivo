"""Feature engineering (Punto 1) + brecha vs. mercado.

Todo vectorizado (operaciones sobre columnas completas, sin bucles fila a fila),
lo que también contribuye al Punto 4 (rendimiento/memoria).
"""
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# 1) Features de fixtures: variables derivadas + binning
# --------------------------------------------------------------------------
def build_fixture_features(fx):
    fx = fx.copy()
    hg = fx["home_goals"].astype("float")
    ag = fx["away_goals"].astype("float")

    fx["total_goals"] = (hg + ag).astype("Int16")
    fx["goal_diff"] = (hg - ag).astype("Int16")

    # Resultado 1X2 (vectorizado con np.select).
    fx["result_1x2"] = np.select(
        [fx["goal_diff"] > 0, fx["goal_diff"] == 0], ["H", "D"], default="A")
    fx["home_win"] = (fx["goal_diff"] > 0).astype("int8")
    fx["btts"] = ((hg > 0) & (ag > 0)).astype("int8")  # both teams to score

    # Puntos otorgados (regla 3-1-0).
    fx["points_home"] = np.select(
        [fx["goal_diff"] > 0, fx["goal_diff"] == 0], [3, 1], default=0).astype("int8")
    fx["points_away"] = np.select(
        [fx["goal_diff"] < 0, fx["goal_diff"] == 0], [3, 1], default=0).astype("int8")

    # Componentes temporales.
    fx["month"] = fx["starting_at"].dt.month.astype("Int8")

    # Binning de goles totales.
    fx["goals_bin"] = pd.cut(
        fx["total_goals"].astype("float"),
        bins=[-0.1, 1, 3, np.inf],
        labels=["Bajo (0-1)", "Medio (2-3)", "Alto (4+)"],
    )
    return fx


# --------------------------------------------------------------------------
# 2) Agregación: forma reciente por equipo (ventana móvil)
# --------------------------------------------------------------------------
def add_recent_form(fx, window=5):
    """Puntos acumulados por equipo en los últimos `window` partidos (previos)."""
    # Formato largo: una fila por (equipo, partido).
    home = fx[["fixture_id", "starting_at", "league_name",
               "home_team", "points_home"]].rename(
        columns={"home_team": "team", "points_home": "points"})
    away = fx[["fixture_id", "starting_at", "league_name",
               "away_team", "points_away"]].rename(
        columns={"away_team": "team", "points_away": "points"})
    long = pd.concat([home, away], ignore_index=True)
    long = long.sort_values(["team", "starting_at"])

    # Media móvil de puntos, desplazada 1 para excluir el partido actual.
    long["form"] = (long.groupby("team", observed=True)["points"]
                    .transform(lambda s: s.shift(1).rolling(window, min_periods=1).mean()))

    form_map = long.set_index(["fixture_id", "team"])["form"]
    fx = fx.copy()
    fx["home_form"] = fx.set_index(["fixture_id", "home_team"]).index.map(form_map).astype("float32")
    fx["away_form"] = fx.set_index(["fixture_id", "away_team"]).index.map(form_map).astype("float32")
    return fx


# --------------------------------------------------------------------------
# 3) Agregación de odds 1X2 a nivel fixture (consenso + spread)
# --------------------------------------------------------------------------
def aggregate_1x2_odds(odds):
    """Consolida el mercado 'Fulltime Result' entre casas: consenso y spread."""
    m = odds[odds["market_description"] == "Fulltime Result"].copy()
    if m.empty:
        logger.warning("No hay mercado 'Fulltime Result' en odds.")
        return pd.DataFrame()

    # Media, min y max de la cuota por fixture y selección (Home/Draw/Away).
    agg = (m.groupby(["fixture_id", "label"], observed=True)["value"]
           .agg(mean_odd="mean", min_odd="min", max_odd="max", n_books="count")
           .reset_index())
    agg["spread"] = agg["max_odd"] - agg["min_odd"]

    # Pivotes por selección.
    mean_odds = agg.pivot(index="fixture_id", columns="label", values="mean_odd")
    spreads = agg.pivot(index="fixture_id", columns="label", values="spread")
    nbooks = agg.pivot(index="fixture_id", columns="label", values="n_books")

    out = pd.DataFrame(index=mean_odds.index)
    # Probabilidad implícita cruda = 1 / cuota media.
    for sel, col in [("Home", "imp_home"), ("Draw", "imp_draw"), ("Away", "imp_away")]:
        if sel in mean_odds.columns:
            out[col] = 1.0 / mean_odds[sel]
    # Normalización: quitar el margen (overround) para que sumen 1.
    prob_cols = [c for c in ("imp_home", "imp_draw", "imp_away") if c in out.columns]
    overround = out[prob_cols].sum(axis=1)
    for c in prob_cols:
        out[c] = out[c] / overround
    out["overround"] = overround - 1.0  # margen del mercado

    for sel, col in [("Home", "spread_home"), ("Draw", "spread_draw"), ("Away", "spread_away")]:
        if sel in spreads.columns:
            out[col] = spreads[sel]
    out["n_bookmakers"] = nbooks.max(axis=1)

    return out.reset_index()


# --------------------------------------------------------------------------
# 4) Merge fixtures + odds: brecha resultado real vs. mercado
# --------------------------------------------------------------------------
def build_market_gap(fx_feat, odds_1x2):
    """Une features de fixtures con odds y calcula la brecha vs. mercado."""
    df = fx_feat.merge(odds_1x2, on="fixture_id", how="inner")

    # Probabilidad implícita del resultado que realmente ocurrió.
    imp_actual = np.select(
        [df["result_1x2"] == "H", df["result_1x2"] == "D"],
        [df.get("imp_home"), df.get("imp_draw")],
        default=df.get("imp_away"),
    )
    df["imp_prob_actual"] = imp_actual.astype("float32")
    # Brecha/sorpresa: 1 - prob implícita del resultado real (alto = mayor sorpresa).
    df["market_surprise"] = (1.0 - df["imp_prob_actual"]).astype("float32")
    return df
