# src/etl/orchestrator.py
import logging
import pandas as pd
from typing import Dict, Any
from config import Settings
from src.data.loader import load_raw_dataset
from src.data.repository import DataRepository, SQLiteRepository
from bronze import ingest_bronze
from silver import transform_silver
from gold import transform_gold


logger = logging.getLogger(__name__)

def run_etl_pipeline(settings: Settings) -> Dict[str, Any]:
    """
    Ejecuta el pipeline ETL completo (Bronze → Silver → Gold) y retorna
    todos los DataFrames y metadatos.
    """
    # 1. Cargar dataset crudo
    logger.info("Cargando dataset crudo...")
    df_bronze = load_raw_dataset(settings)

    # 2. Inicializar repositorio
    repo = SQLiteRepository(settings.db_path)

    # 3. Capa Bronze (solo almacenar)
    ingest_bronze(df_bronze, repo)
    logger.info("Capa Bronze guardada.")

    # 4. Capa Silver
    logger.info("Transformando a Silver...")
    df_silver, meta_silver = transform_silver(df_bronze, settings.silver_columns)
    repo.save_silver(df_silver)
    logger.info("Capa Silver guardada.")

    # 5. Capa Gold
    logger.info("Transformando a Gold...")
    gold_contract, gold_edu, gold_family, meta_gold = transform_gold(df_silver)
    repo.save_gold_tables(gold_contract, gold_edu, gold_family)
    logger.info("Capa Gold guardada.")

    # 6. Retornar todo para la UI y reportes
    results = {
        "bronze_df": df_bronze,
        "silver_df": df_silver,
        "gold_contract": gold_contract,
        "gold_edu": gold_edu,
        "gold_family": gold_family,
        "meta_silver": meta_silver,
        "meta_gold": meta_gold,
    }
    return results