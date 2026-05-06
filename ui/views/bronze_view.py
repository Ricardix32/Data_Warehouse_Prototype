import streamlit as st
import plotly.express as px
from src.audit import auditar_calidad_bronze

def render_bronze(df_bronze, settings):
    st.header("Capa Bronze – Ingesta de datos crudos")
    st.markdown("""
    **Propósito:** Almacenar los datos exactamente como llegan de las fuentes externas.
    Sin modificaciones; se preserva la trazabilidad original.
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

    # Gráfico de distribución del target
    st.subheader("Distribución de TARGET (clientes morosos vs cumplidores)")
    target_counts = df_bronze['TARGET'].value_counts().reset_index()
    target_counts.columns = ['TARGET', 'Cantidad']
    target_counts['TARGET'] = target_counts['TARGET'].map({0:'Cumplidor', 1:'Moroso'})
    fig = px.pie(target_counts, values='Cantidad', names='TARGET',
                 title="Proporción de morosidad en datos crudos",
                 color='TARGET', color_discrete_map={'Cumplidor':'green', 'Moroso':'red'})
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🛠️ Herramientas de auditoría")
    if 'bronze_auditoria_mostrada' not in st.session_state:
        st.session_state.bronze_auditoria_mostrada = False
    if st.button("🔎 Auditar calidad de datos crudos", key="btn_auditar_bronze", type="primary"):
        st.session_state.bronze_auditoria_mostrada = True
    if st.session_state.bronze_auditoria_mostrada:
        resultado_auditoria, num_criticas, pct_dup, memoria_mb, total_cols = auditar_calidad_bronze(
            df_bronze,
            id_column=settings.id_column,
            null_threshold_critical=settings.null_threshold_critical,
            null_threshold_moderate=settings.null_threshold_moderate
        )
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total columnas", total_cols)
        col2.metric("Columnas críticas", num_criticas)
        col3.metric("% Registros duplicados", f"{pct_dup:.2f}%")
        col4.metric("Memoria ocupada (MB)", f"{memoria_mb:.2f}")
        if not resultado_auditoria.empty:
            st.subheader("Columnas con datos faltantes significativos")
            st.dataframe(resultado_auditoria, use_container_width=True)
        if num_criticas > 0:
            st.warning(settings.analysis_audit_bronze)
        else:
            st.success("✅ No se encontraron columnas críticas.")