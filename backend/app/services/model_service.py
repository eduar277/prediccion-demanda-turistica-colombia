import json

import joblib
import numpy as np
import pandas as pd

from app.core.config import (
    MODEL_PATH,
    FEATURES_PATH,
    METADATA_PATH,
    PANEL_PATH,
    DATASET_H6_PATH,
    GEOJSON_PATH,
    PREDICTIONS_PATH,
)


class TourismPredictionService:
    def __init__(self):
        self.model = None
        self.feature_columns = []
        self.metadata = {}
        self.panel = None
        self.dataset_h6 = None
        self.predictions = None
        self.geojson = None

    def load_all(self):
        """
        Carga el modelo, las columnas esperadas, la metadata,
        los datasets y el GeoJSON necesarios para la API.
        """
        self.load_model()
        self.load_data()
        return True

    def load_model(self):
        """
        Carga el modelo XGBoost guardado, la lista de features
        usadas durante el entrenamiento y la metadata del modelo.
        """
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"No se encontró el modelo: {MODEL_PATH}")

        if not FEATURES_PATH.exists():
            raise FileNotFoundError(f"No se encontró el archivo de features: {FEATURES_PATH}")

        if not METADATA_PATH.exists():
            raise FileNotFoundError(f"No se encontró la metadata: {METADATA_PATH}")

        self.model = joblib.load(MODEL_PATH)

        with open(FEATURES_PATH, "r", encoding="utf-8") as f:
            self.feature_columns = json.load(f)

        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

    def load_data(self):
        """
        Carga los archivos de datos necesarios:
        - panel histórico limpio
        - dataset de modelado H6
        - predicciones generadas
        - GeoJSON de departamentos
        """
        if PANEL_PATH.exists():
            self.panel = pd.read_csv(PANEL_PATH)
            self.panel["fecha"] = pd.to_datetime(self.panel["fecha"])

        if DATASET_H6_PATH.exists():
            self.dataset_h6 = pd.read_csv(DATASET_H6_PATH)
            self.dataset_h6["fecha"] = pd.to_datetime(self.dataset_h6["fecha"])

        if PREDICTIONS_PATH.exists():
            self.predictions = pd.read_csv(PREDICTIONS_PATH)
            self.predictions["fecha"] = pd.to_datetime(self.predictions["fecha"])

        if GEOJSON_PATH.exists():
            with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
                self.geojson = json.load(f)

    def get_health(self):
        """
        Devuelve el estado general del servicio.
        Sirve para verificar si el backend cargó correctamente.
        """
        return {
            "status": "ok",
            "modelo_cargado": self.model is not None,
            "features_cargadas": len(self.feature_columns),
            "panel_cargado": self.panel is not None,
            "dataset_h6_cargado": self.dataset_h6 is not None,
            "predicciones_cargadas": self.predictions is not None,
            "geojson_cargado": self.geojson is not None,
        }

    def get_metadata(self):
        """
        Devuelve la metadata del modelo:
        métricas, horizonte, número de features, fechas de prueba, etc.
        """
        return self.metadata

    def get_departamentos(self):
        """
        Devuelve la lista de departamentos disponibles en el panel.
        """
        if self.panel is None:
            return []

        departamentos = sorted(self.panel["departamento"].dropna().unique().tolist())
        return departamentos

    def get_geojson(self):
        """
        Devuelve el GeoJSON de departamentos de Colombia.
        """
        return self.geojson

    def get_predicciones(self, departamento=None):
        """
        Devuelve las predicciones generadas.
        Puede filtrar por departamento.
        """
        if self.predictions is None:
            return []

        df = self.predictions.copy()

        if departamento:
            departamento = departamento.upper().strip()
            df = df[df["departamento"].str.upper().str.strip() == departamento]

        df["fecha"] = df["fecha"].dt.strftime("%Y-%m-%d")

        return df.to_dict(orient="records")

    def get_predicciones_mapa(self):
        """
        Devuelve las predicciones para el mapa.
        Usa la fecha más reciente disponible en el archivo de predicciones.
        """
        if self.predictions is None:
            return []

        df = self.predictions.copy()

        fecha_max = df["fecha"].max()
        df = df[df["fecha"] == fecha_max].copy()

        df["fecha"] = df["fecha"].dt.strftime("%Y-%m-%d")

        columnas = ["fecha", "departamento", "target", "prediccion", "error_abs"]
        columnas = [col for col in columnas if col in df.columns]

        return df[columnas].to_dict(orient="records")

    def get_historico_departamento(self, departamento):
        """
        Devuelve la serie histórica de un departamento.
        Se usará en React para graficar comportamiento histórico.
        """
        if self.panel is None:
            return []

        departamento = departamento.upper().strip()

        df = self.panel.copy()
        df = df[df["departamento"].str.upper().str.strip() == departamento]
        df = df.sort_values("fecha")

        columnas = [
            "fecha",
            "departamento",
            "visitantes_no_residentes",
            "pasajeros_aereos_nacionales",
            "pasajeros_aereos_internacionales",
            "prestadores_activos",
            "trm",
            "ise",
        ]

        columnas = [col for col in columnas if col in df.columns]

        df["fecha"] = df["fecha"].dt.strftime("%Y-%m-%d")

        return df[columnas].to_dict(orient="records")

    def preparar_features_ultima_fila(self, departamento):
        """
        Toma la última fila disponible de un departamento en el dataset H6
        y la transforma para que tenga exactamente las mismas columnas
        usadas durante el entrenamiento del modelo.
        """
        if self.dataset_h6 is None:
            raise ValueError("No está cargado el dataset H6.")

        departamento = departamento.upper().strip()

        df = self.dataset_h6.copy()
        df = df[df["departamento"].str.upper().str.strip() == departamento]

        if df.empty:
            raise ValueError(f"No hay datos para el departamento: {departamento}")

        df = df.sort_values("fecha")
        ultima = df.tail(1).copy()

        # Convertimos departamento en variables dummy, igual que en entrenamiento.
        ultima_modelo = pd.get_dummies(ultima, columns=["departamento"], drop_first=False)

        columnas_excluir = [
            "fecha",
            "target",
            "target_h_1",
            "target_h_3",
            "target_h_6",
            "target_h_12",
        ]

        columnas_excluir = [col for col in columnas_excluir if col in ultima_modelo.columns]

        X = ultima_modelo.drop(columns=columnas_excluir)

        # Dejamos solo variables numéricas y booleanas.
        X = X.select_dtypes(include=["number", "bool"]).copy()

        # Convertimos booleanos a 0/1.
        for col in X.select_dtypes(include=["bool"]).columns:
            X[col] = X[col].astype(int)

        # Reemplazamos infinitos por NaN.
        X = X.replace([np.inf, -np.inf], np.nan)

        # Agregamos columnas faltantes para respetar exactamente
        # la estructura usada durante el entrenamiento.
        for col in self.feature_columns:
            if col not in X.columns:
                X[col] = 0

        # Reordenamos las columnas exactamente como espera el modelo.
        X = X[self.feature_columns]

        # En predicción puntual, cualquier faltante residual se reemplaza por 0.
        X = X.fillna(0)

        fecha_base = ultima["fecha"].iloc[0]

        return X, fecha_base

    def predict_departamento(self, departamento):
        """
        Genera una predicción a 6 meses para el departamento indicado,
        usando la última fila disponible del dataset H6.
        """
        if self.model is None:
            raise ValueError("Modelo no cargado.")

        X, fecha_base = self.preparar_features_ultima_fila(departamento)

        pred = float(self.model.predict(X)[0])

        # La demanda turística no puede ser negativa.
        pred = max(pred, 0)

        fecha_predicha = fecha_base + pd.DateOffset(months=6)

        return {
            "departamento": departamento.upper().strip(),
            "modelo": "XGBoost H6",
            "horizonte": "6 meses",
            "fecha_base": fecha_base.strftime("%Y-%m-%d"),
            "fecha_predicha": fecha_predicha.strftime("%Y-%m-%d"),
            "prediccion_visitantes": round(pred, 2),
            "descripcion": "Predicción estimada de visitantes no residentes para el departamento seleccionado.",
        }


service = TourismPredictionService()