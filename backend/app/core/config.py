from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
OUTPUTS_DIR = BASE_DIR / "outputs"


PANEL_PATH = DATA_DIR / "08_panel_modelo_turismo_2019_2025.csv"
GEOJSON_PATH = DATA_DIR / "colombia_departamentos_normalizado.geojson"


HORIZONTES = {
    "h1": {
        "label": "1 mes",
        "meses": 1,
        "dataset_path": DATA_DIR / "12_dataset_modelado_h1.csv",
        "model_path": MODELS_DIR / "xgboost_h1_model.joblib",
        "features_path": MODELS_DIR / "xgboost_h1_features.json",
        "metadata_path": MODELS_DIR / "xgboost_h1_metadata.json",
        "predictions_path": OUTPUTS_DIR / "predicciones_xgboost_h1_generadas.csv",
    },
    "h3": {
        "label": "3 meses",
        "meses": 3,
        "dataset_path": DATA_DIR / "12_dataset_modelado_h3.csv",
        "model_path": MODELS_DIR / "xgboost_h3_model.joblib",
        "features_path": MODELS_DIR / "xgboost_h3_features.json",
        "metadata_path": MODELS_DIR / "xgboost_h3_metadata.json",
        "predictions_path": OUTPUTS_DIR / "predicciones_xgboost_h3_generadas.csv",
    },
    "h6": {
        "label": "6 meses",
        "meses": 6,
        "dataset_path": DATA_DIR / "12_dataset_modelado_h6.csv",
        "model_path": MODELS_DIR / "xgboost_h6_model.joblib",
        "features_path": MODELS_DIR / "xgboost_h6_features.json",
        "metadata_path": MODELS_DIR / "xgboost_h6_metadata.json",
        "predictions_path": OUTPUTS_DIR / "predicciones_xgboost_h6_generadas.csv",
    },
    "h12": {
        "label": "12 meses",
        "meses": 12,
        "dataset_path": DATA_DIR / "12_dataset_modelado_h12.csv",
        "model_path": MODELS_DIR / "xgboost_h12_model.joblib",
        "features_path": MODELS_DIR / "xgboost_h12_features.json",
        "metadata_path": MODELS_DIR / "xgboost_h12_metadata.json",
        "predictions_path": OUTPUTS_DIR / "predicciones_xgboost_h12_generadas.csv",
    },
}



DEFAULT_HORIZON = "h6"

MODEL_PATH = HORIZONTES[DEFAULT_HORIZON]["model_path"]
FEATURES_PATH = HORIZONTES[DEFAULT_HORIZON]["features_path"]
METADATA_PATH = HORIZONTES[DEFAULT_HORIZON]["metadata_path"]
DATASET_H6_PATH = HORIZONTES[DEFAULT_HORIZON]["dataset_path"]
PREDICTIONS_PATH = HORIZONTES[DEFAULT_HORIZON]["predictions_path"]