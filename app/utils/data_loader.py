"""Carga de datasets mart: cacheo, manejo de errores, medición de tiempo de carga y validación de filtros."""
import time
from pathlib import Path

import pandas as pd
import streamlit as st

from utils.logger_config import get_app_logger

logger = get_app_logger()
MARTS_DIR = Path("data/parquet/marts")
LOAD_TIME_THRESHOLD_S = 3.0  # objetivo UX del slide 3.2.4


@st.cache_data
def load_mart(dataset_name: str) -> pd.DataFrame:
    """
    Carga un mart con manejo de errores; nunca propaga excepción a la UI.

    Parameters
    ----------
    dataset_name : str
        'fixtures_features' | 'odds_1x2' | 'market_gap' | 'standings_clean'

    Returns
    -------
    pd.DataFrame vacío si falla la lectura.
    """
    path_file = MARTS_DIR / f"{dataset_name}.parquet"
    path_dir = MARTS_DIR / dataset_name
    path = path_file if path_file.exists() else path_dir  # marts particionados son carpetas; los planos son archivo único
    start = time.time()
    try:
        df = pd.read_parquet(path)
    except FileNotFoundError:
        logger.error(f"Mart no encontrado: {path}")
        st.error(f"No se encontró '{dataset_name}'. Verifica que build_features.py se haya ejecutado.")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error al cargar {dataset_name}: {e}")
        st.error(f"Error al cargar '{dataset_name}'. Revisa app/logs/app.log.")
        return pd.DataFrame()

    elapsed = time.time() - start
    if elapsed > LOAD_TIME_THRESHOLD_S:
        logger.warning(f"Carga lenta: {dataset_name} tardó {elapsed:.2f}s (objetivo < {LOAD_TIME_THRESHOLD_S}s)")

    return df


def validate_filters(df: pd.DataFrame, **filters) -> pd.DataFrame:
    """
    Aplica filtros columna=valor (o columna=lista) y maneja resultado vacío sin excepción.

    Valores None o listas vacías se ignoran (equivale a "sin filtro").
    Si el resultado queda vacío, muestra advertencia en UI; la vista debe chequear `.empty` antes de graficar.
    """
    result = df.copy()
    for column, value in filters.items():
        if value is None or (isinstance(value, (list, tuple)) and len(value) == 0):
            continue
        if column not in result.columns:
            logger.warning(f"Filtro ignorado: columna '{column}' no existe en el dataset")
            continue
        mask = result[column].isin(value) if isinstance(value, (list, tuple)) else result[column] == value
        result = result[mask]

    if result.empty:
        st.warning("No hay datos para la combinación de filtros seleccionada. Ajusta los criterios.")

    return result