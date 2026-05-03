# 🏦 Data Warehouse para Riesgo Crediticio – Prototipo Interactivo

**Tesis:** *“Arquitectura de Data Warehouse y analítica predictiva para la evaluación de riesgo crediticio en instituciones microfinancieras”*  
**Autores:** Montenegro Baca & Rodriguez Preciado | **Asesor:** Dr. Santos Fernandez  
**Colaboración Técnica:** DeepSeek Expert (asesor de tesis), Google Gemini Pro

---

## 📖 Sobre el prototipo

Este proyecto materializa el **pipeline ETL y la arquitectura de Data Warehouse** descritos en la investigación. Utilizando el dataset público **Home Credit Default Risk** de Kaggle, se implementa un flujo de tres capas (Bronze, Silver, Gold) dentro de una aplicación **Streamlit** que permite:

- Visualizar datos crudos (Bronze) → ingesta sin modificación.
- Explorar datos limpios y transformados (Silver) → imputaciones y variables derivadas de capacidad de pago.
- Consultar métricas agregadas de riesgo (Gold) → tasas de mora por segmentos, listas para modelos.

---

## 🧠 Vinculación con la tesis

| Capa | Rol en la investigación | Variable clave en el prototipo |
|------|--------------------------|--------------------------------|
| **Bronze** | Reemplaza la recepción manual de documentos físicos (boletas, estados de cuenta) y centraliza la información. | `application_train.csv` completo (simula documentos digitalizados) |
| **Silver** | Automatiza el cálculo de la **capacidad de endeudamiento** (objetivo general de la tesis). | `CREDIT_TO_INCOME_RATIO`, `ANNUITY_INCOME_RATIO` (reemplazan cálculos manuales en Excel) |
| **Gold** | Prepara métricas para analítica predictiva y reportes de riesgo institucional. | `bad_rate` por tipo de contrato, educación, estado civil. |

El prototipo también **mide la reducción de latencia** mostrando el tiempo de procesamiento de cada capa, lo que evidencia la mejora frente al método manual (objetivo específico 4 de la tesis).

---

## 🚀 Ejecución local

1. Clona este repositorio o descarga los archivos.
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
