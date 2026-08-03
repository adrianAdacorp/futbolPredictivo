"""Limpieza: deduplicación e integración de los datasets crudos.

Resuelve los duplicados detectados en la exploración (escritura incremental)
y deja los datasets listos para el feature engineering.
"""
import logging

logger = logging.getLogger(__name__)


def deduplicate(df, subset, name):
    """Elimina duplicados por clave y reporta el efecto."""
    before = len(df)
    df = df.drop_duplicates(subset=subset).reset_index(drop=True)
    removed = before - len(df)
    logger.info("Dedup [%s]: %s -> %s filas (-%s)", name, before, len(df), removed)
    return df


def clean_fixtures(df):
    df = deduplicate(df, subset=["fixture_id"], name="fixtures")
    # Solo partidos con resultado (state finalizado) para análisis.
    df = df.dropna(subset=["home_goals", "away_goals"]).reset_index(drop=True)
    logger.info("Fixtures con resultado: %s", len(df))
    return df


def clean_standings(df):
    # Un equipo puede aparecer en varias etapas (regular + campeonato/descenso).
    # La clave real incluye la posición para no colapsar etapas distintas.
    df = deduplicate(df, subset=["season_id", "team_id", "position", "points"],
                     name="standings")
    return df


def clean_odds(df):
    df = deduplicate(df, subset=["odd_id"], name="odds")
    return df
