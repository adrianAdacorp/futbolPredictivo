"""Pipeline de transformación (Tema 3): limpieza -> features -> validación ->
escalado -> almacenamiento optimizado.

Cubre los 4 puntos de la entrega:
  1. Feature engineering (features.py): variables derivadas, agregaciones, binning.
  2. Normalización/Estandarización (scaling.py): StandardScaler.
  3. Validación automatizada (schemas.py): Pandera.
  4. Optimización de memoria (optimize.py): downcasting + vectorización.

Uso:
    python build_features.py
    python build_features.py --scale minmax
"""
import argparse
import logging

import pandas as pd

from config import settings
from src.logger import setup_logging
from src.cleaning import clean_fixtures, clean_odds, clean_standings
from src.optimize import downcast_df, memory_mb
from src.features import (
    aggregate_1x2_odds, add_recent_form, build_fixture_features, build_market_gap,
)
from src.schemas import fixtures_features_schema, market_gap_schema, validate
from src.scaling import scale_features
from src.storage import write_parquet

logger = logging.getLogger("build_features")

MARTS_DIR = settings.PARQUET_DIR / "marts"


def _load(dataset):
    ruta = settings.PARQUET_DIR / dataset
    if not ruta.exists():
        raise FileNotFoundError(f"No existe {ruta}. Corre primero la ingesta (main.py).")
    df = pd.read_parquet(ruta)
    logger.info("Cargado '%s': %s filas | %.1f MB", dataset, len(df), memory_mb(df))
    return df


def run(scale_method="standard"):
    MARTS_DIR.mkdir(parents=True, exist_ok=True)

    # -- Carga --
    fixtures = _load("fixtures")
    odds = _load("odds")
    try:
        standings = _load("standings")
    except FileNotFoundError:
        standings = None

    # -- 1. Limpieza / deduplicación --
    fixtures = clean_fixtures(fixtures)
    odds = clean_odds(odds)
    if standings is not None:
        standings = clean_standings(standings)

    # -- 4. Optimización de memoria (downcasting sobre el dataset pesado) --
    logger.info("Optimizando memoria de odds (capa cruda optimizada)...")
    odds = downcast_df(odds)

    # -- 1. Feature engineering --
    fx_feat = build_fixture_features(fixtures)
    fx_feat = add_recent_form(fx_feat, window=5)
    fx_feat = downcast_df(fx_feat)

    odds_1x2 = aggregate_1x2_odds(odds)          # agregación (capa mart)
    gap = build_market_gap(fx_feat, odds_1x2)    # brecha vs. mercado

    # -- 3. Validación automatizada (Pandera) --
    fx_feat = validate(fx_feat, fixtures_features_schema, "fixtures_features")
    gap = validate(gap, market_gap_schema, "market_gap")

    # -- 2. Normalización / Estandarización --
    gap, _ = scale_features(gap, method=scale_method)
    gap = downcast_df(gap)

    # -- Persistencia de marts --
    write_parquet(fx_feat, MARTS_DIR, "fixtures_features",
                  partition_cols=["league_name"])
    write_parquet(odds_1x2, MARTS_DIR, "odds_1x2", partition_cols=None)
    write_parquet(gap, MARTS_DIR, "market_gap", partition_cols=["league_name"])
    if standings is not None:
        write_parquet(standings, MARTS_DIR, "standings_clean",
                      partition_cols=None)

    resumen = {
        "fixtures_features": len(fx_feat),
        "odds_1x2": len(odds_1x2),
        "market_gap": len(gap),
    }
    logger.info("== FIN TRANSFORMACIÓN == %s", resumen)
    return resumen


def main():
    parser = argparse.ArgumentParser(description="Tema 3: transformación y features.")
    parser.add_argument("--scale", choices=["standard", "minmax"],
                        default="standard", help="Método de escalado.")
    args = parser.parse_args()

    setup_logging(settings.LOG_DIR)
    run(scale_method=args.scale)


if __name__ == "__main__":
    main()
