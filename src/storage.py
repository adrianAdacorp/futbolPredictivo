"""Persistencia en formato columnar Parquet (particionado)."""
import logging
import shutil
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)


def write_parquet(df, base_dir, dataset, partition_cols=None, overwrite=True):
    """Escribe un DataFrame como dataset Parquet.

    overwrite=True limpia el directorio del dataset antes de escribir, evitando
    la acumulación de duplicados entre corridas sucesivas (idempotencia).
    """
    if df is None or df.empty:
        logger.warning("Dataset '%s' vacío: no se escribe.", dataset)
        return None

    out_dir = Path(base_dir) / dataset
    if overwrite and out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if partition_cols:
        for col in partition_cols:
            df[col] = df[col].astype("string").fillna("UNKNOWN")

    table = pa.Table.from_pandas(df, preserve_index=False)

    if partition_cols:
        pq.write_to_dataset(table, root_path=str(out_dir),
                            partition_cols=partition_cols)
    else:
        pq.write_table(table, str(out_dir / f"{dataset}.parquet"))

    logger.info("Parquet escrito: %s (%s filas)", out_dir, len(df))
    return str(out_dir)
