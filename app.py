"""
app.py - Prototipo de Data Warehouse para Evaluación de Riesgo Crediticio

Arquitectura Medallion (Bronze, Silver, Gold) aplicada al dataset
Home Credit Default Risk. Simula la ingesta, limpieza y agregación
de datos que una microfinanciera ejecutaría para calcular capacidad
de endeudamiento, en línea con la tesis:

"Arquitectura de Data Warehouse y analítica predictiva para la evaluación
de riesgo crediticio en instituciones microfinancieras"

Autor: Data Engineer & Streamlit Research Prototyper
Colaboración: Asesor DeepSeek Expert, Google Gemini Pro
"""

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
import time
import os
#import kagglehub
import gdown
url = "https://drive.google.com/file/d/1ZXwmCfeONnTCDtsNw4CMk3ks4oLk9N18/view?usp=drive_link"  # Extrae el ID de tu enlace
gdown.download(url, "application_train.csv", quiet=False)


# =========================== CONFIGURACIÓN INICIAL ===========================
st.set_page_config(page_title="Data Warehouse - Riesgo Crediticio", layout="wide")
st.title("🏦 Prototipo de Data Warehouse para Riesgo Crediticio")
st.markdown("""
**Tesis:** Arquitectura de Data Warehouse y analítica predictiva para la evaluación de riesgo crediticio  
**Autor:** Montenegro Baca & Rodriguez Preciado | **Asesor:** Dr. Santos Fernandez  
*Este prototipo materializa la capa de datos de la investigación (Bronze → Silver → Gold).*
""")

# ====================== FUNCIONES DE CARGA Y TRANSFORMACIÓN ======================

# --- Descarga del dataset desde gdrive (capa de ingesta) ---
@st.cache_data(show_spinner="Descargando dataset completo desde Drive...")
def cargar_dataset_completo():
    # Intentamos obtener la URL desde los secretos de Streamlit Cloud
    gdrive_url = st.secrets.get("gdrive_url")
    
    if gdrive_url:
        # Descargamos con gdown (solo la primera vez, la caché lo retiene)
        output = "application_train.csv"
        if not os.path.exists(output):
            gdown.download(gdrive_url, output, quiet=False)
        df = pd.read_csv(output)
        st.success("✅ Dataset cargado desde Google Drive (nube).")
    elif os.path.exists("application_train.csv"):
        # Fallback: si existe el archivo local (entorno de desarrollo)
        df = pd.read_csv("application_train.csv")
        st.info("📂 Usando archivo local application_train.csv")
    else:
        st.error("❌ No se encontró el dataset. Agrega el archivo CSV localmente o configura el secreto 'gdrive_url'.")
        st.stop()
    return df

# --- Configuración de base de datos SQLite ---
def crear_conexion():
    """Crea/abre la base de datos SQLite que simula el Data Warehouse."""
    conn = sqlite3.connect("credit_warehouse.db")
    return conn

def almacenar_dataframe(conn, df, nombre_tabla, if_exists="replace"):
    """Guarda un DataFrame en SQLite."""
    df.to_sql(nombre_tabla, conn, if_exists=if_exists, index=False)

# --- Transformaciones capa Silver ---
def crear_capa_silver(df_bronze):
    """
    Capa Silver: limpieza, imputación y creación de variables derivadas.
    Se aplican reglas de negocio alineadas con el cálculo de capacidad de endeudamiento.
    """
    tiempo_inicio = time.time()
    df = df_bronze.copy()

    # 1. Tratamiento de valores nulos y ceros inconsistentes
    # Income no puede ser cero para el cálculo de razones financieras
    df['AMT_INCOME_TOTAL'] = df['AMT_INCOME_TOTAL'].replace(0, np.nan)
    # Imputamos income con la mediana (práctica común en ausencia de dato real)
    mediana_income = df['AMT_INCOME_TOTAL'].median()
    df['AMT_INCOME_TOTAL'].fillna(mediana_income, inplace=True)

    # Otras imputaciones básicas
    for col in ['AMT_CREDIT', 'AMT_ANNUITY']:
        df[col].fillna(df[col].median(), inplace=True)

    # DAYS_EMPLOYED: positivo = desempleado, negativo = empleado; creamos indicador binario
    df['IS_EMPLOYED'] = (df['DAYS_EMPLOYED'] < 0).astype(int)

    # 2. Variables derivadas (ratios de capacidad de pago)
    # Razón crédito / ingreso: endeudamiento relativo
    df['CREDIT_TO_INCOME_RATIO'] = df['AMT_CREDIT'] / df['AMT_INCOME_TOTAL']
    # Razón cuota anual / ingreso: carga financiera
    df['ANNUITY_INCOME_RATIO'] = df['AMT_ANNUITY'] / df['AMT_INCOME_TOTAL']

    # 3. Filtrado de outliers simples (aquellos a más de 3 desviaciones de la media)
    for col in ['CREDIT_TO_INCOME_RATIO', 'ANNUITY_INCOME_RATIO']:
        media = df[col].mean()
        desv = df[col].std()
        df = df[(df[col] >= media - 3*desv) & (df[col] <= media + 3*desv)]

    # 4. Selección de columnas relevantes para análisis de riesgo base
    columnas_silver = [
        'SK_ID_CURR', 'TARGET', 'NAME_CONTRACT_TYPE', 'CODE_GENDER',
        'AMT_CREDIT', 'AMT_INCOME_TOTAL', 'AMT_ANNUITY',
        'CREDIT_TO_INCOME_RATIO', 'ANNUITY_INCOME_RATIO',
        'IS_EMPLOYED', 'NAME_EDUCATION_TYPE', 'NAME_FAMILY_STATUS',
        'CNT_CHILDREN'
    ]
    df_silver = df[columnas_silver].copy()
    tiempo_fin = time.time()
    tiempo_procesamiento = tiempo_fin - tiempo_inicio
    return df_silver, tiempo_procesamiento

# --- Transformaciones capa Gold ---
def crear_capa_gold(df_silver):
    """
    Capa Gold: agrega métricas de riesgo para consultas de negocio.
    Se generan tablas dimensionales (métricas por segmentos) similares a las
    que un analista de crédito consultaría.
    """
    tiempo_inicio = time.time()
    df = df_silver.copy()

    # Agregación: tasa de mora (bad rate) por tipo de contrato
    bad_rate_contract = df.groupby('NAME_CONTRACT_TYPE')['TARGET'].agg(['mean', 'count']).reset_index()
    bad_rate_contract.columns = ['TIPO_CONTRATO', 'TASA_MORA', 'TOTAL_CLIENTES']
    bad_rate_contract['TASA_MORA'] = bad_rate_contract['TASA_MORA'].round(4)

    # Bad rate por nivel educativo
    bad_rate_edu = df.groupby('NAME_EDUCATION_TYPE')['TARGET'].agg(['mean', 'count']).reset_index()
    bad_rate_edu.columns = ['NIVEL_EDUCATIVO', 'TASA_MORA', 'TOTAL_CLIENTES']
    bad_rate_edu['TASA_MORA'] = bad_rate_edu['TASA_MORA'].round(4)

    # Razón crédito/ingreso promedio por estado civil
    ratio_family = df.groupby('NAME_FAMILY_STATUS')['CREDIT_TO_INCOME_RATIO'].mean().reset_index()
    ratio_family.columns = ['ESTADO_CIVIL', 'RAZON_CREDITO_INGRESO_PROMEDIO']

    # Unificamos en una sola tabla resumen para visualización
    # (Se pueden crear múltiples tablas Gold según necesidad)
    gold_summary = pd.merge(bad_rate_contract, 
                            df.groupby('NAME_CONTRACT_TYPE')['CREDIT_TO_INCOME_RATIO'].mean().reset_index(),
                            left_on='TIPO_CONTRATO', right_on='NAME_CONTRACT_TYPE', how='left'
                           ).drop(columns='NAME_CONTRACT_TYPE')

    tiempo_fin = time.time()
    tiempo_procesamiento = tiempo_fin - tiempo_inicio
    return gold_summary, bad_rate_edu, ratio_family, tiempo_procesamiento

# ============================== FLUJO PRINCIPAL DE LA APLICACIÓN ==============================

# Descarga y carga de datos (Bronze)
df_bronze = cargar_dataset_completo()

# Conexión a SQLite
conn = crear_conexion()

# --- Menú lateral de navegación ---
st.sidebar.title("📂 Capas del Data Warehouse")
capa = st.sidebar.radio(
    "Selecciona una capa:",
    ["🥉 Bronze (Datos crudos)", "🥈 Silver (Datos limpios y transformados)", "🥇 Gold (Métricas de riesgo)"],
    index=0
)

# Botón para ejecutar/refrescar ETL (simula la automatización del pipeline)
if st.sidebar.button("🔄 Ejecutar Pipeline ETL completo"):
    # (Se ejecuta automáticamente al cargar la app, pero puede forzarse)
    st.cache_data.clear()
    st.rerun()

# --- Almacenamiento inicial de capa Bronze en SQLite (si no existe) ---
try:
    df_bronze.to_sql("bronze_application_train", conn, if_exists="fail", index=False)
except ValueError:
    pass  # ya existe

# Procesamiento Silver (con caché para no recalcular cada vez)
@st.cache_data
def obtener_silver(df_bronze):
    return crear_capa_silver(df_bronze)

df_silver, tiempo_silver = obtener_silver(df_bronze)
almacenar_dataframe(conn, df_silver, "silver_application_train")

# Procesamiento Gold
@st.cache_data
def obtener_gold(df_silver):
    return crear_capa_gold(df_silver)

gold_contract, gold_edu, gold_family, tiempo_gold = obtener_gold(df_silver)
almacenar_dataframe(conn, gold_contract, "gold_risk_contract")
almacenar_dataframe(conn, gold_edu, "gold_risk_education")
almacenar_dataframe(conn, gold_family, "gold_risk_family")

# =============================== MOSTRAR CAPAS ===============================
if capa == "🥉 Bronze (Datos crudos)":
    st.header("Capa Bronze – Ingesta de datos crudos")
    st.markdown("""
    **Propósito:** Almacenar los datos exactamente como llegan de las fuentes externas
    (en una microfinanciera serían documentos físicos escaneados, planillas Excel de diferentes agencias, etc.).
    Aquí no se modifica nada; se preserva la trazabilidad original.
    """)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Número de registros", f"{df_bronze.shape[0]:,}")
    with col2:
        st.metric("Variables originales", df_bronze.shape[1])

    st.subheader("Vista previa (primeras 5 filas)")
    st.dataframe(df_bronze.head())

    st.subheader("Estadísticas básicas")
    st.dataframe(df_bronze.describe())

    # Gráfico: Distribución de la variable objetivo (TARGET = 1 significa moroso)
    st.subheader("Distribución de TARGET (clientes morosos vs cumplidores)")
    target_counts = df_bronze['TARGET'].value_counts().reset_index()
    target_counts.columns = ['TARGET', 'Cantidad']
    target_counts['TARGET'] = target_counts['TARGET'].map({0:'Cumplidor', 1:'Moroso'})
    fig = px.pie(target_counts, values='Cantidad', names='TARGET', 
                 title="Proporción de morosidad en datos crudos",
                 color='TARGET', color_discrete_map={'Cumplidor':'green', 'Moroso':'red'})
    st.plotly_chart(fig, use_container_width=True)

    st.caption("⏱️ Tiempo de carga (incluye descarga): verificado al iniciar la app.")

# -----------------------------------------------------------------------
elif capa == "🥈 Silver (Datos limpios y transformados)":
    st.header("Capa Silver – Transformación y enriquecimiento")
    st.markdown(f"""
    **Propósito:** Aplicar reglas de calidad y derivar variables de capacidad de pago.
    - Se imputaron ingresos nulos/cero.
    - Se crearon razones financieras: `CREDIT_TO_INCOME_RATIO` y `ANNUITY_INCOME_RATIO`.
    - Se filtraron outliers extremos (típico en ETL para evitar distorsiones en modelos).
    
    ⏱️ **Tiempo de procesamiento de esta capa:** {tiempo_silver:.2f} segundos.
    
    *Nota:* En la tesis, esta capa corresponde al cálculo de la capacidad de endeudamiento
    a partir de documentos no estructurados (boletas de pago, estados de cuenta). Aquí simulamos
    ese paso con variables numéricas del dataset.
    """)

    st.subheader("Datos transformados (muestra)")
    st.dataframe(df_silver.head())

    st.subheader("Estadísticas (variables clave)")
    st.dataframe(df_silver.describe())

    # Gráfico: Distribución de CREDIT_TO_INCOME_RATIO según TARGET
    st.subheader("Razón Crédito/Ingreso y morosidad")
    fig = px.histogram(df_silver, x="CREDIT_TO_INCOME_RATIO", color="TARGET",
                       marginal="box", nbins=50,
                       title="¿Clientes con mayor endeudamiento relativo tienen más morosidad?",
                       labels={"CREDIT_TO_INCOME_RATIO": "Razón Crédito/Ingreso", "TARGET": "Moroso"},
                       color_discrete_map={0: 'green', 1: 'red'})
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Un analista de crédito revisaría este gráfico para establecer políticas de endeudamiento máximo.")

# -----------------------------------------------------------------------
elif capa == "🥇 Gold (Métricas de riesgo)":
    st.header("Capa Gold – Agregaciones para toma de decisiones")
    st.markdown(f"""
    **Propósito:** Proporcionar métricas consolidadas listas para ser consumidas
    por reportes, dashboards o futuros modelos de scoring.
    
    ⏱️ **Tiempo de procesamiento de esta capa:** {tiempo_gold:.2f} segundos.
    
    *En la tesis, esta capa alimentará directamente los módulos de analítica predictiva
    y los informes de riesgo institucional.*
    """)

    # Tabla de tasa de mora por tipo de contrato
    st.subheader("Tasa de morosidad por tipo de contrato")
    st.dataframe(gold_contract.style.format({"TASA_MORA": "{:.2%}"}))

    fig1 = px.bar(gold_contract, x="TIPO_CONTRATO", y="TASA_MORA",
                  title="Bad rate por tipo de contrato",
                  labels={"TASA_MORA": "Tasa de morosidad", "TIPO_CONTRATO": ""})
    st.plotly_chart(fig1, use_container_width=True)

    # Tasa de mora por nivel educativo
    st.subheader("Tasa de morosidad por nivel educativo")
    st.dataframe(gold_edu.style.format({"TASA_MORA": "{:.2%}"}))

    fig2 = px.bar(gold_edu, x="NIVEL_EDUCATIVO", y="TASA_MORA",
                  title="Bad rate por educación",
                  labels={"TASA_MORA": "Tasa de morosidad"})
    st.plotly_chart(fig2, use_container_width=True)

    # Razón crédito/ingreso promedio por estado civil
    st.subheader("Razón crédito/ingreso promedio por estado civil")
    st.dataframe(gold_family)

    fig3 = px.bar(gold_family, x="ESTADO_CIVIL", y="RAZON_CREDITO_INGRESO_PROMEDIO",
                  title="Endeudamiento relativo según estado civil",
                  labels={"RAZON_CREDITO_INGRESO_PROMEDIO": "Razón Crédito/Ingreso promedio"})
    st.plotly_chart(fig3, use_container_width=True)

# ================== SECCIÓN FINAL: CONEXIÓN CON LA TESIS ==================
st.sidebar.markdown("---")
st.sidebar.info("""
**📌 Repositorio local:** `credit_warehouse.db`  
**📋 Código fuente:** disponible en el repositorio del proyecto.  
""")

st.markdown("---")
st.markdown("""
## 🔗 Vinculación con el proyecto de tesis

Este prototipo implementa la **arquitectura Medallion** (Bronze, Silver, Gold) descrita en el Capítulo I de la investigación.
La selección de variables y las transformaciones aplicadas emulan el pipeline ETL que las microfinancieras necesitan
para automatizar el cálculo de la capacidad de endeudamiento, superando así la dependencia de hojas de cálculo manuales.

- **Bronze** refleja la ingesta de documentos heterogéneos (boletas de pago, DNI, etc.) que hoy se procesan manualmente.
- **Silver** ejecuta validaciones y genera indicadores como `CREDIT_TO_INCOME_RATIO`, análogos a los que un analista
  obtendría al evaluar la capacidad de pago de una MYPE.
- **Gold** consolida métricas de riesgo (bad rate) por segmentos, que en la siguiente fase (Tesis II) se utilizarán
  como insumos para modelos de machine learning.

El uso de **Streamlit** y **SQLite** permite validar de forma interactiva la precisión y reducción de latencia
(medida con los tiempos de procesamiento mostrados en cada capa), los cuales son los indicadores clave de éxito
definidos en los objetivos específicos (reducción de tiempo y aumento de precisión frente a métodos manuales).

**Próximos pasos sugeridos por el equipo de investigación (DeepSeek Expert & Gemini Pro):**
- Incorporar datos alternativos (texto de documentos) mediante IDP (LayoutLMv3).
- Ampliar la capa Gold con métricas ESG.
- Desplegar en Streamlit Cloud para revisión externa.
""")

# Cierre de conexión
conn.close()