import streamlit as st
import plotly.express as px
from audit import trazabilidad_silver

def render_silver(df_bronze, df_silver, meta_silver, settings):
    st.header("Capa Silver – Transformación y enriquecimiento")
    st.markdown(f"""
    **Propósito:** Aplicar reglas de calidad y derivar variables de capacidad de pago.
    - Se imputaron ingresos nulos/cero.
    - Se crearon razones financieras.
    - Se filtraron outliers extremos.
    ⏱️ **Tiempo de procesamiento de esta capa:** {meta_silver['time_seconds']:.2f} segundos.
    """)
    st.subheader("Datos transformados (muestra)")
    st.dataframe(df_silver.head())
    st.subheader("Estadísticas (variables clave)")
    st.dataframe(df_silver.describe())

    # Gráfico interactivo
    st.subheader("Razón Crédito/Ingreso y morosidad")
    fig = px.histogram(df_silver, x="CREDIT_TO_INCOME_RATIO", color="TARGET",
                       marginal="box", nbins=50,
                       title="¿Clientes con mayor endeudamiento relativo tienen más morosidad?",
                       labels={"CREDIT_TO_INCOME_RATIO": "Razón Crédito/Ingreso", "TARGET": "Moroso"},
                       color_discrete_map={0: 'green', 1: 'red'})
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Gobierno del Dato")
    if 'silver_trazabilidad_mostrada' not in st.session_state:
        st.session_state.silver_trazabilidad_mostrada = False
    if st.button("🧹 Trazabilidad de reglas de calidad (Data Governance)", key="btn_trazabilidad_silver", type="primary"):
        st.session_state.silver_trazabilidad_mostrada = True
    if st.session_state.silver_trazabilidad_mostrada:
        balance, derivadas, _ = trazabilidad_silver(
            df_bronze, df_silver,
            income_column=settings.income_column,
            derived_features=settings.derived_features
        )
        st.subheader("📊 Balance de transformación (Bronze → Silver)")
        st.dataframe(balance, use_container_width=True, hide_index=True)
        st.subheader("🔬 Variables derivadas y sus estadísticas")
        st.dataframe(derivadas, use_container_width=True, hide_index=True)
        st.success("✅ Reglas aplicadas consistentemente. Gobierno del dato asegurado.")