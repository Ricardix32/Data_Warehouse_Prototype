"""
app.py - Orquestador principal del prototipo Data Warehouse – Riesgo Crediticio.
Arquitectura Medallion (Bronze → Silver → Gold) con vistas modulares.
"""

import streamlit as st
from config import load_config
from src.etl import run_etl_pipeline
from src.export import generar_reporte_pdf
from ui.views.bronze_view import render_bronze
from ui.views.silver_view import render_silver
from ui.views.gold_view import render_gold

# --------------------------- CONFIGURACIÓN INICIAL ---------------------------
st.set_page_config(page_title="Data Warehouse - Riesgo Crediticio", layout="wide")
st.title("🏦 Prototipo de Data Warehouse para Riesgo Crediticio")
st.markdown("""
**Tesis:** Arquitectura de Data Warehouse y analítica predictiva para la evaluación de riesgo crediticio  
**Autor:** Montenegro Baca & Rodriguez Preciado | **Asesor:** Dr. Santos Fernandez  
*Este prototipo materializa la capa de datos de la investigación (Bronze → Silver → Gold).*
""")

# --------------------------- CARGA DE CONFIGURACIÓN Y DATOS ---------------------------
settings = load_config()

@st.cache_data(show_spinner="Descargando dataset...")
def get_bronze_df(settings):
    from src.data.loader import load_raw_dataset
    return load_raw_dataset(settings)

@st.cache_resource
def build_warehouse(settings):
    return run_etl_pipeline(settings)

# Ejecución del pipeline
try:
    df_bronze = get_bronze_df(settings)
except RuntimeError as e:
    st.error(str(e))
    st.stop()
warehouse_data = build_warehouse(settings)

# Desempaquetado para las vistas
df_silver = warehouse_data["silver_df"]
gold_contract = warehouse_data["gold_contract"]
gold_edu = warehouse_data["gold_edu"]
gold_family = warehouse_data["gold_family"]
meta_silver = warehouse_data["meta_silver"]
meta_gold = warehouse_data["meta_gold"]

# Guardamos el estado de ETL completado
st.session_state.etl_completado = True

# --------------------------- SIDEBAR Y NAVEGACIÓN ---------------------------
st.sidebar.title("📂 Capas del Data Warehouse")
capa = st.sidebar.radio(
    "Selecciona una capa:",
    ["🥉 Bronze (Datos crudos)", "🥈 Silver (Datos limpios y transformados)", "🥇 Gold (Métricas de riesgo)"],
    index=0
)

# --------------------------- RENDERIZADO DE VISTAS ---------------------------
if capa.startswith("🥉"):
    render_bronze(df_bronze, settings)
elif capa.startswith("🥈"):
    render_silver(df_bronze, df_silver, meta_silver, settings)
else:
    render_gold(df_silver, gold_contract, gold_edu, gold_family, meta_gold, settings)

# --------------------------- BOTONES DEL SIDEBAR ---------------------------
if st.sidebar.button("🔄 Ejecutar Pipeline ETL completo"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()

if st.sidebar.button("📄 Generar Reporte PDF del DW", key="btn_reporte_pdf"):
    if not st.session_state.get("etl_completado", False):
        st.sidebar.error("⚠️ El proceso ETL aún no ha finalizado. Ejecute primero el pipeline completo.")
    else:
        with st.sidebar:
            with st.spinner("Generando reporte PDF..."):
                try:
                    pdf_bytes = generar_reporte_pdf(
                        df_bronze, df_silver,
                        gold_contract, gold_edu, gold_family,
                        settings
                    )
                    st.download_button(
                        label="📥 Descargar Reporte PDF",
                        data=pdf_bytes,
                        file_name="reporte_datawarehouse_riesgo.pdf",
                        mime="application/pdf"
                    )
                    st.success("✅ Reporte generado exitosamente.")
                except Exception as e:
                    st.error(f"❌ Error al generar el reporte: {str(e)}")

# --------------------------- PIE DE PÁGINA ---------------------------
st.sidebar.markdown("---")
st.sidebar.info("""
**📌 Repositorio local:** `credit_warehouse.db`  
**📋 Código fuente:** disponible en el repositorio del proyecto.  
""")