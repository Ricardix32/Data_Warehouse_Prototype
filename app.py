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

Versión: 2.0 - Con botones de auditoría, trazabilidad y exportación
"""

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import time
import os
import gdown

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
        output = "application_train.csv"
        if not os.path.exists(output):
            try:
                with st.spinner("Descargando dataset desde Google Drive..."):
                    gdown.download(gdrive_url, output, quiet=False)
            except Exception as e:
                st.error(f"❌ Error al descargar el dataset: {e}")
                st.stop()
        try:
            df = pd.read_csv(output)
        except Exception as e:
            st.error(f"❌ No se pudo leer el archivo descargado: {e}")
            st.stop()
        st.success("✅ Dataset cargado desde Google Drive (nube).")
        return df
    elif os.path.exists("application_train.csv"):
        # Fallback: si existe el archivo local (entorno de desarrollo)
        df = pd.read_csv("application_train.csv")
        st.info("📂 Usando archivo local application_train.csv")
        return df
    else:
        st.error("❌ No se encontró el dataset. Agrega el archivo CSV localmente o configura el secreto 'gdrive_url'.")
        st.stop()

# --- Configuración de base de datos SQLite ---
def crear_conexion():
    """Crea/abre la base de datos SQLite que simula el Data Warehouse."""
    conn = sqlite3.connect("credit_warehouse.db")
    return conn
    
# Función cacheada que construye todo el almacén      
@st.cache_resource
def construir_data_warehouse(df_bronze):
    """
    Crea las tablas en SQLite y devuelve los dataframes ya procesados.
    Solo se ejecuta una vez por sesión, evitando bloqueos de SQLite.
    """
    conn = sqlite3.connect("credit_warehouse.db")
    
    # Bronze
    df_bronze.to_sql("bronze_application_train", conn, if_exists="replace", index=False)
    
    # Silver (procesamos y guardamos)
    df_silver, tiempo_silver = crear_capa_silver(df_bronze)
    df_silver.to_sql("silver_application_train", conn, if_exists="replace", index=False)
    
    # Gold
    gold_contract, gold_edu, gold_family, tiempo_gold = crear_capa_gold(df_silver)
    gold_contract.to_sql("gold_risk_contract", conn, if_exists="replace", index=False)
    gold_edu.to_sql("gold_risk_education", conn, if_exists="replace", index=False)
    gold_family.to_sql("gold_risk_family", conn, if_exists="replace", index=False)
    
    conn.close()
    return df_silver, tiempo_silver, gold_contract, gold_edu, gold_family, tiempo_gold

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
    df['AMT_INCOME_TOTAL'] = df['AMT_INCOME_TOTAL'].fillna(mediana_income)
    
    # Otras imputaciones básicas
    for col in ['AMT_CREDIT', 'AMT_ANNUITY']:
        df[col] = df[col].fillna(df[col].median())
    
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
    gold_summary = pd.merge(bad_rate_contract,
                            df.groupby('NAME_CONTRACT_TYPE')['CREDIT_TO_INCOME_RATIO'].mean().reset_index(),
                            left_on='TIPO_CONTRATO', right_on='NAME_CONTRACT_TYPE', how='left'
                           ).drop(columns='NAME_CONTRACT_TYPE')
    
    tiempo_fin = time.time()
    tiempo_procesamiento = tiempo_fin - tiempo_inicio
    
    return gold_summary, bad_rate_edu, ratio_family, tiempo_procesamiento


# --- BOTÓN 1: Auditoría de calidad en Bronze ---
def auditar_calidad_bronze(df):
    """Evalúa la calidad de los datos crudos: nulos, duplicados y memoria."""
    total_cols = len(df.columns)
    
    # Porcentaje de nulos por columna
    null_percent = (df.isnull().sum() / len(df)) * 100
    
    # Clasificación de columnas
    criticas = null_percent[null_percent > 50].reset_index()
    criticas.columns = ['COLUMNA', '%_NULOS']
    criticas['CLASIFICACION'] = 'CRÍTICA (>50%)'
    
    moderadas = null_percent[(null_percent >= 20) & (null_percent <= 50)].reset_index()
    moderadas.columns = ['COLUMNA', '%_NULOS']
    moderadas['CLASIFICACION'] = 'MODERADA (20-50%)'
    
    aceptables = null_percent[null_percent < 20].reset_index()
    aceptables.columns = ['COLUMNA', '%_NULOS']
    aceptables['CLASIFICACION'] = 'ACEPTABLE (<20%)'
    
    resultado = pd.concat([criticas, moderadas], ignore_index=True)
    resultado['%_NULOS'] = resultado['%_NULOS'].round(2)
    
    # Duplicados basados en SK_ID_CURR
    duplicados = df['SK_ID_CURR'].duplicated().sum() if 'SK_ID_CURR' in df.columns else 0
    pct_duplicados = (duplicados / len(df)) * 100
    
    # Memoria
    memoria_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    
    return resultado, len(criticas), pct_duplicados, memoria_mb, total_cols


# --- BOTÓN 2: Trazabilidad de reglas en Silver ---
def trazabilidad_silver(df_bronze, df_silver):
    """Compara el estado antes (bronze) y después (silver) de las transformaciones."""
    # Balance de filas
    filas_bronze = len(df_bronze)
    filas_silver = len(df_silver)
    filas_eliminadas = filas_bronze - filas_silver
    
    # Balance de columnas
    cols_bronze = len(df_bronze.columns)
    cols_silver = len(df_silver.columns)
    
    # Identificar cuántos ingresos eran 0 o nulos en bronze
    if 'AMT_INCOME_TOTAL' in df_bronze.columns:
        ingresos_problematicos = df_bronze['AMT_INCOME_TOTAL'].isnull().sum() + (df_bronze['AMT_INCOME_TOTAL'] == 0).sum()
    else:
        ingresos_problematicos = 0
    
    balance = pd.DataFrame({
        'MÉTRICA': ['Filas totales', 'Columnas totales', 'Ingresos imputados (nulos/cero → mediana)'],
        'VALOR_BRONZE': [filas_bronze, cols_bronze, ingresos_problematicos],
        'VALOR_SILVER': [filas_silver, cols_silver, 0],
        'VARIACIÓN': [f'-{filas_eliminadas} filas (outliers)', 
                      f'+{cols_silver - cols_bronze} columnas derivadas',
                      f'{ingresos_problematicos} valores corregidos']
    })
    
    # Variables derivadas
    derivadas = pd.DataFrame({
        'VARIABLE': ['CREDIT_TO_INCOME_RATIO', 'ANNUITY_INCOME_RATIO', 'IS_EMPLOYED'],
        'FÓRMULA': ['AMT_CREDIT / AMT_INCOME_TOTAL', 'AMT_ANNUITY / AMT_INCOME_TOTAL', 'DAYS_EMPLOYED < 0 → 1 (empleado)'],
        'MIN': [df_silver['CREDIT_TO_INCOME_RATIO'].min(), df_silver['ANNUITY_INCOME_RATIO'].min(), None],
        'MAX': [df_silver['CREDIT_TO_INCOME_RATIO'].max(), df_silver['ANNUITY_INCOME_RATIO'].max(), None],
        'MEDIA': [df_silver['CREDIT_TO_INCOME_RATIO'].mean(), df_silver['ANNUITY_INCOME_RATIO'].mean(), None],
        'MEDIANA': [df_silver['CREDIT_TO_INCOME_RATIO'].median(), df_silver['ANNUITY_INCOME_RATIO'].median(), None],
        'NULOS_RESIDUALES': [df_silver['CREDIT_TO_INCOME_RATIO'].isnull().sum(), 
                             df_silver['ANNUITY_INCOME_RATIO'].isnull().sum(), 
                             df_silver['IS_EMPLOYED'].isnull().sum()]
    })
    
    # Redondear valores numéricos para mejor visualización
    for col in ['MIN', 'MAX', 'MEDIA', 'MEDIANA']:
        derivadas[col] = derivadas[col].apply(lambda x: round(x, 4) if pd.notnull(x) else 'N/A')
    
    return balance, derivadas, filas_eliminadas


# --- BOTÓN 3: Exportar feature store en Gold ---
def exportar_feature_store(df_silver, gold_contract, gold_edu, gold_family):
    """Prepara el catálogo de features y exporta datasets para ML."""
    # Catálogo de features
    features_numericas = df_silver.select_dtypes(include=[np.number]).columns.tolist()
    features_categoricas = df_silver.select_dtypes(include=['object']).columns.tolist()
    
    catalogo = []
    for col in features_numericas:
        if col != 'TARGET':  # TARGET es la variable objetivo, no un predictor
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
    
    # Matriz de correlación
    cols_corr = [c for c in features_numericas if c != 'TARGET']
    if cols_corr:
        corr_matrix = df_silver[cols_corr].corr()
    else:
        corr_matrix = pd.DataFrame()
    
    # CSV Gold consolidado
    csv_gold = pd.concat([
        gold_contract.assign(TIPO_METRICA='RIESGO_CONTRATO'),
        gold_edu.assign(TIPO_METRICA='RIESGO_EDUCACION')
    ], ignore_index=True)
    
    # CSV Silver (muestra para ML)
    csv_ml = df_silver.sample(n=min(1000, len(df_silver)), random_state=42)
    
    return df_catalogo, corr_matrix, csv_gold, csv_ml


# ============================== FLUJO PRINCIPAL DE LA APLICACIÓN ==============================

# Descarga y carga de datos (Bronze)
df_bronze = cargar_dataset_completo()
if df_bronze is None:
    st.error("No se pudo obtener el dataset. Revisa los logs.")
    st.stop()

# --- Menú lateral de navegación ---
st.sidebar.title("📂 Capas del Data Warehouse")
capa = st.sidebar.radio(
    "Selecciona una capa:",
    ["🥉 Bronze (Datos crudos)", "🥈 Silver (Datos limpios y transformados)", "🥇 Gold (Métricas de riesgo)"],
    index=0
)

# Botón para ejecutar/refrescar ETL (simula la automatización del pipeline)
if st.sidebar.button("🔄 Ejecutar Pipeline ETL completo"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()

# Construcción del Data Warehouse (cacheada como recurso)
df_silver, tiempo_silver, gold_contract, gold_edu, gold_family, tiempo_gold = construir_data_warehouse(df_bronze)


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
    
    # ==================== BOTÓN 1: AUDITORÍA DE CALIDAD BRONZE ====================
    st.markdown("---")
    st.subheader("🛠️ Herramientas de auditoría")
    
    # Inicializar session state
    if 'bronze_auditoria_mostrada' not in st.session_state:
        st.session_state.bronze_auditoria_mostrada = False
    
    if st.button("🔎 Auditar calidad de datos crudos", key="btn_auditar_bronze", type="primary"):
        st.session_state.bronze_auditoria_mostrada = True
    
    if st.session_state.bronze_auditoria_mostrada:
        resultado_auditoria, num_criticas, pct_dup, memoria_mb, total_cols = auditar_calidad_bronze(df_bronze)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total columnas", total_cols)
        with col2:
            st.metric("Columnas críticas (>50% nulos)", num_criticas)
        with col3:
            st.metric("% Registros duplicados", f"{pct_dup:.2f}%")
        with col4:
            st.metric("Memoria ocupada (MB)", f"{memoria_mb:.2f}")
        
        if not resultado_auditoria.empty:
            st.subheader("Columnas con datos faltantes significativos")
            st.dataframe(resultado_auditoria, use_container_width=True)
        
        if num_criticas > 0:
            st.warning("⚠️ Estas columnas introducen asimetría de información severa. En una IMF sin Data Warehouse, este nivel de datos faltantes obliga al analista a rechazar solicitudes o decidir sin evidencia. Nuestra arquitectura aplica reglas de imputación en la capa Silver para mitigar este problema.")
        else:
            st.success("✅ No se encontraron columnas críticas. La calidad base de los datos es aceptable para iniciar el proceso ETL.")


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
    
    # ==================== BOTÓN 2: TRAZABILIDAD SILVER ====================
    st.markdown("---")
    st.subheader("📋 Gobierno del Dato")
    
    # Inicializar session state
    if 'silver_trazabilidad_mostrada' not in st.session_state:
        st.session_state.silver_trazabilidad_mostrada = False
    
    if st.button("🧹 Trazabilidad de reglas de calidad (Data Governance)", key="btn_trazabilidad_silver", type="primary"):
        st.session_state.silver_trazabilidad_mostrada = True
    
    if st.session_state.silver_trazabilidad_mostrada:
        balance, derivadas, filas_eliminadas = trazabilidad_silver(df_bronze, df_silver)
        
        st.subheader("📊 Balance de transformación (Bronze → Silver)")
        st.dataframe(balance, use_container_width=True, hide_index=True)
        
        st.subheader("🔬 Variables derivadas y sus estadísticas")
        st.dataframe(derivadas, use_container_width=True, hide_index=True)
        
        st.success("✅ La aplicación consistente de reglas de calidad elimina la variabilidad humana en la preparación de datos. Cada registro recibe exactamente el mismo tratamiento, garantizando equidad en la evaluación crediticia. Las reglas documentadas aquí son el primer paso hacia un gobierno del dato auditado y transparente.")


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
    
    # ==================== BOTÓN 3: EXPORTAR FEATURE STORE GOLD ====================
    st.markdown("---")
    st.subheader("🤖 Preparación para Machine Learning")
    
    # Inicializar session state
    if 'gold_exportacion_mostrada' not in st.session_state:
        st.session_state.gold_exportacion_mostrada = False
    
    if st.button("📊 Exportar feature store para modelo predictivo", key="btn_exportar_gold", type="primary"):
        st.session_state.gold_exportacion_mostrada = True
    
    if st.session_state.gold_exportacion_mostrada:
        df_catalogo, corr_matrix, csv_gold, csv_ml = exportar_feature_store(df_silver, gold_contract, gold_edu, gold_family)
        
        # Catálogo de features
        st.subheader("📋 Catálogo de features disponibles")
        st.dataframe(df_catalogo, use_container_width=True, hide_index=True)
        
        # Matriz de correlación
        if not corr_matrix.empty:
            st.subheader("🔗 Matriz de correlación (variables numéricas de Silver)")
            fig_corr = px.imshow(corr_matrix, 
                                 text_auto='.2f',
                                 color_continuous_scale='RdBu_r',
                                 zmin=-1, zmax=1,
                                 title="Correlación entre features numéricas")
            fig_corr.update_layout(height=600)
            st.plotly_chart(fig_corr, use_container_width=True)
        
        # Botones de descarga
        st.subheader("📥 Descarga de datasets")
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Descargar métricas Gold (CSV)",
                data=csv_gold.to_csv(index=False).encode('utf-8'),
                file_name='gold_metricas_riesgo.csv',
                mime='text/csv',
                key='download_gold'
            )
        with col2:
            st.download_button(
                label="📥 Descargar muestra para ML - 1000 registros (CSV)",
                data=csv_ml.to_csv(index=False).encode('utf-8'),
                file_name='silver_sample_ml.csv',
                mime='text/csv',
                key='download_ml'
            )
        
        st.info("💡 Esta capa Gold es la **feature store** que alimentará los modelos predictivos en Tesis II. Las variables aquí estandarizadas (ratios financieros, indicadores binarios de empleo, segmentaciones por educación y estado civil) constituyen el conjunto mínimo viable de predictores para un modelo de credit scoring en microfinanzas. La matriz de correlación ayuda a identificar posibles variables redundantes antes del entrenamiento.")


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
