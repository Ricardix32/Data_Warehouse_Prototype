import logging
import pandas as pd
from src.data.repository import DataRepository

logger = logging.getLogger(__name__)

def ingest_bronze(df: pd.DataFrame, repo: DataRepository) -> None:
    """
    Almacena el DataFrame crudo en la capa Bronze del repositorio.
    """
    repo.save_bronze(df)
    logger.info(f"Capa Bronze: {len(df)} registros ingeridos.")