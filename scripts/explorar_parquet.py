"""Explorador de los datasets Parquet generados (evidencia para sustentación).

Uso (desde la raíz):
    python scripts/explorar_parquet.py
"""
import logging

import _bootstrap  # noqa: F401
import pandas as pd

from config import settings
from src.logger import setup_logging
from src.optimize import memory_mb

logger = logging.getLogger("explorar")

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)


def _cargar(dataset):
    ruta = settings.PARQUET_DIR / dataset
    if not ruta.exists():
        logger.warning("Dataset '%s' no existe en %s", dataset, ruta)
        return None
    return pd.read_parquet(ruta)


def _resumen(nombre, df):
    if df is None or df.empty:
        logger.warning("[%s] vacío o inexistente.", nombre)
        return
    logger.info("=" * 60)
    logger.info("[%s] filas=%s | columnas=%s | %.1f MB",
                nombre, len(df), df.shape[1], memory_mb(df))
    logger.info("Columnas: %s", list(df.columns))
    print(f"\n--- {nombre}: tipos ---")
    print(df.dtypes.to_string())
    print(f"\n--- {nombre}: muestra (5 filas) ---")
    print(df.head(5).to_string(index=False))


def explorar_fixtures():
    df = _cargar("fixtures")
    _resumen("FIXTURES", df)
    if df is None or df.empty:
        return
    print("\n--- Fixtures por liga ---")
    print(df["league_name"].value_counts().to_string())
    jugados = df.dropna(subset=["home_goals", "away_goals"])
    print(f"\nPartidos con resultado: {len(jugados)}/{len(df)}")


def explorar_standings():
    df = _cargar("standings")
    _resumen("STANDINGS", df)
    if df is None or df.empty:
        return
    if {"season_id", "team_id"}.issubset(df.columns):
        dup = df.groupby(["season_id", "team_id"]).size()
        print(f"\nMáx. filas para un mismo equipo/temporada: {dup.max()}")
        print("Si >1, hay varias etapas (regular + campeonato/descenso).")


def explorar_odds():
    df = _cargar("odds")
    _resumen("ODDS", df)
    if df is None or df.empty:
        return
    print("\n--- Odds: cardinalidades ---")
    print(f"Fixtures con odds : {df['fixture_id'].nunique()}")
    print(f"Mercados distintos: {df['market_description'].nunique()}")
    print(f"Bookmakers        : {df['bookmaker_id'].nunique()}")
    print(f"Filas promedio por fixture: {len(df) / max(df['fixture_id'].nunique(), 1):.0f}")
    print("\n--- Top 10 mercados por volumen ---")
    print(df["market_description"].value_counts().head(10).to_string())


def main():
    setup_logging(settings.LOG_DIR)
    logger.info("== EXPLORACIÓN DE DATASETS PARQUET ==")
    explorar_fixtures()
    explorar_standings()
    explorar_odds()
    logger.info("== FIN EXPLORACIÓN ==")


if __name__ == "__main__":
    main()
