"""Obtiene el season_id vigente de cada liga configurada.

Uso (desde la raíz):
    python scripts/obtener_seasons.py
"""
import logging

import _bootstrap  # noqa: F401
import requests

from config import settings
from src.logger import setup_logging

logger = logging.getLogger("seasons")


def _current_season(payload):
    data = payload.get("data") or {}
    season = (data.get("currentseason")
              or data.get("current_season")
              or data.get("currentSeason")
              or {})
    if isinstance(season, list):
        season = season[0] if season else {}
    return season.get("id"), season.get("name")


def main():
    setup_logging(settings.LOG_DIR)
    token = settings.SPORTMONKS_TOKEN
    if not token:
        logger.error("SPORTMONKS_TOKEN vacío. Configura .env.")
        raise SystemExit(1)

    headers = {"Authorization": token, "Accept": "application/json"}
    resultado = {}

    logger.info("== OBTENER SEASONS VIGENTES ==")
    for name, league_id in settings.LEAGUES.items():
        url = f"{settings.BASE_URL.rstrip('/')}/leagues/{league_id}"
        try:
            resp = requests.get(url, headers=headers,
                                params={"include": "currentSeason"}, timeout=30)
        except requests.RequestException as exc:
            logger.error("%-25s | ERROR DE RED: %s", name, exc)
            continue

        if resp.status_code != 200:
            logger.warning("%-25s | HTTP %s", name, resp.status_code)
            continue

        season_id, season_name = _current_season(resp.json())
        if season_id:
            resultado[name] = season_id
            logger.info("%-25s | season_id=%s | %s", name, season_id, season_name)
        else:
            logger.warning("%-25s | sin currentSeason en la respuesta", name)

    logger.info("-- Copia este bloque en config/settings.py --")
    print("\nSEASONS = {")
    for name, season_id in resultado.items():
        print(f'    "{name}": {season_id},')
    print("}\n")


if __name__ == "__main__":
    main()
