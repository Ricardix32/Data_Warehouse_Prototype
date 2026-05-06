# src/etl/silver.py
import time
import pandas as pd
import numpy as np

def transform_silver(
    df_bronze: pd.DataFrame,
    silver_columns: tuple = None  # opcional, para no romper el orquestador
) -> tuple[pd.DataFrame, dict]:
    if silver_columns is None:
        # fallback por si se llama sin el parámetro (mantiene compatibilidad)
        silver_columns = (
            "SK_ID_CURR", "TARGET", "NAME_CONTRACT_TYPE", "CODE_GENDER",
            "AMT_CREDIT", "AMT_INCOME_TOTAL", "AMT_ANNUITY",
            "CREDIT_TO_INCOME_RATIO", "ANNUITY_INCOME_RATIO",
            "IS_EMPLOYED", "NAME_EDUCATION_TYPE", "NAME_FAMILY_STATUS",
            "CNT_CHILDREN",
        )
    start = time.time()
    df = df_bronze.copy()

    # 1. Imputaciones y tratamiento (igual que en app.py)
    df['AMT_INCOME_TOTAL'] = df['AMT_INCOME_TOTAL'].replace(0, np.nan)
    mediana_income = df['AMT_INCOME_TOTAL'].median()
    df['AMT_INCOME_TOTAL'] = df['AMT_INCOME_TOTAL'].fillna(mediana_income)

    for col in ['AMT_CREDIT', 'AMT_ANNUITY']:
        df[col] = df[col].fillna(df[col].median())

    df['IS_EMPLOYED'] = (df['DAYS_EMPLOYED'] < 0).astype(int)

    # 2. Ratios
    df['CREDIT_TO_INCOME_RATIO'] = df['AMT_CREDIT'] / df['AMT_INCOME_TOTAL']
    df['ANNUITY_INCOME_RATIO'] = df['AMT_ANNUITY'] / df['AMT_INCOME_TOTAL']

    # 3. Filtrado de outliers
    for col in ['CREDIT_TO_INCOME_RATIO', 'ANNUITY_INCOME_RATIO']:
        media = df[col].mean()
        desv = df[col].std()
        df = df[(df[col] >= media - 3*desv) & (df[col] <= media + 3*desv)]

    # 4. Selección de columnas
    columnas_silver = [
        'SK_ID_CURR', 'TARGET', 'NAME_CONTRACT_TYPE', 'CODE_GENDER',
        'AMT_CREDIT', 'AMT_INCOME_TOTAL', 'AMT_ANNUITY',
        'CREDIT_TO_INCOME_RATIO', 'ANNUITY_INCOME_RATIO',
        'IS_EMPLOYED', 'NAME_EDUCATION_TYPE', 'NAME_FAMILY_STATUS',
        'CNT_CHILDREN'
    ]
    df_silver = df[list(silver_columns)].copy()
    elapsed = time.time() - start
    metadata = {
        "rows_before": len(df_bronze),
        "rows_after": len(df_silver),
        "columns_before": len(df_bronze.columns),
        "columns_after": len(df_silver.columns),
        "time_seconds": elapsed,
        "rules_applied": [
            "Imputación de AMT_INCOME_TOTAL con mediana",
            "Imputación de AMT_CREDIT y AMT_ANNUITY con mediana",
            "Creación de IS_EMPLOYED a partir de DAYS_EMPLOYED",
            "Creación de CREDIT_TO_INCOME_RATIO y ANNUITY_INCOME_RATIO",
            "Filtrado de outliers (3 desviaciones estándar)",
            "Selección de columnas para análisis de riesgo"
        ]
    }
    return df_silver, metadata