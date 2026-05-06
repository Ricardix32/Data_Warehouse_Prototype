# src/etl/gold.py
import time
import pandas as pd

def transform_gold(df_silver: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    start = time.time()

    # Tasa de mora por contrato
    bad_rate_contract = df_silver.groupby('NAME_CONTRACT_TYPE')['TARGET'].agg(['mean', 'count']).reset_index()
    bad_rate_contract.columns = ['TIPO_CONTRATO', 'TASA_MORA', 'TOTAL_CLIENTES']
    bad_rate_contract['TASA_MORA'] = bad_rate_contract['TASA_MORA'].round(4)

    # Tasa de mora por nivel educativo
    bad_rate_edu = df_silver.groupby('NAME_EDUCATION_TYPE')['TARGET'].agg(['mean', 'count']).reset_index()
    bad_rate_edu.columns = ['NIVEL_EDUCATIVO', 'TASA_MORA', 'TOTAL_CLIENTES']
    bad_rate_edu['TASA_MORA'] = bad_rate_edu['TASA_MORA'].round(4)

    # Razón crédito/ingreso por estado civil
    ratio_family = df_silver.groupby('NAME_FAMILY_STATUS')['CREDIT_TO_INCOME_RATIO'].mean().reset_index()
    ratio_family.columns = ['ESTADO_CIVIL', 'RAZON_CREDITO_INGRESO_PROMEDIO']

    elapsed = time.time() - start
    metadata = {
        "time_seconds": elapsed,
        "aggregations": [
            "Bad rate por tipo de contrato (gold_contract)",
            "Bad rate por nivel educativo (gold_edu)",
            "Razón crédito/ingreso promedio por estado civil (gold_family)"
        ]
    }
    return bad_rate_contract, bad_rate_edu, ratio_family, metadata