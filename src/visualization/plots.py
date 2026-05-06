import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Tuple

def _make_bar_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    scale_y: float = 1.0,           # por ejemplo, 100 para convertir a porcentaje
    title: str = '',
    xlabel: str = '',
    ylabel: str = '',
    color: str = 'steelblue',
    figsize: Tuple[int, int] = (5, 3),
    fontsize_title: int = 10,
    fontsize_labels: int = 8,
    rotation: int = 45,
    ylim_scale: float = 1.17,
    bar_label_offset: float = 0.5,
    bar_label_format: str = '{:.1f}%'
) -> plt.Figure:
    """
    Función privada para crear un gráfico de barras estándar para métricas Gold.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame de la capa Gold con las columnas x_col e y_col.
    x_col, y_col : str
        Nombres de las columnas para el eje X e Y.
    scale_y : float
        Factor de escala para los valores Y (ej. 100 para tasas en %).
    ...
    Returns
    -------
    matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    values = df[y_col] * scale_y
    bars = ax.bar(df[x_col], values, color=color)
    ax.set_title(title, fontsize=fontsize_title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis='x', rotation=rotation)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2,
                bar.get_height() + bar_label_offset,
                bar_label_format.format(val),
                ha='center', fontsize=fontsize_labels)

    # Límite Y robusto, usa np.nanmax para ignorar NaN
    max_val = np.nanmax(values) if not df.empty else 1.0
    if np.isnan(max_val) or max_val == 0:
        max_val = 1.0
    ax.set_ylim(0, max_val * ylim_scale)

    plt.tight_layout()
    return fig


# -------------------------------------------------------------------
# Fachadas públicas con valores por defecto alineados al dominio
# -------------------------------------------------------------------

def plot_bad_rate_by_contract(
    gold_contract: pd.DataFrame,
    x_col: str = 'TIPO_CONTRATO',
    y_col: str = 'TASA_MORA',
    title: str = 'Tasa de Morosidad por Tipo de Contrato',
    ylabel: str = 'Tasa de Mora (%)',
    color: str = 'steelblue',
    ylim_scale: float = 1.17,
    bar_label_offset: float = 0.5,
    bar_label_format: str = '{:.1f}%'
) -> plt.Figure:
    """Tasa de morosidad por tipo de contrato."""
    return _make_bar_chart(
        gold_contract,
        x_col=x_col,
        y_col=y_col,
        scale_y=100,
        title=title,
        ylabel=ylabel,
        color=color,
        ylim_scale=ylim_scale,
        bar_label_offset=bar_label_offset,
        bar_label_format=bar_label_format
    )


def plot_bad_rate_by_education(
    gold_edu: pd.DataFrame,
    x_col: str = 'NIVEL_EDUCATIVO',
    y_col: str = 'TASA_MORA',
    title: str = 'Tasa de Morosidad por Nivel Educativo',
    ylabel: str = 'Tasa de Mora (%)',
    color: str = 'darkorange',
    ylim_scale: float = 1.2,
    bar_label_offset: float = 0.5,
    bar_label_format: str = '{:.1f}%'
) -> plt.Figure:
    """Tasa de morosidad por nivel educativo."""
    return _make_bar_chart(
        gold_edu,
        x_col=x_col,
        y_col=y_col,
        scale_y=100,
        title=title,
        ylabel=ylabel,
        color=color,
        ylim_scale=ylim_scale,
        bar_label_offset=bar_label_offset,
        bar_label_format=bar_label_format
    )


def plot_income_ratio_by_family(
    gold_family: pd.DataFrame,
    x_col: str = 'ESTADO_CIVIL',
    y_col: str = 'RAZON_CREDITO_INGRESO_PROMEDIO',
    title: str = 'Razón Crédito/Ingreso Promedio por Estado Civil',
    ylabel: str = 'Razón Crédito/Ingreso',
    color: str = 'seagreen',
    ylim_scale: float = 1.2,
    bar_label_offset: float = 0.01,
    bar_label_format: str = '{:.2f}'
) -> plt.Figure:
    """Razón crédito/ingreso promedio por estado civil."""
    return _make_bar_chart(
        gold_family,
        x_col=x_col,
        y_col=y_col,
        scale_y=1,
        title=title,
        ylabel=ylabel,
        color=color,
        ylim_scale=ylim_scale,
        bar_label_offset=bar_label_offset,
        bar_label_format=bar_label_format
    )