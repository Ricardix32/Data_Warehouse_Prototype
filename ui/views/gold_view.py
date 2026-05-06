import streamlit as st
import plotly.express as px
from export import exportar_feature_store

def render_gold(df_silver, gold_contract, gold_edu, gold_family, meta_gold, settings):
    st.header("Capa Gold – Agregaciones para toma de decisiones")
    st.markdown(f"""
    **Propósito:** Métricas consolidadas para reportes y modelos de scoring.
    ⏱️ **Tiempo de procesamiento de esta capa:** {meta_gold['time_seconds']:.2f} segundos.
    """)

    # Tabla 1: Morosidad por contrato
    st.subheader("Tasa de morosidad por tipo de contrato")
    st.dataframe(gold_contract.style.format({"TASA_MORA": "{:.2%}"}))
    fig1 = px.bar(gold_contract, x="TIPO_CONTRATO", y="TASA_MORA",
                  title="Bad rate por tipo de contrato",
                  labels={"TASA_MORA": "Tasa de morosidad"})
    st.plotly_chart(fig1, use_container_width=True)

    # Tabla 2: Morosidad por educación
    st.subheader("Tasa de morosidad por nivel educativo")
    st.dataframe(gold_edu.style.format({"TASA_MORA": "{:.2%}"}))
    fig2 = px.bar(gold_edu, x="NIVEL_EDUCATIVO", y="TASA_MORA",
                  title="Bad rate por educación",
                  labels={"TASA_MORA": "Tasa de morosidad"})
    st.plotly_chart(fig2, use_container_width=True)

    # Tabla 3: Endeudamiento por estado civil
    st.subheader("Razón crédito/ingreso promedio por estado civil")
    st.dataframe(gold_family)
    fig3 = px.bar(gold_family, x="ESTADO_CIVIL", y="RAZON_CREDITO_INGRESO_PROMEDIO",
                  title="Endeudamiento relativo según estado civil",
                  labels={"RAZON_CREDITO_INGRESO_PROMEDIO": "Razón Crédito/Ingreso promedio"})
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")
    st.subheader("🤖 Preparación para Machine Learning")
    if 'gold_exportacion_mostrada' not in st.session_state:
        st.session_state.gold_exportacion_mostrada = False
    if st.button("📊 Exportar feature store para modelo predictivo", key="btn_exportar_gold", type="primary"):
        st.session_state.gold_exportacion_mostrada = True
    if st.session_state.gold_exportacion_mostrada:
        df_catalogo, corr_matrix, csv_gold, csv_ml = exportar_feature_store(
            df_silver, gold_contract, gold_edu, gold_family, settings
        )
        st.subheader("📋 Catálogo de features disponibles")
        st.dataframe(df_catalogo, use_container_width=True, hide_index=True)

        if not corr_matrix.empty:
            st.subheader("🔗 Matriz de correlación (variables numéricas de Silver)")
            fig_corr = px.imshow(corr_matrix, text_auto='.2f',
                                 color_continuous_scale='RdBu_r', zmin=-1, zmax=1,
                                 title="Correlación entre features numéricas")
            fig_corr.update_layout(height=600)
            st.plotly_chart(fig_corr, use_container_width=True)

        st.subheader("📥 Descarga de datasets")
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Descargar métricas Gold (CSV)",
                data=csv_gold.to_csv(index=False).encode('utf-8'),
                file_name=settings.export_gold_csv_name,
                mime='text/csv'
            )
        with col2:
            st.download_button(
                label="📥 Descargar muestra para ML (CSV)",
                data=csv_ml.to_csv(index=False).encode('utf-8'),
                file_name=settings.export_ml_csv_name,
                mime='text/csv'
            )
        st.info("💡 La capa Gold es la feature store que alimentará modelos en Tesis II.")