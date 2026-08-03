"""Normalización / Estandarización (Punto 2).

Para el conjunto de features numéricas se aplica estandarización (z-score) con
StandardScaler, apropiada porque las variables están en escalas muy distintas
(goles 0-7, probabilidades 0-1, spreads pequeños). Se ofrece también MinMax.
"""
import logging

import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler

logger = logging.getLogger(__name__)

# Features numéricas candidatas a escalado (las que existan en el df).
NUMERIC_FEATURES = [
    "total_goals", "goal_diff", "home_form", "away_form",
    "imp_home", "imp_draw", "imp_away", "overround",
    "spread_home", "spread_draw", "spread_away", "market_surprise",
]


def scale_features(df, method="standard", columns=None):
    """Devuelve (df_con_columnas_escaladas, scaler).

    method: 'standard' (z-score) o 'minmax' (0-1).
    Añade columnas con sufijo _z (standard) o _norm (minmax).
    """
    cols = [c for c in (columns or NUMERIC_FEATURES) if c in df.columns]
    if not cols:
        logger.warning("No hay columnas numéricas para escalar.")
        return df, None

    subset = df[cols].astype("float64")
    # Imputación simple de faltantes con la media (necesario para el scaler).
    subset = subset.fillna(subset.mean())

    if method == "minmax":
        scaler, suffix = MinMaxScaler(), "_norm"
    else:
        scaler, suffix = StandardScaler(), "_z"

    scaled = scaler.fit_transform(subset)
    scaled_df = pd.DataFrame(scaled, columns=[c + suffix for c in cols],
                             index=df.index).astype("float32")

    logger.info("Escalado [%s] aplicado a %s columnas: %s",
                method, len(cols), cols)
    return pd.concat([df, scaled_df], axis=1), scaler
