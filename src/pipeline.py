"""Orquestación del pipeline de ingesta: API -> normalización -> Parquet."""
import logging

import pandas as pd

from config import settings
from src.client import SportmonksClient
from src.endpoints import (
    fetch_fixtures_between,
    fetch_odds_by_fixture,
    fetch_standings_by_season,
)
from src.normalize import normalize_fixtures, normalize_odds, normalize_standings
from src.storage import write_parquet

logger = logging.getLogger(__name__)


def _build_client():
    return SportmonksClient(
        token=settings.SPORTMONKS_TOKEN,
        base_url=settings.BASE_URL,
        timeout=settings.REQUEST_TIMEOUT,
        max_retries=settings.MAX_RETRIES,
        backoff_factor=settings.BACKOFF_FACTOR,
        rate_limit_buffer=settings.RATE_LIMIT_BUFFER,
        per_page=settings.PER_PAGE,
    )


def ingest_fixtures(client, leagues, start, end):
    """Ingesta de fixtures por liga en un rango de fechas."""
    frames, summary = [], {}
    for name, league_id in leagues.items():
        logger.info("Fixtures | liga=%s (id=%s) | %s -> %s",
                    name, league_id, start, end)
        records = fetch_fixtures_between(client, start, end, league_id=league_id)
        df = normalize_fixtures(records)
        if not df.empty:
            df["league_name"] = df["league_name"].fillna(name)
        logger.info("  -> %s fixtures normalizados", len(df))
        summary[name] = len(df)
        frames.append(df)

    fixtures_df = (pd.concat(frames, ignore_index=True)
                   if frames else pd.DataFrame())
    write_parquet(fixtures_df, settings.PARQUET_DIR, "fixtures",
                  partition_cols=["league_name"])
    return summary, fixtures_df


def ingest_standings(client, seasons):
    """Ingesta de tablas de posiciones por temporada."""
    if not seasons:
        logger.info("Sin season_id configurados: se omite standings.")
        return {}

    frames, summary = [], {}
    for name, season_id in seasons.items():
        logger.info("Standings | liga=%s (season_id=%s)", name, season_id)
        records = fetch_standings_by_season(client, season_id)
        df = normalize_standings(records)
        logger.info("  -> %s filas de standings", len(df))
        summary[name] = len(df)
        frames.append(df)

    standings_df = (pd.concat(frames, ignore_index=True)
                    if frames else pd.DataFrame())
    write_parquet(standings_df, settings.PARQUET_DIR, "standings",
                  partition_cols=["season_id"])
    return summary


def ingest_odds(client, fixtures_df, max_fixtures=None):
    """Ingesta de cuotas pre-partido por fixture (todos los mercados/bookmakers)."""
    if fixtures_df is None or fixtures_df.empty:
        logger.info("Sin fixtures: se omite odds.")
        return {}

    subset = (fixtures_df[["fixture_id", "league_name"]]
              .dropna(subset=["fixture_id"]))
    if max_fixtures:
        subset = subset.head(max_fixtures)

    frames, total = [], len(subset)
    logger.info("Odds | procesando %s fixtures", total)
    for i, (_, row) in enumerate(subset.iterrows(), start=1):
        fixture_id = int(row["fixture_id"])
        league_name = row["league_name"]
        records = fetch_odds_by_fixture(client, fixture_id)
        df = normalize_odds(records, fixture_id=fixture_id,
                            league_name=league_name)
        if not df.empty:
            frames.append(df)
        if i % 25 == 0 or i == total:
            logger.info("  Odds | %s/%s fixtures", i, total)

    odds_df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    write_parquet(odds_df, settings.PARQUET_DIR, "odds",
                  partition_cols=["league_name"])
    return {"odds_rows": len(odds_df), "fixtures_con_odds": len(frames)}


def run(start, end, leagues=None, seasons=None, with_odds=True,
        odds_max_fixtures=None):
    """Ejecuta el pipeline completo y devuelve un resumen de conteos."""
    client = _build_client()
    leagues = leagues if leagues is not None else settings.LEAGUES
    seasons = seasons if seasons is not None else settings.SEASONS

    logger.info("== INICIO INGESTA == ligas=%s | %s a %s",
                list(leagues), start, end)

    fixtures_summary, fixtures_df = ingest_fixtures(client, leagues, start, end)
    result = {
        "fixtures": fixtures_summary,
        "standings": ingest_standings(client, seasons),
    }
    if with_odds:
        result["odds"] = ingest_odds(client, fixtures_df,
                                     max_fixtures=odds_max_fixtures)
    else:
        logger.info("Odds desactivado (--no-odds).")

    logger.info("== FIN INGESTA == %s", result)
    return result
