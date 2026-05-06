from dataclasses import dataclass, field
from typing import Tuple, Dict, Any
import os

def _default_derived_features() -> tuple:
    return (
        {
            "name": "CREDIT_TO_INCOME_RATIO",
            "expression": "AMT_CREDIT / AMT_INCOME_TOTAL",
            "source_columns": ["AMT_CREDIT", "AMT_INCOME_TOTAL"],
            "type": "numeric"
        },
        {
            "name": "ANNUITY_INCOME_RATIO",
            "expression": "AMT_ANNUITY / AMT_INCOME_TOTAL",
            "source_columns": ["AMT_ANNUITY", "AMT_INCOME_TOTAL"],
            "type": "numeric"
        },
        {
            "name": "IS_EMPLOYED",
            "expression": "DAYS_EMPLOYED < 0 -> 1 (empleado)",
            "source_columns": ["DAYS_EMPLOYED"],
            "type": "binary"
        }
    )

@dataclass(frozen=True)
class Settings: 
    """
    Contenedor de configuración inmutable (Single Source of Truth).
    El uso de frozen=True garantiza la integridad del pipeline ETL durante su ejecución.
    """
    # --- Configuración de Infraestructura y Datos ---
    gdrive_url: str = ""
    csv_filename: str = "application_train.csv"
    db_path: str = "credit_warehouse.db"
    
    # --- Umbrales de Calidad de Datos (Data Governance) ---
    null_threshold_moderate: float = 20.0
    null_threshold_critical: float = 50.0
    
    # --- Definición de Features ---
    derived_features: Tuple[Dict[str, Any], ...] = field( 
        default_factory=_default_derived_features
    )
    target_column: str = 'TARGET'
    ml_sample_size: int = 1000
    ml_random_state: int = 42
    gold_metric_labels: Tuple[str, ...] = ("RIESGO_CONTRATO", "RIESGO_EDUCACION")
    
    # --- Configuración del Reporte PDF (Estructura) ---
    PDF_COLUMNS_AUDIT: Tuple[str, ...] = ("COLUMNA", "%_NULOS", "CLASIFICACION")
    PDF_COLUMNS_BALANCE: Tuple[str, ...] = ("MÉTRICA", "VALOR_BRONZE", "VALOR_SILVER", "VARIACIÓN")
    PDF_COLUMNS_DERIVED: Tuple[str, ...] = ("VARIABLE", "FÓRMULA", "MEDIA", "MEDIANA", "NULOS_RESIDUALES")
    PDF_COLUMNS_RISK_CONTRACT: Tuple[str, ...] = ("TIPO_CONTRATO", "TASA_MORA", "TOTAL_CLIENTES")
    PDF_COLUMNS_RISK_EDUCATION: Tuple[str, ...] = ("NIVEL_EDUCATIVO", "TASA_MORA", "TOTAL_CLIENTES")
    PDF_COLUMNS_RISK_FAMILY: Tuple[str, ...] = ("ESTADO_CIVIL", "RAZON_CREDITO_INGRESO_PROMEDIO")
    
    # Metadata del Reporte
    report_author: str = "Montenegro & Rodriguez"
    report_title: str = "Reporte de Data Warehouse - Riesgo Crediticio"
    
    # --- Parámetros Visuales y de Formato (UI/UX Reporte) ---
    pdf_margin: int = 15
    pdf_font_size_h1: int = 18
    pdf_font_size_h2: int = 14
    pdf_font_size_h3: int = 12
    pdf_font_size_body: int = 11
    pdf_font_size_table_header: int = 10
    pdf_font_size_table_row: int = 9
    pdf_font_size_caption: int = 8
    
    # Anchos de celdas (mm)
    pdf_cell_w_col: int = 60
    pdf_cell_w_val_small: int = 30
    pdf_cell_w_class: int = 40
    pdf_cell_w_metric: int = 85
    pdf_cell_w_var: int = 45
    pdf_cell_w_formula: int = 70
    pdf_cell_w_stat: int = 20
    pdf_cell_w_res_null: int = 30
    
    # Configuración de Gráficos (Plotting)
    plot_dpi: int = 120
    plot_color_primary: str = 'steelblue'
    plot_color_secondary: str = 'darkorange'
    plot_color_tertiary: str = 'seagreen'
    plot_bg_color_analysis: Tuple[int, int, int] = (240, 240, 240)
    
    plot_yscale_factor_contract: float = 1.17
    plot_yscale_factor_general: float = 1.2
    
    plot_label_offset_standard: float = 0.5
    plot_label_offset_ratio: float = 0.01
    
    # Formatos de Datos
    fmt_pct_one_decimal: str = '{:.1f}%'
    fmt_decimal_two_places: str = '{:.2f}'
    fmt_pct_two_decimals: str = '{:.2%}'
    fmt_stat_decimal: str = '{:.4f}'
    
    #limite de auditorías
    audit_head_limit: int = 10
        
    # --- Identificadores de columnas clave ---
    id_column: str = "SK_ID_CURR"
    income_column: str = "AMT_INCOME_TOTAL"
    silver_columns: Tuple[str, ...] = (
        "SK_ID_CURR", "TARGET", "NAME_CONTRACT_TYPE", "CODE_GENDER",
        "AMT_CREDIT", "AMT_INCOME_TOTAL", "AMT_ANNUITY",
        "CREDIT_TO_INCOME_RATIO", "ANNUITY_INCOME_RATIO",
        "IS_EMPLOYED", "NAME_EDUCATION_TYPE", "NAME_FAMILY_STATUS",
        "CNT_CHILDREN",
    )

    # --- Exportación de archivos ---
    export_gold_csv_name: str = "gold_metricas_riesgo.csv"
    export_ml_csv_name: str = "silver_sample_ml.csv"

    # --- Metadatos del reporte ---
    report_authors_full: str = (
        "Montenegro Baca, Zee Ricardo & Rodriguez Preciado, Andre Jhonel"
    )
    report_advisor: str = "Dr. Santos Fernandez, Juan Pedro"
    pdf_footer_text: str = (
        "Reporte generado automáticamente por el prototipo de Data Warehouse - Tesis I"
    )
    pdf_date_format: str = "%d/%m/%Y %H:%M"

    # --- Lógica de Negocio / Análisis BA Parametrizado ---
    @property
    def analysis_audit_bronze(self) -> str:
        """Genera el texto de análisis inyectando el umbral crítico actual."""
        return (f"Análisis BA: La presencia de columnas con más del {self.null_threshold_critical}% "
                "de valores nulos introduce asimetría de información severa. En una microfinanciera "
                "sin automatización, estos vacíos obligan al analista a rechazar solicitudes o "
                "decidir con datos incompletos. Se recomienda aplicar reglas de imputación "
                "consistentes en la capa Silver.")

    analysis_transformation_silver: str = (
        "Análisis BA: Las variables derivadas CREDIT_TO_INCOME_RATIO y ANNUITY_INCOME_RATIO "
        "permiten estandarizar la capacidad de pago independientemente del monto absoluto. "
        "La creación del indicador IS_EMPLOYED a través de reglas objetivas elimina la "
        "subjetividad del analista al clasificar la situación laboral del solicitante."
    )

    analysis_risk_contract_gold: str = (
        "Análisis BA: Los contratos de tipo 'Revolving' muestran la tasa de morosidad más alta. "
        "Esto sugiere que los productos de crédito rotativo requieren controles adicionales "
        "de seguimiento y quizás límites más conservadores."
    )
    
    # Dentro de la clase Settings, junto a los otros textos de análisis:
    analysis_risk_education_gold: str = (
        "La educación secundaria presenta la tasa más baja de incumplimiento, "
        "mientras que los clientes con educación primaria o inferior muestran mayor riesgo. "
        "Esta variable es un fuerte predictor y debería considerarse en el scoring final."
    )
    analysis_risk_family_gold: str = (
        "Los clientes solteros y viudos tienden a tener una razón crédito/ingreso más alta, "
        "lo que podría indicar una mayor carga financiera relativa. Conviene evaluar si "
        "estos segmentos requieren criterios de aprobación diferenciados."
    )
    

def load_config() -> Settings:
    """
    Orquestador de carga de configuración. 
    Prioriza variables de entorno y secretos de Streamlit sobre valores por defecto.
    """
    # Intenta importar streamlit
    try:
        import streamlit as st
        secrets = st.secrets
    except ImportError:
        secrets = None
    
    # Ingesta de variables externas
    gdrive_url = os.environ.get("CREDIT_RISK_GDRIVE_URL")
    if not gdrive_url and secrets:
        gdrive_url = secrets.get("gdrive_url")
        
    csv_filename = os.environ.get("CREDIT_RISK_CSV_FILE", "application_train.csv")
    db_path = os.environ.get("CREDIT_RISK_DB_PATH", "credit_warehouse.db")
    
    critical = os.environ.get("CREDIT_RISK_NULL_CRITICAL_THRESHOLD")
    moderate = os.environ.get("CREDIT_RISK_NULL_MODERATE_THRESHOLD")
    
    author = os.environ.get("REPORT_AUTHOR", "Montenegro & Rodriguez")
    title = os.environ.get("REPORT_TITLE", "Análisis de Riesgo Crediticio - DW")
        
    authors_full = os.environ.get(
        "REPORT_AUTHORS_FULL",
        "Montenegro Baca, Zee Ricardo & Rodriguez Preciado, Andre Jhonel",
    )
    advisor = os.environ.get("REPORT_ADVISOR", "Dr. Santos Fernandez, Juan Pedro")
    footer = os.environ.get(
        "REPORT_FOOTER",
        "Reporte generado automáticamente por el prototipo de Data Warehouse - Tesis I",
    )
    date_format = os.environ.get("REPORT_DATE_FORMAT", "%d/%m/%Y %H:%M")

    # Nombres de exportación
    gold_csv = os.environ.get("EXPORT_GOLD_CSV", "gold_metricas_riesgo.csv")
    ml_csv = os.environ.get("EXPORT_ML_CSV", "silver_sample_ml.csv")

    # Validación de integridad de origen de datos
    if not gdrive_url and not os.path.exists(csv_filename):
        # En el entorno sin gdrive, si el CSV local no existe, falla.
        raise RuntimeError(
            "Fallo Crítico: No se encontró la URL de Google Drive ni el archivo CSV local. "
            "Defina CREDIT_RISK_GDRIVE_URL o coloque el archivo application_train.csv."
        )
        
    return Settings(
        gdrive_url=gdrive_url or "",  # puede ser vacío si usamos archivo local
        csv_filename=csv_filename,
        db_path=db_path,
        null_threshold_critical=float(critical) if critical else 50.0,
        null_threshold_moderate=float(moderate) if moderate else 20.0,
        report_author=author,
        report_title=title,
        target_column=os.environ.get("FEATURE_TARGET_COLUMN", "TARGET"),
        ml_sample_size=int(os.environ.get("ML_SAMPLE_SIZE", "1000")),
        ml_random_state=int(os.environ.get("ML_RANDOM_STATE", "42")),
        report_authors_full=authors_full,
        report_advisor=advisor,
        pdf_footer_text=footer,
        pdf_date_format=date_format,
        export_gold_csv_name=gold_csv,
        export_ml_csv_name=ml_csv,
    )
