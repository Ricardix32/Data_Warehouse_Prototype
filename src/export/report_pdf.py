"""
Generador de reporte PDF profesional.
Utiliza las funciones puras de auditoría y visualización,
y toda la configuración desde Settings.
"""

from fpdf import FPDF
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from typing import Tuple

from config.settings import Settings
from src.audit.quality import auditar_calidad_bronze
from src.audit.lineage import trazabilidad_silver
from src.visualization.plots import (
    plot_bad_rate_by_contract,
    plot_bad_rate_by_education,
    plot_income_ratio_by_family,
)


def generar_reporte_pdf(
    df_bronze: pd.DataFrame,
    df_silver: pd.DataFrame,
    gold_contract: pd.DataFrame,
    gold_edu: pd.DataFrame,
    gold_family: pd.DataFrame,
    settings: Settings,
) -> bytes:
    """
    Construye el reporte PDF integrando auditoría, trazabilidad y métricas Gold.
    Devuelve el contenido binario del PDF listo para descargar.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=settings.pdf_margin)
    pdf.add_page()

    # ==================== PORTADA ====================
    pdf.set_font("Arial", "B", settings.pdf_font_size_h1)
    pdf.cell(0, 10, settings.report_title, ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "", settings.pdf_font_size_h3)
    pdf.cell(0, 8, "Proyecto de Tesis: Arquitectura de Data Warehouse y analítica predictiva", ln=True, align="C")
    pdf.cell(0, 8, "para la evaluación de riesgo crediticio en instituciones microfinancieras", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "I", settings.pdf_font_size_body)
    pdf.cell(0, 8, f"Autores: {settings.report_authors_full}", ln=True, align="C")
    pdf.cell(0, 8, f"Asesor: {settings.report_advisor}", ln=True, align="C")
    pdf.cell(0, 8, f"Fecha: {pd.Timestamp.now().strftime(settings.pdf_date_format)}", ln=True, align="C")
    pdf.ln(10)

    # ==================== SECCIÓN 1: AUDITORÍA BRONZE ====================
    pdf.set_font("Arial", "B", settings.pdf_font_size_h2)
    pdf.cell(0, 10, settings.pdf_section_titles[0] if hasattr(settings, 'pdf_section_titles') else "1. Auditoría de Datos Crudos (Bronze)", ln=True)
    pdf.ln(3)

    resultado_aud, num_criticas, pct_dup, memoria_mb, total_cols = auditar_calidad_bronze(
        df_bronze,
        id_column=settings.id_column,
        null_threshold_critical=settings.null_threshold_critical,
        null_threshold_moderate=settings.null_threshold_moderate,
    )

    pdf.set_font("Arial", "", settings.pdf_font_size_body)
    pdf.cell(0, 7, f"Total de columnas: {total_cols}  |  Columnas críticas: {num_criticas}  |  Duplicados: {pct_dup:.2f}%  |  Memoria: {memoria_mb:.2f} MB", ln=True)
    pdf.ln(3)

    if not resultado_aud.empty:
        # Encabezados de la tabla de auditoría
        headers_aud = [h.title() for h in settings.PDF_COLUMNS_AUDIT]
        pdf.set_font("Arial", "B", settings.pdf_font_size_table_header)
        for i, h in enumerate(headers_aud):
            width = getattr(settings, f"pdf_cell_w_col") if i == 0 else (
                settings.pdf_cell_w_val_small if i == 1 else settings.pdf_cell_w_class
            )
            pdf.cell(width, 7, h, border=1)
        pdf.ln()

        pdf.set_font("Arial", "", settings.pdf_font_size_table_row)
        for _, row in resultado_aud.head(settings.audit_head_limit).iterrows():
            pdf.cell(settings.pdf_cell_w_col, 6, str(row['COLUMNA']), border=1)
            pdf.cell(settings.pdf_cell_w_val_small, 6, f"{row['%_NULOS']:.2f}", border=1)
            pdf.cell(settings.pdf_cell_w_class, 6, row['CLASIFICACION'], border=1)
            pdf.ln()

    pdf.ln(5)
    pdf.set_fill_color(*settings.plot_bg_color_analysis)
    pdf.set_font("Arial", "I", settings.pdf_font_size_body)
    pdf.multi_cell(0, 6, settings.analysis_audit_bronze, fill=True)
    pdf.ln(5)

    # ==================== SECCIÓN 2: TRAZABILIDAD SILVER ====================
    pdf.set_font("Arial", "B", settings.pdf_font_size_h2)
    pdf.cell(0, 10, "2. Transformaciones y Calidad (Silver)", ln=True)
    pdf.ln(3)

    balance, derivadas, _ = trazabilidad_silver(
        df_bronze,
        df_silver,
        income_column=settings.income_column,
        derived_features=settings.derived_features,
    )

    # Tabla de balance
    headers_bal = [h.title() for h in settings.PDF_COLUMNS_BALANCE]
    pdf.set_font("Arial", "B", settings.pdf_font_size_table_header)
    widths_bal = [settings.pdf_cell_w_metric, settings.pdf_cell_w_val_small, settings.pdf_cell_w_val_small, settings.pdf_cell_w_class]
    for i, h in enumerate(headers_bal):
        pdf.cell(widths_bal[i], 7, h, border=1)
    pdf.ln()
    pdf.set_font("Arial", "", settings.pdf_font_size_table_row)
    for _, row in balance.iterrows():
        pdf.cell(widths_bal[0], 6, str(row[settings.PDF_COLUMNS_BALANCE[0]]), border=1)
        pdf.cell(widths_bal[1], 6, str(row[settings.PDF_COLUMNS_BALANCE[1]]), border=1)
        pdf.cell(widths_bal[2], 6, str(row[settings.PDF_COLUMNS_BALANCE[2]]), border=1)
        pdf.cell(widths_bal[3], 6, str(row[settings.PDF_COLUMNS_BALANCE[3]]), border=1)
        pdf.ln()

    pdf.ln(3)
    # Tabla de variables derivadas
    pdf.set_font("Arial", "B", settings.pdf_font_size_h3)
    pdf.cell(0, 7, "Variables Derivadas", ln=True)
    headers_der = [h.title() for h in settings.PDF_COLUMNS_DERIVED]
    pdf.set_font("Arial", "B", settings.pdf_font_size_caption)
    # Tabla de variables derivadas
    headers_der = [h.title() for h in settings.PDF_COLUMNS_DERIVED]
    widths_der = [
        settings.pdf_cell_w_var,
        settings.pdf_cell_w_formula,
        settings.pdf_cell_w_stat,
        settings.pdf_cell_w_stat,
        settings.pdf_cell_w_res_null,
    ]
    # Imprimir encabezados
    pdf.set_font("Arial", "B", settings.pdf_font_size_caption)
    for i, h in enumerate(headers_der):
        pdf.cell(widths_der[i], 6, h, border=1)
    pdf.ln()
    
    # Cuerpo de la tabla usando solo la configuración
    pdf.set_font("Arial", "", settings.pdf_font_size_caption)
    cols = settings.PDF_COLUMNS_DERIVED  # tupla con los nombres reales de las columnas
    for _, row in derivadas.iterrows():
        for i, col in enumerate(cols):
            value = row[col]
            # Formato especial para columnas numéricas (MEDIA, MEDIANA)
            if col in ('MEDIA', 'MEDIANA'):
                text = f"{value:.4f}" if pd.notna(value) else ""
            elif col == cols[-1]:  # última columna (NULOS_RESIDUALES)
                text = str(value) if pd.notna(value) else ""
            else:
                text = str(value)
            pdf.cell(widths_der[i], 5, text, border=1)
        pdf.ln()

    pdf.ln(5)
    pdf.set_fill_color(*settings.plot_bg_color_analysis)
    pdf.set_font("Arial", "I", settings.pdf_font_size_body)
    pdf.multi_cell(0, 6, settings.analysis_transformation_silver, fill=True)
    pdf.ln(5)

    # ==================== SECCIÓN 3: MÉTRICAS DE RIESGO (GOLD) ====================
    pdf.set_font("Arial", "B", settings.pdf_font_size_h2)
    pdf.cell(0, 10, "3. Métricas de Riesgo (Gold)", ln=True)
    pdf.ln(3)

    # -- Gráfico 1: Morosidad por contrato --
    fig1 = plot_bad_rate_by_contract(
        gold_contract,
        color=settings.plot_color_primary,
        ylim_scale=settings.plot_yscale_factor_contract,
        bar_label_offset=settings.plot_label_offset_standard,
        bar_label_format=settings.fmt_pct_one_decimal,
        title='Tasa de Morosidad por Tipo de Contrato',
    )
    img_buf = BytesIO()
    fig1.savefig(img_buf, format='PNG', dpi=settings.plot_dpi)
    plt.close(fig1)
    img_buf.seek(0)
    pdf.image(img_buf, x=10, w=pdf.w - 20)
    pdf.ln(2)
    
    # Tabla de datos (contrato)
    tab_headers_contract = [h.title() for h in settings.PDF_COLUMNS_RISK_CONTRACT]
    pdf.set_font("Arial", "B", settings.pdf_font_size_table_header)
    pdf.cell(settings.pdf_cell_w_var, 7, tab_headers_contract[0], border=1)
    pdf.cell(settings.pdf_cell_w_val_small, 7, tab_headers_contract[1], border=1)
    pdf.cell(settings.pdf_cell_w_val_small, 7, tab_headers_contract[2], border=1)
    pdf.ln()
    pdf.set_font("Arial", "", settings.pdf_font_size_table_row)
    for _, row in gold_contract.iterrows():
        pdf.cell(settings.pdf_cell_w_var, 6, str(row[settings.PDF_COLUMNS_RISK_CONTRACT[0]]), border=1)
        pdf.cell(settings.pdf_cell_w_val_small, 6, f"{row[settings.PDF_COLUMNS_RISK_CONTRACT[1]]:.2%}", border=1)
        pdf.cell(settings.pdf_cell_w_val_small, 6, str(row[settings.PDF_COLUMNS_RISK_CONTRACT[2]]), border=1)
        pdf.ln()
    pdf.ln(4)

    pdf.set_fill_color(*settings.plot_bg_color_analysis)
    pdf.set_font("Arial", "I", settings.pdf_font_size_body)
    pdf.multi_cell(0, 6, settings.analysis_risk_contract_gold, fill=True)
    pdf.ln(5)

    # -- Gráfico 2: Morosidad por educación --
    fig2 = plot_bad_rate_by_education(
        gold_edu,
        color=settings.plot_color_secondary,
        ylim_scale=settings.plot_yscale_factor_general,
        bar_label_offset=settings.plot_label_offset_standard,
        bar_label_format=settings.fmt_pct_one_decimal,
        title='Tasa de Morosidad por Nivel Educativo',
    )
    img_buf2 = BytesIO()
    fig2.savefig(img_buf2, format='PNG', dpi=settings.plot_dpi)
    plt.close(fig2)
    img_buf2.seek(0)
    pdf.image(img_buf2, x=10, w=pdf.w - 20)
    pdf.ln(2)

    tab_headers_edu = [h.title() for h in settings.PDF_COLUMNS_RISK_EDUCATION]
    pdf.set_font("Arial", "B", settings.pdf_font_size_table_header)
    pdf.cell(settings.pdf_cell_w_var, 7, tab_headers_edu[0], border=1)
    pdf.cell(settings.pdf_cell_w_val_small, 7, tab_headers_edu[1], border=1)
    pdf.cell(settings.pdf_cell_w_val_small, 7, tab_headers_edu[2], border=1)
    pdf.ln()
    pdf.set_font("Arial", "", settings.pdf_font_size_table_row)
    for _, row in gold_edu.iterrows():
        pdf.cell(settings.pdf_cell_w_var, 6, str(row[settings.PDF_COLUMNS_RISK_EDUCATION[0]]), border=1)
        pdf.cell(settings.pdf_cell_w_val_small, 6, f"{row[settings.PDF_COLUMNS_RISK_EDUCATION[1]]:.2%}", border=1)
        pdf.cell(settings.pdf_cell_w_val_small, 6, str(row[settings.PDF_COLUMNS_RISK_EDUCATION[2]]), border=1)
        pdf.ln()
    pdf.ln(4)

    pdf.set_fill_color(*settings.plot_bg_color_analysis)
    pdf.set_font("Arial", "I", settings.pdf_font_size_body)
    pdf.multi_cell(0, 6, settings.analysis_risk_education_gold, fill=True)
    pdf.ln(5)

    # -- Gráfico 3: Endeudamiento por estado civil --
    fig3 = plot_income_ratio_by_family(
        gold_family,
        color=settings.plot_color_tertiary,
        ylim_scale=settings.plot_yscale_factor_general,
        bar_label_offset=settings.plot_label_offset_ratio,
        bar_label_format=settings.fmt_decimal_two_places,
        title='Razón Crédito/Ingreso Promedio por Estado Civil',
    )
    img_buf3 = BytesIO()
    fig3.savefig(img_buf3, format='PNG', dpi=settings.plot_dpi)
    plt.close(fig3)
    img_buf3.seek(0)
    pdf.image(img_buf3, x=10, w=pdf.w - 20)
    pdf.ln(2)

    tab_headers_fam = [h.title() for h in settings.PDF_COLUMNS_RISK_FAMILY]
    pdf.set_font("Arial", "B", settings.pdf_font_size_table_header)
    pdf.cell(settings.pdf_cell_w_var, 7, tab_headers_fam[0], border=1)
    pdf.cell(settings.pdf_cell_w_formula, 7, tab_headers_fam[1], border=1)
    pdf.ln()
    pdf.set_font("Arial", "", settings.pdf_font_size_table_row)
    for _, row in gold_family.iterrows():
        pdf.cell(settings.pdf_cell_w_var, 6, str(row[settings.PDF_COLUMNS_RISK_FAMILY[0]]), border=1)
        pdf.cell(settings.pdf_cell_w_formula, 6, f"{row[settings.PDF_COLUMNS_RISK_FAMILY[1]]:.2f}", border=1)
        pdf.ln()
    pdf.ln(4)

    pdf.set_fill_color(*settings.plot_bg_color_analysis)
    pdf.set_font("Arial", "I", settings.pdf_font_size_body)
    pdf.multi_cell(0, 6, settings.analysis_risk_family_gold, fill=True)
    pdf.ln(10)

    # ==================== PIE DE PÁGINA ====================
    pdf.set_font("Arial", "I", settings.pdf_font_size_caption)
    pdf.cell(0, 8, settings.pdf_footer_text, ln=True, align="C")

    return bytes(pdf.output(dest='S'))