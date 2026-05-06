"""
Feature Store – Prepara el catálogo de features y datasets para ML.
Función pura, sin dependencias de Streamlit.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any
from config import Settings


def exportar_feature_store(
    df_silver: pd.DataFrame,
    gold_contract: pd.DataFrame,
    gold_edu: pd.DataFrame,
    gold_family: pd.DataFrame,
    settings: Settings,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Genera el catálogo de features, la matriz de correlación,
    el CSV consolidado de Gold y una muestra de Silver para ML.

    Retorna
    -------
    df_catalogo, corr_matrix, csv_gold, csv_ml
    """
    # --- Catálogo de features ---
    features_numericas = df_silver.select_dtypes(include=[np.number]).columns.tolist()
    features_categoricas = df_silver.select_dtypes(include=['object']).columns.tolist()

    catalogo = []
    for col in features_numericas:
        if col != settings.target_column:
            catalogo.append({
                'FEATURE': col,
                'TIPO': 'Numérica',
                'RANGO': f"{df_silver[col].min():.2f} - {df_silver[col].max():.2f}",
                'NULOS': df_silver[col].isnull().sum()
            })
    for col in features_categoricas:
        catalogo.append({
            'FEATURE': col,
            'TIPO': 'Categórica',
            'RANGO': f"{df_silver[col].nunique()} categorías únicas",
            'NULOS': df_silver[col].isnull().sum()
        })
    df_catalogo = pd.DataFrame(catalogo)

    # --- Matriz de correlación (solo numéricas, excluyendo el target) ---
    cols_corr = [c for c in features_numericas if c != settings.target_column]
    if cols_corr:
        corr_matrix = df_silver[cols_corr].corr()
    else:
        corr_matrix = pd.DataFrame()

    # --- CSV Gold consolidado (usando las etiquetas de settings) ---
    labels = settings.gold_metric_labels  # ("RIESGO_CONTRATO", "RIESGO_EDUCACION")
    csv_gold = pd.concat([
        gold_contract.assign(TIPO_METRICA=labels[0]),
        gold_edu.assign(TIPO_METRICA=labels[1]),
    ], ignore_index=True)

    # --- Muestra de Silver para ML (usando sample size y semilla de settings) ---
    csv_ml = df_silver.sample(
        n=min(settings.ml_sample_size, len(df_silver)),
        random_state=settings.ml_random_state,
    )

    return df_catalogo, corr_matrix, csv_gold, csv_ml