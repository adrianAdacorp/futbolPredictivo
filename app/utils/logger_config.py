"""Configuración de logging para la Data App (independiente del logger del pipeline de ingesta en src/)."""
import logging
from pathlib import Path

LOG_DIR = Path("app/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_app_logger(name: str = "data_app") -> logging.Logger:
    """Retorna un logger que escribe en app/logs/app.log, evitando duplicar handlers en cada re-run de Streamlit."""
    logger = logging.getLogger(name)
    if not logger.handlers:  # sin este guard, cada re-run agrega un handler nuevo y duplica logs
        handler = logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger