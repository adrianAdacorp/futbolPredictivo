"""Punto de entrada del pipeline de ingesta Sportmonks (Temas 1-2).

Ejemplos:
    python main.py --start 2025-07-15 --end 2026-05-20
    python main.py --start 2025-08-01 --end 2025-08-31 --leagues "Danish Superliga"
    python main.py --start 2025-08-01 --end 2025-08-31 --no-odds
"""
import argparse
import logging

from config import settings
from src.logger import setup_logging
from src.pipeline import run


def parse_args():
    parser = argparse.ArgumentParser(
        description="Ingesta de datos de fútbol Sportmonks v3 -> Parquet."
    )
    parser.add_argument("--start", required=True, help="Fecha inicial YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="Fecha final YYYY-MM-DD")
    parser.add_argument("--leagues", nargs="*",
                        help="Subconjunto de ligas (según config). Por defecto: todas.")
    parser.add_argument("--no-odds", action="store_true",
                        help="Desactiva la ingesta de cuotas (odds).")
    parser.add_argument("--odds-max", type=int, default=None,
                        help="Límite de fixtures para odds (control de cupo horario).")
    return parser.parse_args()


def main():
    args = parse_args()
    setup_logging(settings.LOG_DIR)
    log = logging.getLogger("main")

    if not settings.SPORTMONKS_TOKEN:
        log.error("SPORTMONKS_TOKEN no definido. Copia .env.example a .env "
                  "y coloca tu token.")
        raise SystemExit(1)

    leagues = None
    if args.leagues:
        leagues = {k: v for k, v in settings.LEAGUES.items() if k in args.leagues}
        missing = set(args.leagues) - set(leagues)
        if missing:
            log.warning("Ligas no reconocidas (ignoradas): %s", missing)

    summary = run(start=args.start, end=args.end, leagues=leagues,
                  with_odds=not args.no_odds, odds_max_fixtures=args.odds_max)
    log.info("Resumen final de ingesta: %s", summary)


if __name__ == "__main__":
    main()
