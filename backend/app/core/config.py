from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
OUTPUTS_DIR = BASE_DIR / "outputs"

MODEL_PATH = MODELS_DIR / "xgboost_h6_model.joblib"
FEATURES_PATH = MODELS_DIR / "xgboost_h6_features.json"
METADATA_PATH = MODELS_DIR / "xgboost_h6_metadata.json"

PANEL_PATH = DATA_DIR / "08_panel_modelo_turismo_2019_2025.csv"
DATASET_H6_PATH = DATA_DIR / "12_dataset_modelado_h6.csv"
GEOJSON_PATH = DATA_DIR / "colombia_departamentos_normalizado.geojson"

PREDICTIONS_PATH = OUTPUTS_DIR / "predicciones_xgboost_h6_generadas.csv"