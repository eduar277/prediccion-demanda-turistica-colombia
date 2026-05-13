import json

import joblib
import numpy as np
import pandas as pd

from app.core.config import (
    PANEL_PATH,
    GEOJSON_PATH,
    HORIZONTES,
    DEFAULT_HORIZON,
)


class TourismPredictionService:
    def __init__(self):
        self.models = {}
        self.feature_columns = {}
        self.metadata = {}
        self.datasets = {}
        self.predictions = {}

        self.panel = None
        self.geojson = None

    def load_all(self):
        """
        Carga todos los modelos, features, metadata, datasets,
        predicciones, panel histórico y GeoJSON.
        """
        self.load_models()
        self.load_data()
        return True

    def validar_horizonte(self, horizonte):
        """
        Valida que el horizonte solicitado exista.
        """
        horizonte = horizonte.lower().strip()

        if horizonte not in HORIZONTES:
            disponibles = ", ".join(HORIZONTES.keys())
            raise ValueError(
                f"Horizonte no válido: {horizonte}. Horizontes disponibles: {disponibles}"
            )

        return horizonte

    def load_models(self):
        """
        Carga los modelos XGBoost, las columnas esperadas
        y la metadata para cada horizonte.
        """
        for horizonte, config in HORIZONTES.items():
            model_path = config["model_path"]
            features_path = config["features_path"]
            metadata_path = config["metadata_path"]

            if not model_path.exists():
                raise FileNotFoundError(f"No se encontró el modelo: {model_path}")

            if not features_path.exists():
                raise FileNotFoundError(f"No se encontró el archivo de features: {features_path}")

            if not metadata_path.exists():
                raise FileNotFoundError(f"No se encontró la metadata: {metadata_path}")

            self.models[horizonte] = joblib.load(model_path)

            with open(features_path, "r", encoding="utf-8") as f:
                self.feature_columns[horizonte] = json.load(f)

            with open(metadata_path, "r", encoding="utf-8") as f:
                self.metadata[horizonte] = json.load(f)

    def load_data(self):
        """
        Carga los datasets por horizonte, predicciones generadas,
        panel histórico y GeoJSON.
        """
        if PANEL_PATH.exists():
            self.panel = pd.read_csv(PANEL_PATH)
            self.panel["fecha"] = pd.to_datetime(self.panel["fecha"])

        if GEOJSON_PATH.exists():
            with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
                self.geojson = json.load(f)

        for horizonte, config in HORIZONTES.items():
            dataset_path = config["dataset_path"]
            predictions_path = config["predictions_path"]

            if dataset_path.exists():
                df_dataset = pd.read_csv(dataset_path)
                df_dataset["fecha"] = pd.to_datetime(df_dataset["fecha"])
                self.datasets[horizonte] = df_dataset

            if predictions_path.exists():
                df_pred = pd.read_csv(predictions_path)
                df_pred["fecha"] = pd.to_datetime(df_pred["fecha"])

                if "fecha_predicha" in df_pred.columns:
                    df_pred["fecha_predicha"] = pd.to_datetime(df_pred["fecha_predicha"])

                self.predictions[horizonte] = df_pred

    def get_health(self):
        """
        Devuelve estado general del backend y de los artefactos cargados.
        """
        horizontes_estado = {}

        for horizonte in HORIZONTES.keys():
            horizontes_estado[horizonte] = {
                "modelo_cargado": horizonte in self.models,
                "features_cargadas": len(self.feature_columns.get(horizonte, [])),
                "metadata_cargada": horizonte in self.metadata,
                "dataset_cargado": horizonte in self.datasets,
                "predicciones_cargadas": horizonte in self.predictions,
            }

        return {
            "status": "ok",
            "horizonte_default": DEFAULT_HORIZON,
            "panel_cargado": self.panel is not None,
            "geojson_cargado": self.geojson is not None,
            "horizontes": horizontes_estado,
            # Compatibilidad con frontend anterior:
            "modelo_cargado": DEFAULT_HORIZON in self.models,
            "features_cargadas": len(self.feature_columns.get(DEFAULT_HORIZON, [])),
            "dataset_h6_cargado": DEFAULT_HORIZON in self.datasets,
            "predicciones_cargadas": DEFAULT_HORIZON in self.predictions,
        }

    def get_horizontes(self):
        """
        Devuelve los horizontes disponibles para el frontend.
        """
        salida = []

        for horizonte, config in HORIZONTES.items():
            meta = self.metadata.get(horizonte, {})
            metricas = meta.get("metricas_test", {})

            salida.append(
                {
                    "id": horizonte,
                    "label": config["label"],
                    "meses": config["meses"],
                    "modelo_cargado": horizonte in self.models,
                    "dataset_cargado": horizonte in self.datasets,
                    "predicciones_cargadas": horizonte in self.predictions,
                    "metricas_test": metricas,
                }
            )

        return salida

    def get_metadata(self, horizonte=DEFAULT_HORIZON):
        """
        Devuelve metadata de un horizonte específico.
        """
        horizonte = self.validar_horizonte(horizonte)
        return self.metadata.get(horizonte, {})

    def get_metadata_all(self):
        """
        Devuelve metadata de todos los horizontes.
        """
        return self.metadata

    def get_departamentos(self):
        """
        Devuelve la lista de departamentos disponibles en el panel.
        """
        if self.panel is None:
            return []

        return sorted(self.panel["departamento"].dropna().unique().tolist())

    def get_geojson(self):
        """
        Devuelve GeoJSON de departamentos.
        """
        return self.geojson

    def get_predicciones(self, horizonte=DEFAULT_HORIZON, departamento=None):
        """
        Devuelve predicciones generadas por horizonte.
        Puede filtrar por departamento.
        """
        horizonte = self.validar_horizonte(horizonte)

        if horizonte not in self.predictions:
            return []

        df = self.predictions[horizonte].copy()

        if departamento:
            departamento = departamento.upper().strip()
            df = df[df["departamento"].str.upper().str.strip() == departamento]

        df["fecha"] = df["fecha"].dt.strftime("%Y-%m-%d")

        if "fecha_predicha" in df.columns:
            df["fecha_predicha"] = df["fecha_predicha"].dt.strftime("%Y-%m-%d")

        return df.to_dict(orient="records")

    def get_predicciones_mapa(self, horizonte=DEFAULT_HORIZON):
        """
        Devuelve las predicciones para pintar el mapa,
        usando la fecha predicha más reciente disponible.
        """
        horizonte = self.validar_horizonte(horizonte)

        if horizonte not in self.predictions:
            return []

        df = self.predictions[horizonte].copy()

        if "fecha_predicha" in df.columns:
            fecha_ref = df["fecha_predicha"].max()
            df = df[df["fecha_predicha"] == fecha_ref].copy()
        else:
            fecha_ref = df["fecha"].max()
            df = df[df["fecha"] == fecha_ref].copy()

        df["fecha"] = df["fecha"].dt.strftime("%Y-%m-%d")

        if "fecha_predicha" in df.columns:
            df["fecha_predicha"] = df["fecha_predicha"].dt.strftime("%Y-%m-%d")

        columnas = [
            "fecha",
            "fecha_predicha",
            "departamento",
            "target",
            "prediccion",
            "error_abs",
            "horizonte",
            "meses_horizonte",
        ]

        columnas = [col for col in columnas if col in df.columns]

        return df[columnas].to_dict(orient="records")

    def get_historico_departamento(self, departamento):
        """
        Devuelve histórico del panel para un departamento.
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

    def preparar_features_ultima_fila(self, departamento, horizonte=DEFAULT_HORIZON):
        """
        Toma la última fila disponible del departamento para el horizonte indicado
        y la transforma para que coincida con las columnas usadas al entrenar.
        """
        horizonte = self.validar_horizonte(horizonte)

        if horizonte not in self.datasets:
            raise ValueError(f"No está cargado el dataset para {horizonte}")

        departamento = departamento.upper().strip()

        df = self.datasets[horizonte].copy()
        df = df[df["departamento"].str.upper().str.strip() == departamento]

        if df.empty:
            raise ValueError(
                f"No hay datos para el departamento {departamento} en el horizonte {horizonte}"
            )

        df = df.sort_values("fecha")
        ultima = df.tail(1).copy()

        ultima_modelo = pd.get_dummies(ultima, columns=["departamento"], drop_first=False)

        columnas_excluir = [
            "fecha",
            "fecha_predicha",
            "target",
            "target_h_1",
            "target_h_3",
            "target_h_6",
            "target_h_12",
        ]

        columnas_excluir = [col for col in columnas_excluir if col in ultima_modelo.columns]

        X = ultima_modelo.drop(columns=columnas_excluir)
        X = X.select_dtypes(include=["number", "bool"]).copy()

        for col in X.select_dtypes(include=["bool"]).columns:
            X[col] = X[col].astype(int)

        X = X.replace([np.inf, -np.inf], np.nan)

        expected_features = self.feature_columns[horizonte]

        for col in expected_features:
            if col not in X.columns:
                X[col] = 0

        X = X[expected_features]
        X = X.fillna(0)

        fecha_base = ultima["fecha"].iloc[0]

        return X, fecha_base

    def predict_departamento(self, departamento, horizonte=DEFAULT_HORIZON):
        """
        Genera predicción para un departamento y un horizonte específico.
        """
        horizonte = self.validar_horizonte(horizonte)

        if horizonte not in self.models:
            raise ValueError(f"Modelo no cargado para el horizonte {horizonte}")

        config = HORIZONTES[horizonte]
        meses = config["meses"]

        X, fecha_base = self.preparar_features_ultima_fila(
            departamento=departamento,
            horizonte=horizonte,
        )

        pred = float(self.models[horizonte].predict(X)[0])
        pred = max(pred, 0)

        fecha_predicha = fecha_base + pd.DateOffset(months=meses)

        return {
            "departamento": departamento.upper().strip(),
            "modelo": f"XGBoost {horizonte.upper()}",
            "horizonte": horizonte,
            "horizonte_label": config["label"],
            "meses_horizonte": meses,
            "fecha_base": fecha_base.strftime("%Y-%m-%d"),
            "fecha_predicha": fecha_predicha.strftime("%Y-%m-%d"),
            "prediccion_visitantes": round(pred, 2),
            "descripcion": "Predicción estimada de visitantes no residentes para el departamento seleccionado.",
        }

    def get_periodos_disponibles(self):
        """
        Devuelve los periodos disponibles en el panel histórico.
        Formato: YYYY-MM.
        """
        if self.panel is None:
            return []

        if "fecha" not in self.panel.columns:
            return []

        df = self.panel.copy()
        df["periodo"] = df["fecha"].dt.to_period("M").astype(str)

        return sorted(df["periodo"].dropna().unique().tolist())

    def comparar_periodos(self, fecha_a, fecha_b):
        """
        Compara la demanda turística entre dos periodos mensuales.

        Parámetros:
        - fecha_a: periodo base, por ejemplo 2024-07 o 2024-07-01.
        - fecha_b: periodo de comparación, por ejemplo 2025-07 o 2025-07-01.

        Retorna:
        - valor en fecha_a
        - valor en fecha_b
        - diferencia absoluta
        - variación porcentual
        - estado de crecimiento por departamento
        """
        if self.panel is None:
            return []

        if "visitantes_no_residentes" not in self.panel.columns:
            raise ValueError(
                "El panel no tiene la columna 'visitantes_no_residentes'."
            )

        df = self.panel.copy()

        df["fecha"] = pd.to_datetime(df["fecha"])
        df["periodo"] = df["fecha"].dt.to_period("M")

        periodo_a = pd.to_datetime(fecha_a).to_period("M")
        periodo_b = pd.to_datetime(fecha_b).to_period("M")

        fecha_a_ref = periodo_a.to_timestamp().strftime("%Y-%m-%d")
        fecha_b_ref = periodo_b.to_timestamp().strftime("%Y-%m-%d")

        valor_col = "visitantes_no_residentes"

        df_a = (
            df[df["periodo"] == periodo_a]
            .groupby("departamento", as_index=False)[valor_col]
            .sum(min_count=1)
            .rename(columns={valor_col: "valor_a"})
        )

        df_b = (
            df[df["periodo"] == periodo_b]
            .groupby("departamento", as_index=False)[valor_col]
            .sum(min_count=1)
            .rename(columns={valor_col: "valor_b"})
        )

        comparacion = pd.merge(df_a, df_b, on="departamento", how="outer")

        comparacion["diferencia"] = comparacion["valor_b"] - comparacion["valor_a"]

        comparacion["variacion_pct"] = np.where(
            (comparacion["valor_a"].notna()) & (comparacion["valor_a"] != 0),
            (comparacion["diferencia"] / comparacion["valor_a"]) * 100,
            np.nan,
        )

        def clasificar_estado(row):
            if pd.isna(row["valor_a"]) or pd.isna(row["valor_b"]):
                return "sin_dato"

            if row["diferencia"] > 0:
                return "crecimiento"

            if row["diferencia"] < 0:
                return "disminucion"

            return "sin_cambio"

        comparacion["estado"] = comparacion.apply(clasificar_estado, axis=1)

        comparacion = comparacion.sort_values(
            by="variacion_pct",
            ascending=False,
            na_position="last",
        )

        def limpiar_numero(valor):
            if pd.isna(valor):
                return None

            return round(float(valor), 4)

        salida = []

        for _, row in comparacion.iterrows():
            salida.append(
                {
                    "departamento": row["departamento"],
                    "fecha_a": fecha_a_ref,
                    "fecha_b": fecha_b_ref,
                    "periodo_a": str(periodo_a),
                    "periodo_b": str(periodo_b),
                    "valor_a": limpiar_numero(row["valor_a"]),
                    "valor_b": limpiar_numero(row["valor_b"]),
                    "diferencia": limpiar_numero(row["diferencia"]),
                    "variacion_pct": limpiar_numero(row["variacion_pct"]),
                    "estado": row["estado"],
                }
            )

        return salida
    def _resumen_dataframe(self, nombre, df):
        """
        Genera un resumen estándar de calidad para un DataFrame.
        """
        if df is None:
            return {
                "nombre": nombre,
                "cargado": False,
                "filas": 0,
                "columnas": 0,
                "duplicados": 0,
                "nulos_totales": 0,
                "porcentaje_nulos": 0,
                "columnas_con_nulos": [],
                "columnas": [],
                "rango_fechas": None,
                "departamentos": 0,
            }

        filas, columnas = df.shape
        duplicados = int(df.duplicated().sum())
        nulos_totales = int(df.isna().sum().sum())
        total_celdas = filas * columnas if filas and columnas else 0
        porcentaje_nulos = (nulos_totales / total_celdas * 100) if total_celdas else 0

        columnas_con_nulos = []

        for col in df.columns:
            nulos = int(df[col].isna().sum())
            if nulos > 0:
                columnas_con_nulos.append(
                    {
                        "columna": col,
                        "nulos": nulos,
                        "porcentaje": round((nulos / filas) * 100, 4) if filas else 0,
                    }
                )

        columnas_con_nulos = sorted(
            columnas_con_nulos,
            key=lambda item: item["nulos"],
            reverse=True,
        )[:15]

        rango_fechas = None

        if "fecha" in df.columns:
            fechas = pd.to_datetime(df["fecha"], errors="coerce")
            if fechas.notna().sum() > 0:
                rango_fechas = {
                    "min": fechas.min().strftime("%Y-%m-%d"),
                    "max": fechas.max().strftime("%Y-%m-%d"),
                }

        departamentos = 0

        if "departamento" in df.columns:
            departamentos = int(df["departamento"].dropna().nunique())

        return {
            "nombre": nombre,
            "cargado": True,
            "filas": int(filas),
            "columnas": int(columnas),
            "duplicados": duplicados,
            "nulos_totales": nulos_totales,
            "porcentaje_nulos": round(float(porcentaje_nulos), 4),
            "columnas_con_nulos": columnas_con_nulos,
            "columnas": df.columns.tolist(),
            "rango_fechas": rango_fechas,
            "departamentos": departamentos,
        }

    def _duplicados_clave_temporal(self, df):
        """
        Evalúa duplicados por clave lógica departamento-fecha.
        """
        if df is None:
            return None

        if "fecha" not in df.columns or "departamento" not in df.columns:
            return None

        duplicados = int(df.duplicated(subset=["fecha", "departamento"]).sum())

        return {
            "clave": ["fecha", "departamento"],
            "duplicados": duplicados,
        }

    def _analizar_desbalance_territorial(self):
        """
        Calcula desbalance territorial usando visitantes_no_residentes
        del panel histórico.
        """
        if self.panel is None:
            return None

        if "departamento" not in self.panel.columns:
            return None

        if "visitantes_no_residentes" not in self.panel.columns:
            return None

        df = self.panel.copy()
        df["visitantes_no_residentes"] = pd.to_numeric(
            df["visitantes_no_residentes"],
            errors="coerce",
        )

        resumen = (
            df.groupby("departamento", as_index=False)["visitantes_no_residentes"]
            .sum(min_count=1)
            .dropna()
        )

        if resumen.empty:
            return None

        total = resumen["visitantes_no_residentes"].sum()

        resumen["participacion_pct"] = np.where(
            total > 0,
            resumen["visitantes_no_residentes"] / total * 100,
            np.nan,
        )

        resumen = resumen.sort_values(
            "visitantes_no_residentes",
            ascending=False,
        )

        max_valor = float(resumen["visitantes_no_residentes"].max())
        min_valor = float(resumen["visitantes_no_residentes"].min())
        promedio = float(resumen["visitantes_no_residentes"].mean())
        mediana = float(resumen["visitantes_no_residentes"].median())

        razon_max_min = max_valor / min_valor if min_valor > 0 else None

        return {
            "total_visitantes": round(float(total), 4),
            "departamentos": int(resumen["departamento"].nunique()),
            "maximo": round(max_valor, 4),
            "minimo": round(min_valor, 4),
            "promedio": round(promedio, 4),
            "mediana": round(mediana, 4),
            "razon_max_min": round(float(razon_max_min), 4) if razon_max_min else None,
            "top_demanda": resumen.head(5).to_dict(orient="records"),
            "menor_demanda": resumen.tail(5).to_dict(orient="records"),
        }

    def get_calidad_datos(self):
        """
        Devuelve resumen de calidad de datos para el dashboard.
        """
        panel_resumen = self._resumen_dataframe(
            "Panel histórico 2019-2025",
            self.panel,
        )

        panel_resumen["duplicados_clave_temporal"] = self._duplicados_clave_temporal(
            self.panel
        )

        datasets = []

        for horizonte, df in self.datasets.items():
            item = self._resumen_dataframe(
                f"Dataset modelado {horizonte.upper()}",
                df,
            )
            item["horizonte"] = horizonte
            item["duplicados_clave_temporal"] = self._duplicados_clave_temporal(df)
            datasets.append(item)

        predicciones = []

        for horizonte, df in self.predictions.items():
            item = self._resumen_dataframe(
                f"Predicciones {horizonte.upper()}",
                df,
            )
            item["horizonte"] = horizonte
            item["duplicados_clave_temporal"] = self._duplicados_clave_temporal(df)
            predicciones.append(item)

        geojson_info = {
            "cargado": self.geojson is not None,
            "features": 0,
        }

        if self.geojson is not None and isinstance(self.geojson, dict):
            geojson_info["features"] = len(self.geojson.get("features", []))

        return {
            "estado": "ok",
            "panel": panel_resumen,
            "datasets_modelado": sorted(datasets, key=lambda x: x["horizonte"]),
            "predicciones": sorted(predicciones, key=lambda x: x["horizonte"]),
            "geojson": geojson_info,
            "desbalance_territorial": self._analizar_desbalance_territorial(),
            "criterios_calidad": [
                "Validación de carga de archivos requeridos.",
                "Conteo de filas y columnas.",
                "Revisión de valores faltantes.",
                "Revisión de duplicados generales.",
                "Revisión de duplicados por fecha y departamento.",
                "Validación de cobertura temporal.",
                "Validación de cobertura territorial.",
                "Análisis de desbalance territorial de la demanda.",
                "Verificación de artefactos por horizonte de predicción.",
            ],
        }
service = TourismPredictionService()

