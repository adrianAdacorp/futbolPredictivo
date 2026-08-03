"""Optimización de memoria: downcasting de tipos y reporte.

Punto 4 de la entrega: reducción de memoria por downcasting. La vectorización
se aplica en features.py (operaciones sobre columnas completas, sin bucles).
"""
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def memory_mb(df):
    """Memoria del DataFrame en MB (incluye objetos con deep=True)."""
    return df.memory_usage(deep=True).sum() / 1024 ** 2


def _downcast_int_series(s):
    """Reduce un entero al tipo más pequeño que lo contenga (soporta nullable)."""
    if s.isna().any():
        lo, hi = s.min(), s.max()
        for t in ("Int8", "Int16", "Int32"):
            info = np.iinfo(t.lower())
            if lo >= info.min and hi <= info.max:
                return s.astype(t)
        return s
    return pd.to_numeric(s, downcast="integer")


def downcast_df(df, category_threshold=0.5):
    """Downcast in place de enteros, flotantes y objetos de baja cardinalidad.

    - Enteros -> menor int/Int que los contenga.
    - Flotantes -> float32 cuando es seguro.
    - Texto con < category_threshold de valores únicos -> category.
    """
    before = memory_mb(df)

    for col in df.columns:
        s = df[col]
        if pd.api.types.is_integer_dtype(s):
            df[col] = _downcast_int_series(s)
        elif pd.api.types.is_float_dtype(s):
            df[col] = pd.to_numeric(s, downcast="float")
        elif isinstance(s.dtype, pd.CategoricalDtype):
            continue
        elif pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s):
            n = len(s)
            if n and s.nunique(dropna=False) / n < category_threshold:
                df[col] = s.astype("category")

    after = memory_mb(df)
    reduccion = 100 * (before - after) / before if before else 0
    logger.info("Downcast: %.2f MB -> %.2f MB (%.1f%% reducción)",
                before, after, reduccion)
    return df
