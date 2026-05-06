import pandas as pd

def balance_silver(
    df_bronze: pd.DataFrame,
    df_silver: pd.DataFrame,
    income_column: str = 'AMT_INCOME_TOTAL',
    derived_features_names: list = []
) -> pd.DataFrame:
    """
    Retorna DataFrame con el balance de transformación Bronze -> Silver.
    """
    filas_bronze = len(df_bronze)
    filas_silver = len(df_silver)
    filas_eliminadas = filas_bronze - filas_silver

    cols_bronze = len(df_bronze.columns)
    cols_silver = len(df_silver.columns)

    ingresos_problematicos = 0
    if income_column in df_bronze.columns:
        ingresos_problematicos = (df_bronze[income_column].isnull().sum() +
                                  (df_bronze[income_column] == 0).sum())

    balance = pd.DataFrame({
        'MÉTRICA': ['Filas totales', 'Columnas totales', f'Ingresos imputados (nulos/cero) - {income_column}'],
        'VALOR_BRONZE': [filas_bronze, cols_bronze, ingresos_problematicos],
        'VALOR_SILVER': [filas_silver, cols_silver, 0],
        'VARIACIÓN': [f'-{filas_eliminadas} filas (outliers)',
                      f'+{cols_silver - cols_bronze} columnas derivadas',
                      f'{ingresos_problematicos} valores corregidos']
    })
    return balance

def compute_derived_stats(
    df_silver: pd.DataFrame,
    derived_features: tuple
) -> pd.DataFrame:
    """
    Calcula estadísticas para cada variable derivada según la configuración.
    derived_features es una tupla de diccionarios con 'name', 'type', 'expression', etc.
    """
    rows = []
    for feat in derived_features:
        col_name = feat['name']
        if col_name not in df_silver.columns:
            continue  # o añadir fila con todo N/A
        tipo = feat.get('type', 'numeric')
        formula = feat.get('expression', '')
        if tipo == 'numeric':
            min_val = df_silver[col_name].min()
            max_val = df_silver[col_name].max()
            media = df_silver[col_name].mean()
            mediana = df_silver[col_name].median()
            nulos = df_silver[col_name].isnull().sum()
        else:
            # Para binarias solo nulos
            min_val = max_val = media = mediana = None
            nulos = df_silver[col_name].isnull().sum()
        rows.append({
            'VARIABLE': col_name,
            'FÓRMULA': formula,
            'MIN': round(min_val, 4) if pd.notnull(min_val) else None,
            'MAX': round(max_val, 4) if pd.notnull(max_val) else None,
            'MEDIA': round(media, 4) if pd.notnull(media) else None,
            'MEDIANA': round(mediana, 4) if pd.notnull(mediana) else None,
            'NULOS_RESIDUALES': nulos
        })
    return pd.DataFrame(rows)

def trazabilidad_silver(
    df_bronze: pd.DataFrame,
    df_silver: pd.DataFrame,
    income_column: str = 'AMT_INCOME_TOTAL',
    derived_features: tuple = ()
) -> tuple:
    """
    Versión unificada que retorna (balance, derivadas_stats, filas_eliminadas).
    """
    balance = balance_silver(df_bronze, df_silver, income_column, derived_features)
    derivadas = compute_derived_stats(df_silver, derived_features)
    filas_eliminadas = len(df_bronze) - len(df_silver)
    return balance, derivadas, filas_eliminadas