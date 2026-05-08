from pathlib import Path
import json
import joblib

import numpy as np
import pandas as pd

from sklearn.metrics import mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
OUTPUTS_DIR = BASE_DIR / "outputs"

MODELS_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)

DATASET_PATH = DATA_DIR / "12_dataset_modelado_h6.csv"

MODEL_PATH = MODELS_DIR / "xgboost_h6_model.joblib"
FEATURES_PATH = MODELS_DIR / "xgboost_h6_features.json"
METADATA_PATH = MODELS_DIR / "xgboost_h6_metadata.json"
PREDICTIONS_PATH = OUTPUTS_DIR / "predicciones_xgboost_h6_generadas.csv"

# En tu archivo, la variable objetivo se llama target.
TARGET = "target"


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


def cargar_datos():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"No se encontró el dataset: {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH)

    if "fecha" not in df.columns:
        raise ValueError("El dataset debe tener una columna llamada 'fecha'.")

    if "departamento" not in df.columns:
        raise ValueError("El dataset debe tener una columna llamada 'departamento'.")

    if TARGET not in df.columns:
        raise ValueError(f"No existe la columna objetivo: {TARGET}")

    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df.dropna(subset=[TARGET]).copy()

    return df


def preparar_matriz_modelo(df):
    # Convertimos departamento en variables dummy para que XGBoost pueda usarlo.
    df_modelo = pd.get_dummies(df, columns=["departamento"], drop_first=False)

    columnas_excluir = [
        "fecha",
        "target",
        "target_h_1",
        "target_h_3",
        "target_h_6",
        "target_h_12",
    ]

    columnas_excluir = [col for col in columnas_excluir if col in df_modelo.columns]

    X = df_modelo.drop(columns=columnas_excluir)
    y = df_modelo[TARGET]

    # Nos quedamos solo con variables numéricas o booleanas.
    X = X.select_dtypes(include=["number", "bool"]).copy()

    # Convertimos booleanos a 0/1.
    for col in X.select_dtypes(include=["bool"]).columns:
        X[col] = X[col].astype(int)

    # Reemplazamos infinitos por NaN.
    X = X.replace([np.inf, -np.inf], np.nan)

    # Eliminamos columnas completamente vacías.
    X = X.dropna(axis=1, how="all")

    # Imputamos nulos restantes con la mediana.
    # Esto aplica especialmente a algunas variaciones porcentuales iniciales.
    X = X.fillna(X.median(numeric_only=True))

    return X, y


def entrenar():
    print("=" * 80)
    print("ENTRENAMIENTO MODELO XGBOOST H6")
    print("=" * 80)

    df = cargar_datos()

    print(f"Dataset cargado: {df.shape[0]} filas x {df.shape[1]} columnas")
    print(f"Rango fechas: {df['fecha'].min()} a {df['fecha'].max()}")

    X, y = preparar_matriz_modelo(df)

    fechas = df["fecha"]

    # Split temporal: entrenamos con datos antes de 2025 y probamos con 2025.
    X_train = X[fechas < "2025-01-01"]
    y_train = y[fechas < "2025-01-01"]

    X_test = X[fechas >= "2025-01-01"]
    y_test = y[fechas >= "2025-01-01"]

    df_test = df.loc[fechas >= "2025-01-01", ["fecha", "departamento", TARGET]].copy()

    print(f"Features usadas: {X.shape[1]}")
    print(f"Train: {X_train.shape[0]} filas")
    print(f"Test: {X_test.shape[0]} filas")

    if X_train.empty or X_test.empty:
        raise ValueError("Train o test quedó vacío. Revisa el rango de fechas.")

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

    mae = mean_absolute_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred) ** 0.5
    mape = mape_seguro(y_test, y_pred)
    wmape_value = wmape(y_test, y_pred)

    print("\nMÉTRICAS TEST 2025")
    print(f"MAE:   {mae:.2f}")
    print(f"RMSE:  {rmse:.2f}")
    print(f"MAPE:  {mape:.2f}%")
    print(f"wMAPE: {wmape_value:.2f}%")

    df_pred = df_test.copy()
    df_pred["prediccion"] = y_pred
    df_pred["error"] = df_pred[TARGET] - df_pred["prediccion"]
    df_pred["error_abs"] = df_pred["error"].abs()

    df_pred.to_csv(PREDICTIONS_PATH, index=False, encoding="utf-8-sig")

    joblib.dump(modelo, MODEL_PATH)

    feature_columns = X.columns.tolist()

    with open(FEATURES_PATH, "w", encoding="utf-8") as f:
        json.dump(feature_columns, f, ensure_ascii=False, indent=2)

    metadata = {
        "modelo": "XGBoost Regressor",
        "horizonte": "6 meses",
        "target": TARGET,
        "descripcion": "Modelo para predicción de visitantes no residentes por departamento a 6 meses.",
        "fecha_train_max": str(df.loc[fechas < "2025-01-01", "fecha"].max()),
        "fecha_test_min": str(df.loc[fechas >= "2025-01-01", "fecha"].min()),
        "fecha_test_max": str(df.loc[fechas >= "2025-01-01", "fecha"].max()),
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

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("\nARCHIVOS GENERADOS")
    print(f"Modelo:       {MODEL_PATH}")
    print(f"Features:     {FEATURES_PATH}")
    print(f"Metadata:     {METADATA_PATH}")
    print(f"Predicciones: {PREDICTIONS_PATH}")

    print("\nFase de entrenamiento completada correctamente.")


if __name__ == "__main__":
    entrenar()