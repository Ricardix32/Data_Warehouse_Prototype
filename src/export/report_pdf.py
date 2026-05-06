from visualization import plot_bad_rate_by_contract
from audit import auditar_calidad_bronze
from audit import trazabilidad_silver
from config import Settings
from fpdf import FPDF

# GENERAR REPORTE PDF
def generar_reporte_pdf(df_bronze, df_silver, gold_contract, gold_edu, gold_family):
    """Genera un PDF profesional con análisis de datos y gráficos para la tesis."""
    
    pdf = FPDF()
    pdf.add_page()
    
    # --- Configuración de estilos ---
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PORTADA ---
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, "Reporte de Data Warehouse para Riesgo Crediticio", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, "Proyecto de Tesis: Arquitectura de Data Warehouse y analítica predictiva", ln=True, align="C")
    pdf.cell(0, 8, "para la evaluación de riesgo crediticio en instituciones microfinancieras", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "I", 11)
    pdf.cell(0, 8, "Autores: Montenegro Baca, Zee Ricardo & Rodriguez Preciado, Andre Jhonel", ln=True, align="C")
    pdf.cell(0, 8, "Asesor: Dr. Santos Fernandez, Juan Pedro", ln=True, align="C")
    pdf.cell(0, 8, f"Fecha: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align="C")
    pdf.ln(10)
    
    # ========== SECCIÓN 1: AUDITORÍA DE CALIDAD (BRONZE) ==========
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "1. Auditoría de Datos Crudos (Bronze)", ln=True)
    pdf.ln(3)
    
    resultado_aud, num_criticas, pct_dup, memoria_mb, total_cols = auditar_calidad_bronze(df_bronze)
    
    # Métricas
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 7, f"Total de columnas: {total_cols}  |  Columnas críticas: {num_criticas}  |  Duplicados: {pct_dup:.2f}%  |  Memoria: {memoria_mb:.2f} MB", ln=True)
    pdf.ln(3)
    
    # Tabla de columnas problemáticas
    if not resultado_aud.empty:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(60, 7, "Columna", border=1)
        pdf.cell(30, 7, "% Nulos", border=1)
        pdf.cell(40, 7, "Clasificación", border=1, ln=True)
        pdf.set_font("Arial", "", 9)
        for _, row in resultado_aud.head(10).iterrows():
            pdf.cell(60, 6, row['COLUMNA'], border=1)
            pdf.cell(30, 6, f"{row['%_NULOS']:.2f}", border=1)
            pdf.cell(40, 6, row['CLASIFICACION'], border=1, ln=True)
    
    pdf.ln(5)
    # Análisis BA
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(0, 6, 
        "Análisis BA: La presencia de columnas con más del 50% de valores nulos introduce asimetría de información severa. "
        "En una microfinanciera sin automatización, estos vacíos obligan al analista a rechazar solicitudes o decidir con datos incompletos. "
        "Se recomienda aplicar reglas de imputación consistentes en la capa Silver.",
        fill=True)
    pdf.ln(5)
    
    # ========== SECCIÓN 2: TRAZABILIDAD SILVER ==========
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "2. Transformaciones y Calidad (Silver)", ln=True)
    pdf.ln(3)
    
    balance, derivadas, _ = trazabilidad_silver(df_bronze, df_silver)
    
    # Balance
    pdf.set_font("Arial", "B", 10)
    pdf.cell(60, 7, "Métrica", border=1)
    pdf.cell(40, 7, "Valor Bronze", border=1)
    pdf.cell(40, 7, "Valor Silver", border=1)
    pdf.cell(50, 7, "Variación", border=1, ln=True)
    pdf.set_font("Arial", "", 9)
    for _, row in balance.iterrows():
        pdf.cell(60, 6, row['MÉTRICA'], border=1)
        pdf.cell(40, 6, str(row['VALOR_BRONZE']), border=1)
        pdf.cell(40, 6, str(row['VALOR_SILVER']), border=1)
        pdf.cell(50, 6, str(row['VARIACIÓN']), border=1, ln=True)
    
    pdf.ln(3)
    # Variables derivadas
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 7, "Variables Derivadas", ln=True)
    # Tabla simplificada
    pdf.set_font("Arial", "B", 8)
    pdf.cell(45, 6, "Variable", border=1)
    pdf.cell(70, 6, "Fórmula", border=1)
    pdf.cell(20, 6, "Media", border=1)
    pdf.cell(20, 6, "Mediana", border=1)
    pdf.cell(20, 6, "Nulos Res.", border=1, ln=True)
    pdf.set_font("Arial", "", 8)
    for _, row in derivadas.iterrows():
        pdf.cell(45, 5, row['VARIABLE'], border=1)
        pdf.cell(70, 5, row['FÓRMULA'], border=1)
        pdf.cell(20, 5, str(row['MEDIA']), border=1)
        pdf.cell(20, 5, str(row['MEDIANA']), border=1)
        pdf.cell(20, 5, str(row['NULOS_RESIDUALES']), border=1, ln=True)
    
    pdf.ln(5)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(0, 6, 
        "Análisis BA: Las variables derivadas CREDIT_TO_INCOME_RATIO y ANNUITY_INCOME_RATIO permiten estandarizar la capacidad de pago "
        "independientemente del monto absoluto. La creación del indicador IS_EMPLOYED a través de reglas objetivas elimina la subjetividad "
        "del analista al clasificar la situación laboral del solicitante.",
        fill=True)
    pdf.ln(5)
    
    # ========== SECCIÓN 3: MÉTRICAS DE RIESGO (GOLD) ==========
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "3. Métricas de Riesgo (Gold)", ln=True)
    pdf.ln(3)
    
    # -- Gráfico 1: Tasa mora por contrato --
    fig, ax = plt.subplots(figsize=(5, 3))
    bars = ax.bar(gold_contract['TIPO_CONTRATO'], gold_contract['TASA_MORA']*100, color='steelblue')
    ax.set_title('Tasa de Morosidad por Tipo de Contrato', fontsize=10)
    ax.set_ylabel('Tasa de Mora (%)')
    ax.tick_params(axis='x', rotation=45)
    for bar, val in zip(bars, gold_contract['TASA_MORA']*100):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, f'{val:.1f}%', ha='center', fontsize=8)
    plt.tight_layout()

    # Ajustar límite superior del eje Y para que las etiquetas queden dentro
    max_val = gold_contract['TASA_MORA'].max() * 100
    ax.set_ylim(0, max_val * 1.17)

    img_buf = BytesIO()
    fig.savefig(img_buf, format='PNG', dpi=120)
    plt.close()
    img_buf.seek(0)
    pdf.image(img_buf, x=10, w=pdf.w - 20)
    
    # Tabla de datos
    pdf.ln(2)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(50, 7, "Tipo Contrato", border=1)
    pdf.cell(30, 7, "Tasa Mora", border=1)
    pdf.cell(30, 7, "Total Clientes", border=1, ln=True)
    pdf.set_font("Arial", "", 9)
    for _, row in gold_contract.iterrows():
        pdf.cell(50, 6, row['TIPO_CONTRATO'], border=1)
        pdf.cell(30, 6, f"{row['TASA_MORA']:.2%}", border=1)
        pdf.cell(30, 6, str(row['TOTAL_CLIENTES']), border=1, ln=True)
    
    pdf.ln(4)
    # Análisis BA
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(0, 6, 
        "Análisis BA: Los contratos de tipo 'Revolving' muestran la tasa de morosidad más alta. "
        "Esto sugiere que los productos de crédito rotativo requieren controles adicionales de seguimiento y quizás "
        "límites más conservadores. Los contratos 'Cash loans' presentan mejor comportamiento, posiblemente por estar "
        "respaldados por flujos de caja predecibles.",
        fill=True)
    pdf.ln(5)
    
    # -- Gráfico 2: Tasa mora por educación --
    fig, ax = plt.subplots(figsize=(5, 3))
    bars = ax.bar(gold_edu['NIVEL_EDUCATIVO'], gold_edu['TASA_MORA']*100, color='darkorange')
    ax.set_title('Tasa de Morosidad por Nivel Educativo', fontsize=10)
    ax.set_ylabel('Tasa de Mora (%)')
    ax.tick_params(axis='x', rotation=45)
    for bar, val in zip(bars, gold_edu['TASA_MORA']*100):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, f'{val:.1f}%', ha='center', fontsize=8)
    plt.tight_layout()

    # Después de crear las barras y antes de guardar la imagen
    max_val = gold_edu['TASA_MORA'].max() * 100
    ax.set_ylim(0, max_val * 1.2)

    img_buf2 = BytesIO()
    fig.savefig(img_buf2, format='PNG', dpi=120)
    plt.close()
    img_buf2.seek(0)
    pdf.image(img_buf2, x=10, w=pdf.w - 20)
    
    # Tabla
    pdf.ln(2)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(50, 7, "Nivel Educativo", border=1)
    pdf.cell(30, 7, "Tasa Mora", border=1)
    pdf.cell(30, 7, "Total Clientes", border=1, ln=True)
    pdf.set_font("Arial", "", 9)
    for _, row in gold_edu.iterrows():
        pdf.cell(50, 6, row['NIVEL_EDUCATIVO'], border=1)
        pdf.cell(30, 6, f"{row['TASA_MORA']:.2%}", border=1)
        pdf.cell(30, 6, str(row['TOTAL_CLIENTES']), border=1, ln=True)
    
    pdf.ln(4)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(0, 6, 
        "Análisis BA: La educación secundaria presenta la tasa más baja de incumplimiento, mientras que los clientes con educación "
        "primaria o inferior muestran mayor riesgo. Esta variable es un fuerte predictor y debería considerarse en el scoring final.",
        fill=True)
    pdf.ln(5)
    
    # -- Gráfico 3: Endeudamiento relativo por estado civil --
    fig, ax = plt.subplots(figsize=(5, 3))
    bars = ax.bar(gold_family['ESTADO_CIVIL'], gold_family['RAZON_CREDITO_INGRESO_PROMEDIO'], color='seagreen')
    ax.set_title('Razón Crédito/Ingreso Promedio por Estado Civil', fontsize=10)
    ax.set_ylabel('Razón Crédito/Ingreso')
    ax.tick_params(axis='x', rotation=45)
    for bar, val in zip(bars, gold_family['RAZON_CREDITO_INGRESO_PROMEDIO']):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, f'{val:.2f}', ha='center', fontsize=8)
    plt.tight_layout()

    max_val = gold_family['RAZON_CREDITO_INGRESO_PROMEDIO'].max()
    ax.set_ylim(0, max_val * 1.2)

    img_buf3 = BytesIO()
    fig.savefig(img_buf3, format='PNG', dpi=120)
    plt.close()
    img_buf3.seek(0)
    pdf.image(img_buf3, x=10, w=pdf.w - 20)
    
    pdf.ln(4)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(0, 6, 
        "Análisis BA: Los clientes solteros y viudos tienden a tener una razón crédito/ingreso más alta, lo que podría indicar "
        "una mayor carga financiera relativa. Conviene evaluar si estos segmentos requieren criterios de aprobación diferenciados.",
        fill=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", "I", 9)
    pdf.cell(0, 8, "Reporte generado automaticamente por el prototipo de Data Warehouse - Tesis I", ln=True, align="C")
    
    # Devolver el PDF como bytes
    return bytes(pdf.output(dest='S'))