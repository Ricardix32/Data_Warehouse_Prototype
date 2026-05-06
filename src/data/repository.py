from abc import ABC, abstractmethod
import pandas as pd
import sqlite3
from typing import Optional

class DataRepository(ABC):
    """Interfaz abstracta para el almacenamiento del Data Warehouse."""

    @abstractmethod
    def save_bronze(self, df: pd.DataFrame) -> None:
        """Guardar datos crudos (Bronze)."""
        ...

    @abstractmethod
    def get_bronze(self) -> pd.DataFrame:
        """Recuperar datos crudos (Bronze)."""
        ...

    @abstractmethod
    def save_silver(self, df: pd.DataFrame) -> None:
        """Guardar datos transformados (Silver)."""
        ...

    @abstractmethod
    def get_silver(self) -> pd.DataFrame:
        """Recuperar datos transformados (Silver)."""
        ...

    @abstractmethod
    def save_gold_tables(self, contract: pd.DataFrame, edu: pd.DataFrame, family: pd.DataFrame) -> None:
        """Guardar las tres tablas de métricas (Gold)."""
        ...

    @abstractmethod
    def get_gold_contract(self) -> pd.DataFrame:
        """Recuperar tabla de riesgo por contrato (Gold)."""
        ...

    @abstractmethod
    def get_gold_edu(self) -> pd.DataFrame:
        """Recuperar tabla de riesgo por educación (Gold)."""
        ...

    @abstractmethod
    def get_gold_family(self) -> pd.DataFrame:
        """Recuperar tabla de riesgo por familia (Gold)."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Cerrar la conexión o liberar recursos."""
        ...


class SQLiteRepository(DataRepository):
    """Implementación concreta del repositorio sobre SQLite."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)

    def save_bronze(self, df: pd.DataFrame) -> None:
        df.to_sql('bronze_application_train', self.conn, if_exists='replace', index=False)

    def get_bronze(self) -> pd.DataFrame:
        return pd.read_sql_query("SELECT * FROM bronze_application_train", self.conn)

    def save_silver(self, df: pd.DataFrame) -> None:
        df.to_sql('silver_application_train', self.conn, if_exists='replace', index=False)

    def get_silver(self) -> pd.DataFrame:
        return pd.read_sql_query("SELECT * FROM silver_application_train", self.conn)

    def save_gold_tables(self, contract: pd.DataFrame, edu: pd.DataFrame, family: pd.DataFrame) -> None:
        contract.to_sql('gold_risk_contract', self.conn, if_exists='replace', index=False)
        edu.to_sql('gold_risk_education', self.conn, if_exists='replace', index=False)
        family.to_sql('gold_risk_family', self.conn, if_exists='replace', index=False)

    def get_gold_contract(self) -> pd.DataFrame:
        return pd.read_sql_query("SELECT * FROM gold_risk_contract", self.conn)

    def get_gold_edu(self) -> pd.DataFrame:
        return pd.read_sql_query("SELECT * FROM gold_risk_education", self.conn)

    def get_gold_family(self) -> pd.DataFrame:
        return pd.read_sql_query("SELECT * FROM gold_risk_family", self.conn)

    def close(self) -> None:
        self.conn.close()