from pathlib import Path
import json
import joblib

import numpy as np
import pandas as pd

from sklearn.metrics import mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor


# ============================================================
# RUTAS BASE
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
OUTPUTS_DIR = BASE_DIR / "outputs"

MODELS_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

TARGET = "target"
TEST_START = pd.Timestamp("2025-01-01")

HORIZONTES = {
    "h1": {
        "meses": 1,
        "dataset": "12_dataset_modelado_h1.csv",
        "descripcion": "Predicción de visitantes no residentes a 1 mes.",
    },
    "h3": {
        "meses": 3,
        "dataset": "12_dataset_modelado_h3.csv",
        "descripcion": "Predicción de visitantes no residentes a 3 meses.",
    },
    "h6": {
        "meses": 6,
        "dataset": "12_dataset_modelado_h6.csv",
        "descripcion": "Predicción de visitantes no residentes a 6 meses.",
    },
    "h12": {
        "meses": 12,
        "dataset": "12_dataset_modelado_h12.csv",
        "descripcion": "Predicción de visitantes no residentes a 12 meses.",
    },
}


# ============================================================
# MÉTRICAS
# ============================================================

def wmape(y_true, y_pred):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    denominador = np.sum(np.abs(y_true))

    if denominador == 0:
        return np.nan

    return np.sum(np.abs(y_true - y_pred)) / denominador * 100


def mape_seguro(y_true, y_pred):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    mascara = y_true != 0

    if mascara.sum() == 0:
        return np.nan

    return np.mean(np.abs((y_true[mascara] - y_pred[mascara]) / y_true[mascara])) * 100


# ============================================================
# CARGA Y VALIDACIÓN DE DATOS
# ============================================================

def cargar_dataset(nombre_archivo):
    ruta = DATA_DIR / nombre_archivo

    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el archivo requerido: {ruta}")

    df = pd.read_csv(ruta)

    columnas_requeridas = ["fecha", "departamento", TARGET]

    for columna in columnas_requeridas:
        if columna not in df.columns:
            raise ValueError(
                f"El archivo {nombre_archivo} no tiene la columna requerida: {columna}"
            )

    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df.dropna(subset=[TARGET]).copy()

    return df


def agregar_fecha_predicha(df, meses_horizonte):
    """
    Crea la fecha real que el modelo está intentando predecir.

    Ejemplo:
    - H1: fecha base 2024-12 -> fecha predicha 2025-01
    - H3: fecha base 2024-10 -> fecha predicha 2025-01
    - H6: fecha base 2024-07 -> fecha predicha 2025-01
    - H12: fecha base 2024-01 -> fecha predicha 2025-01
    """

    df = df.copy()
    df["fecha_predicha"] = df["fecha"].apply(
        lambda fecha: fecha + pd.DateOffset(months=meses_horizonte)
    )
    return df


def preparar_matriz_modelo(df):
    """
    Convierte el dataset tabular en matriz X e y para XGBoost.

    Pasos:
    - Convierte departamento a variables dummy.
    - Elimina fecha, fecha_predicha y target.
    - Conserva variables numéricas y booleanas.
    - Convierte booleanos a 0/1.
    - Reemplaza infinitos.
    - Elimina columnas vacías.
    - Imputa faltantes residuales con mediana.
    """

    df_modelo = pd.get_dummies(df, columns=["departamento"], drop_first=False)

    columnas_excluir = [
        "fecha",
        "fecha_predicha",
        "target",
        "target_h_1",
        "target_h_3",
        "target_h_6",
        "target_h_12",
    ]

    columnas_excluir = [col for col in columnas_excluir if col in df_modelo.columns]

    X = df_modelo.drop(columns=columnas_excluir)
    y = df_modelo[TARGET]

    X = X.select_dtypes(include=["number", "bool"]).copy()

    for col in X.select_dtypes(include=["bool"]).columns:
        X[col] = X[col].astype(int)

    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.dropna(axis=1, how="all")
    X = X.fillna(X.median(numeric_only=True))

    return X, y


# ============================================================
# ENTRENAMIENTO POR HORIZONTE
# ============================================================

def entrenar_horizonte(nombre_horizonte, config):
    print("\n" + "=" * 90)
    print(f"ENTRENANDO MODELO XGBOOST {nombre_horizonte.upper()}")
    print("=" * 90)

    dataset_nombre = config["dataset"]
    meses = config["meses"]

    df = cargar_dataset(dataset_nombre)
    df = agregar_fecha_predicha(df, meses)

    print(f"Dataset: {dataset_nombre}")
    print(f"Filas: {df.shape[0]}")
    print(f"Columnas: {df.shape[1]}")
    print(f"Rango fecha base: {df['fecha'].min()} a {df['fecha'].max()}")
    print(f"Rango fecha predicha: {df['fecha_predicha'].min()} a {df['fecha_predicha'].max()}")

    X, y = preparar_matriz_modelo(df)

    # ========================================================
    # SPLIT TEMPORAL CORRECTO POR FECHA PREDICHA
    # ========================================================
    # Entrenamiento:
    #   Casos cuya fecha objetivo predicha es anterior a 2025.
    #
    # Prueba:
    #   Casos cuya fecha objetivo predicha pertenece a 2025 o posterior.
    #
    # Esto evita el problema de H12, donde la fecha base está en 2024
    # pero la fecha predicha corresponde a 2025.
    # ========================================================

    train_mask = df["fecha_predicha"] < TEST_START
    test_mask = df["fecha_predicha"] >= TEST_START

    X_train = X[train_mask]
    y_train = y[train_mask]

    X_test = X[test_mask]
    y_test = y[test_mask]

    df_test = df.loc[
        test_mask,
        ["fecha", "fecha_predicha", "departamento", TARGET]
    ].copy()

    print(f"Features usadas: {X.shape[1]}")
    print(f"Train: {X_train.shape[0]} filas")
    print(f"Test: {X_test.shape[0]} filas")

    if X_train.empty:
        raise ValueError(f"El conjunto de entrenamiento quedó vacío para {nombre_horizonte}")

    if X_test.empty:
        raise ValueError(f"El conjunto de prueba quedó vacío para {nombre_horizonte}")

    print(f"Train fecha predicha: {df.loc[train_mask, 'fecha_predicha'].min()} a {df.loc[train_mask, 'fecha_predicha'].max()}")
    print(f"Test fecha predicha: {df.loc[test_mask, 'fecha_predicha'].min()} a {df.loc[test_mask, 'fecha_predicha'].max()}")

    modelo = XGBRegressor(
        n_estimators=400,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="reg:squarederror",
        random_state=42,
        n_jobs=-1,
    )

    modelo.fit(X_train, y_train)

    y_pred = modelo.predict(X_test)
    y_pred = np.clip(y_pred, 0, None)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred) ** 0.5
    mape = mape_seguro(y_test, y_pred)
    wmape_value = wmape(y_test, y_pred)

    print("\nMÉTRICAS TEST")
    print(f"MAE:   {mae:.2f}")
    print(f"RMSE:  {rmse:.2f}")
    print(f"MAPE:  {mape:.2f}%")
    print(f"wMAPE: {wmape_value:.2f}%")

    # ========================================================
    # GUARDAR PREDICCIONES
    # ========================================================

    df_pred = df_test.copy()
    df_pred["prediccion"] = y_pred
    df_pred["error"] = df_pred[TARGET] - df_pred["prediccion"]
    df_pred["error_abs"] = df_pred["error"].abs()
    df_pred["horizonte"] = nombre_horizonte
    df_pred["meses_horizonte"] = meses

    predicciones_path = OUTPUTS_DIR / f"predicciones_xgboost_{nombre_horizonte}_generadas.csv"
    df_pred.to_csv(predicciones_path, index=False, encoding="utf-8-sig")

    # ========================================================
    # GUARDAR MODELO Y ARTEFACTOS
    # ========================================================

    model_path = MODELS_DIR / f"xgboost_{nombre_horizonte}_model.joblib"
    features_path = MODELS_DIR / f"xgboost_{nombre_horizonte}_features.json"
    metadata_path = MODELS_DIR / f"xgboost_{nombre_horizonte}_metadata.json"

    joblib.dump(modelo, model_path)

    feature_columns = X.columns.tolist()

    with open(features_path, "w", encoding="utf-8") as f:
        json.dump(feature_columns, f, ensure_ascii=False, indent=2)

    metadata = {
        "modelo": "XGBoost Regressor",
        "horizonte": nombre_horizonte,
        "meses_horizonte": meses,
        "target": TARGET,
        "descripcion": config["descripcion"],
        "dataset_entrenamiento": dataset_nombre,
        "criterio_split": "Split temporal por fecha_predicha. Train: fecha_predicha < 2025-01-01. Test: fecha_predicha >= 2025-01-01.",
        "fecha_base_min": str(df["fecha"].min()),
        "fecha_base_max": str(df["fecha"].max()),
        "fecha_predicha_min": str(df["fecha_predicha"].min()),
        "fecha_predicha_max": str(df["fecha_predicha"].max()),
        "fecha_train_predicha_min": str(df.loc[train_mask, "fecha_predicha"].min()),
        "fecha_train_predicha_max": str(df.loc[train_mask, "fecha_predicha"].max()),
        "fecha_test_predicha_min": str(df.loc[test_mask, "fecha_predicha"].min()),
        "fecha_test_predicha_max": str(df.loc[test_mask, "fecha_predicha"].max()),
        "filas_train": int(X_train.shape[0]),
        "filas_test": int(X_test.shape[0]),
        "n_features": int(len(feature_columns)),
        "metricas_test": {
            "MAE": round(float(mae), 4),
            "RMSE": round(float(rmse), 4),
            "MAPE": round(float(mape), 4),
            "wMAPE": round(float(wmape_value), 4),
        },
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("\nARCHIVOS GENERADOS")
    print(f"Modelo:       {model_path}")
    print(f"Features:     {features_path}")
    print(f"Metadata:     {metadata_path}")
    print(f"Predicciones: {predicciones_path}")

    return {
        "horizonte": nombre_horizonte,
        "meses_horizonte": meses,
        "dataset": dataset_nombre,
        "filas": int(df.shape[0]),
        "features": int(X.shape[1]),
        "train": int(X_train.shape[0]),
        "test": int(X_test.shape[0]),
        "fecha_base_min": str(df["fecha"].min().date()),
        "fecha_base_max": str(df["fecha"].max().date()),
        "fecha_predicha_min": str(df["fecha_predicha"].min().date()),
        "fecha_predicha_max": str(df["fecha_predicha"].max().date()),
        "MAE": round(float(mae), 4),
        "RMSE": round(float(rmse), 4),
        "MAPE": round(float(mape), 4),
        "wMAPE": round(float(wmape_value), 4),
    }


# ============================================================
# EJECUCIÓN PRINCIPAL
# ============================================================

def main():
    resumen = []

    for nombre_horizonte, config in HORIZONTES.items():
        resultado = entrenar_horizonte(nombre_horizonte, config)
        resumen.append(resultado)

    df_resumen = pd.DataFrame(resumen)

    resumen_path = OUTPUTS_DIR / "metricas_xgboost_multihorizonte.csv"
    df_resumen.to_csv(resumen_path, index=False, encoding="utf-8-sig")

    print("\n" + "=" * 90)
    print("RESUMEN FINAL DE MODELOS XGBOOST MULTIHORIZONTE")
    print("=" * 90)
    print(df_resumen)

    print("\nResumen guardado en:")
    print(resumen_path)

    print("\nEntrenamiento multihorizonte completado correctamente.")


if __name__ == "__main__":
    main()