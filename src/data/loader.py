import pandas as pd
import os
import logging
from config.settings import Settings   # solo para el tipo, no crea acoplamiento

logger = logging.getLogger(__name__)

def load_raw_dataset(settings: Settings) -> pd.DataFrame:
    """
    Carga el dataset crudo respetando la configuración.
    
    1. Si settings.gdrive_url no está vacío y el archivo local no existe, lo descarga.
    2. Luego carga el CSV local.
    3. Si ninguna fuente funciona, lanza FileNotFoundError.
    """
    # 1. Descargar si es necesario
    _download_if_needed(settings.gdrive_url, settings.csv_filename)
    
    # 2. Cargar el CSV
    if not os.path.exists(settings.csv_filename):
        raise FileNotFoundError(
            f"No se encontró el archivo '{settings.csv_filename}'. "
            "Asegúrese de que la URL de Google Drive sea válida o coloque el CSV manualmente."
        )
    df = pd.read_csv(settings.csv_filename)
    logger.info(f"Dataset cargado: {len(df)} filas, {len(df.columns)} columnas.")
    return df

def _download_if_needed(gdrive_url: str, local_filename: str) -> None:
    """Descarga el archivo desde Google Drive si hace falta."""
    if not gdrive_url:
        logger.info("No se proporcionó URL de Google Drive. Se usará archivo local si existe.")
        return
    if os.path.exists(local_filename):
        logger.info(f"El archivo '{local_filename}' ya existe. Se omite la descarga.")
        return
    try:
        import gdown
        logger.info("Descargando dataset desde Google Drive...")
        gdown.download(gdrive_url, local_filename, quiet=False)
        logger.info("Descarga completada.")
    except ImportError:
        raise ImportError("La biblioteca 'gdown' no está instalada. No se puede descargar el dataset.")
    except Exception as e:
        raise RuntimeError(f"Error al descargar el dataset desde Google Drive: {e}")