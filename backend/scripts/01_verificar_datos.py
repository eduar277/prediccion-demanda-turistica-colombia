from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

ARCHIVOS_ESPERADOS = [
    "08_panel_modelo_turismo_2019_2025.csv",
    "11_panel_features_base.csv",
    "12_dataset_modelado_h6.csv",
    "colombia_departamentos_normalizado.geojson",
]


def verificar_archivos():
    print("=" * 80)
    print("VERIFICACIÓN DE ARCHIVOS DEL PROYECTO")
    print("=" * 80)

    for archivo in ARCHIVOS_ESPERADOS:
        ruta = DATA_DIR / archivo
        if ruta.exists():
            print(f"OK: {archivo}")
        else:
            print(f"FALTA: {archivo}")


def revisar_dataset_modelado():
    ruta = DATA_DIR / "12_dataset_modelado_h6.csv"

    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró: {ruta}")

    df = pd.read_csv(ruta)

    print("\n" + "=" * 80)
    print("REVISIÓN DATASET H6")
    print("=" * 80)

    print(f"Filas: {df.shape[0]}")
    print(f"Columnas: {df.shape[1]}")

    print("\nColumnas:")
    for col in df.columns:
        print(f"- {col}")

    print("\nPrimeras filas:")
    print(df.head())

    print("\nNulos principales:")
    print(df.isna().sum().sort_values(ascending=False).head(25))

    if "target" in df.columns:
        print("\nOK: existe la columna objetivo target")
    else:
        print("\nERROR: no existe la columna objetivo target")


if __name__ == "__main__":
    verificar_archivos()
    revisar_dataset_modelado()