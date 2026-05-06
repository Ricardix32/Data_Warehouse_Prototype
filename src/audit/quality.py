import pandas as pd
import numpy as np

def auditar_calidad_bronze(
    df: pd.DataFrame,
    id_column: str = 'SK_ID_CURR',
    null_threshold_critical: float = 50.0,
    null_threshold_moderate: float = 20.0
) -> tuple:
    """
    Auditoría de calidad del dataset crudo (capa Bronze).
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame original.
    id_column : str
        Nombre de la columna de identificación única para detectar duplicados.
    null_threshold_critical : float
        Umbral (%) por encima del cual la columna se considera crítica.
    null_threshold_moderate : float
        Umbral (%) inferior para rango moderado.
    
    Returns
    -------
    tuple: (resultado, num_criticas, pct_duplicados, memoria_mb, total_cols)
    """
    total_cols = len(df.columns)
    null_percent = (df.isnull().sum() / len(df)) * 100

    # Clasificación usando umbrales parametrizados
    criticas = null_percent[null_percent > null_threshold_critical].reset_index()
    criticas.columns = ['COLUMNA', '%_NULOS']
    criticas['CLASIFICACION'] = f'CRÍTICA (>{null_threshold_critical}%)'

    moderadas = null_percent[(null_percent >= null_threshold_moderate) & 
                             (null_percent <= null_threshold_critical)].reset_index()
    moderadas.columns = ['COLUMNA', '%_NULOS']
    moderadas['CLASIFICACION'] = f'MODERADA ({null_threshold_moderate}-{null_threshold_critical}%)'

    resultado = pd.concat([criticas, moderadas], ignore_index=True)
    resultado['%_NULOS'] = resultado['%_NULOS'].round(2)

    # Duplicados
    if id_column in df.columns:
        duplicados = df[id_column].duplicated().sum()
        pct_duplicados = (duplicados / len(df)) * 100
    else:
        duplicados = 0
        pct_duplicados = 0.0

    memoria_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)

    return resultado, len(criticas), pct_duplicados, memoria_mb, total_cols