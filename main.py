from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


# =========================================================
# CONFIGURACIÓN
# =========================================================
# esta ruta por la carpeta de archivos
INPUT_DIR = Path(r"C:\Users\edwar\OneDrive\Imágenes\Documents\Documentos\Datos")
OUTPUT_DIR = INPUT_DIR / "output_turismo"

# Nombres de archivos:
# - Extranjeros_No_Residentes_20260311.csv
# - Tasa de cambio del peso colombiano.csv
# - Registro_Nacional_de_Turismo_-_RNT_20260311.csv
# - Operaciones_aéreas_acumuladas_en_Colombia_20260311.csv
# - ISE.xlsx o ISE.csv (opcional)
# - airport_department_map.csv (opcional, para volver territorial el archivo aéreo)


# =========================================================
# UTILIDADES GENERALES
# =========================================================
MESES_MAP = {
    "ENE": 1, "FEB": 2, "MAR": 3, "ABR": 4,
    "MAY": 5, "JUN": 6, "JUL": 7, "AGO": 8,
    "SEP": 9, "OCT": 10, "NOV": 11, "DIC": 12
}

DEPT_EQUIV = {
    "BOGOTA D C": "BOGOTA",
    "BOGOTA D.C.": "BOGOTA",
    "BOGOTA D C.": "BOGOTA",
    "BOGOTA D C ": "BOGOTA",
    "BOGOTA D.C": "BOGOTA",
    "BOGOTA DC": "BOGOTA",
    "BOGOTA": "BOGOTA",
    "LA GUAJIRA": "GUAJIRA",
    "ARCHIPIELAGO DE SAN ANDRES": "SAN ANDRES Y PROVIDENCIA",
    "SAN ANDRES PROVIDENCIA Y SANTA CATALINA": "SAN ANDRES Y PROVIDENCIA",
    "SAN ANDRES Y PROVIDENCIA": "SAN ANDRES Y PROVIDENCIA",
    "VALLE DEL CAUCA": "VALLE DEL CAUCA",
    "NORTE DE SANTANDER": "NORTE DE SANTANDER",
    "SIN ESPECIFICAR": np.nan,
    "NO DETERMINADO": np.nan
}


def normalize_text(value: object) -> Optional[str]:
    """Normaliza texto: mayúsculas"""
    if pd.isna(value):
        return None

    text = str(value).strip().upper()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return DEPT_EQUIV.get(text, text)


def find_file(input_dir: Path, patterns: list[str]) -> Optional[Path]:
    """Busca un archivo en la carpeta si su nombre contiene alguno de los patrones."""
    files = list(input_dir.glob("*"))
    normalized = {normalize_text(f.name) or f.name.upper(): f for f in files}

    for pattern in patterns:
        pat_norm = normalize_text(pattern) or pattern.upper()
        for name_norm, file_path in normalized.items():
            if pat_norm in name_norm:
                return file_path
    return None


def make_month_end(year: pd.Series, month: pd.Series) -> pd.Series:
    """Convierte columnas year, month a fecha de fin de mes."""
    return pd.to_datetime({
        "year": year.astype(int),
        "month": month.astype(int),
        "day": 1
    }) + pd.offsets.MonthEnd(0)


def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


# =========================================================
# PROCESAMIENTO DE CADA FUENTE
# =========================================================
def process_enr(path: Path) -> pd.DataFrame:
    """
    Procesa Extranjeros No Residentes.
    Espera algo como:
    - AÑO
    - MES
    - DEPARTAMENTO
    - EXTRANJEROS NO RESIDENTES
    """
    print(f"[INFO] Procesando ENR: {path.name}")
    df = pd.read_csv(path, low_memory=False)

    cols_lower = {c.lower(): c for c in df.columns}
    year_col = cols_lower.get("año") or cols_lower.get("ano")
    month_col = cols_lower.get("mes")
    dept_col = cols_lower.get("departamento")
    count_col = next((c for c in df.columns if "extranjeros" in c.lower()), None)

    if not all([year_col, month_col, dept_col, count_col]):
        raise ValueError(
            "No se encontraron las columnas esperadas en Extranjeros No Residentes."
        )

    out = df[[year_col, month_col, dept_col, count_col]].copy()

    out["year"] = (
        out[year_col]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    out["year"] = pd.to_numeric(out["year"], errors="coerce")

    out["month"] = (
        out[month_col]
        .astype(str)
        .str.strip()
        .str[:3]
        .str.upper()
        .map(MESES_MAP)
    )

    out["departamento"] = out[dept_col].map(normalize_text)

    out["visitantes_no_residentes"] = pd.to_numeric(
        out[count_col].astype(str).str.replace(",", "", regex=False),
        errors="coerce"
    )

    out = out.dropna(subset=["year", "month", "departamento", "visitantes_no_residentes"])
    out["fecha_mes"] = make_month_end(out["year"], out["month"])

    out = (
        out.groupby(["departamento", "fecha_mes"], as_index=False)
        .agg(visitantes_no_residentes=("visitantes_no_residentes", "sum"))
    )

    return out


def process_trm(path: Path) -> pd.DataFrame:
    """
    Procesa TRM.
    El archivo subido venía con separador ';' y con columnas como:
    - Periodo
    - TRM
    """
    print(f"[INFO] Procesando TRM: {path.name}")
    df = pd.read_csv(path, sep=";", low_memory=False)

    date_col = next((c for c in df.columns if "periodo" in c.lower()), None)
    value_col = next((c for c in df.columns if "trm" in c.lower()), None)

    if not all([date_col, value_col]):
        raise ValueError("No se encontraron las columnas esperadas en TRM.")

    out = df[[date_col, value_col]].copy()
    out["fecha"] = pd.to_datetime(out[date_col], errors="coerce")

    # Ejemplo común en datos colombianos: 4.123,45
    out["trm"] = pd.to_numeric(
        out[value_col]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False),
        errors="coerce"
    )

    out = out.dropna(subset=["fecha", "trm"])
    out["fecha_mes"] = out["fecha"].dt.to_period("M").dt.to_timestamp("M")

    out = (
        out.groupby("fecha_mes", as_index=False)
        .agg(
            trm_promedio_mes=("trm", "mean"),
            trm_cierre_mes=("trm", "last")
        )
    )

    return out


def process_rnt(path: Path) -> pd.DataFrame:
    """
    Procesa RNT.
    La lógica:
    - filtrar ACTIVO si existe columna de estado
    - agregar por departamento y año
    - expandir a cada mes de ese año
    """
    print(f"[INFO] Procesando RNT: {path.name}")
    df = pd.read_csv(path, low_memory=False)

    year_col = next((c for c in df.columns if c.lower() in ["año", "ano"]), None)
    dept_col = next((c for c in df.columns if c.lower() == "departamento"), None)
    state_col = next((c for c in df.columns if "estado" in c.lower()), None)

    if not all([year_col, dept_col]):
        raise ValueError("No se encontraron las columnas esperadas en RNT.")

    out = df.copy()
    out["departamento"] = out[dept_col].map(normalize_text)
    out["year"] = pd.to_numeric(out[year_col], errors="coerce")

    if state_col:
        out = out[out[state_col].astype(str).str.upper().str.contains("ACTIVO", na=False)]

    out = out.dropna(subset=["departamento", "year"])

    # Variables opcionales si existen
    empleados_col = next((c for c in df.columns if "NUMERO_DE_EMPLEADOS" == c.upper()), None)
    habitaciones_col = next((c for c in df.columns if "NUMERO_DE_HABITACIONES" == c.upper()), None)
    camas_col = next((c for c in df.columns if "NUMERO_DE_CAMAS" == c.upper()), None)

    agg_dict = {
        "prestadores_turisticos_activos": ("departamento", "size")
    }

    if empleados_col:
        out[empleados_col] = pd.to_numeric(out[empleados_col], errors="coerce")
        agg_dict["empleados_rnt"] = (empleados_col, "sum")

    if habitaciones_col:
        out[habitaciones_col] = pd.to_numeric(out[habitaciones_col], errors="coerce")
        agg_dict["habitaciones_rnt"] = (habitaciones_col, "sum")

    if camas_col:
        out[camas_col] = pd.to_numeric(out[camas_col], errors="coerce")
        agg_dict["camas_rnt"] = (camas_col, "sum")

    agg = out.groupby(["departamento", "year"], as_index=False).agg(**agg_dict)

    # Expandir a los 12 meses del año
    months = pd.DataFrame({"month": range(1, 13)})
    agg = agg.merge(months, how="cross")
    agg["fecha_mes"] = make_month_end(agg["year"], agg["month"])

    return agg.drop(columns=["year", "month"])


def process_ops(path: Path, airport_map_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Procesa operaciones aéreas.
    Si existe mapa aeropuerto -> departamento, devuelve operaciones por departamento y mes.
    Si no existe, devuelve operaciones nacionales por mes.
    """
    print(f"[INFO] Procesando operaciones aéreas: {path.name}")
    df = pd.read_csv(path, low_memory=False)

    required_cols = ["ANIO", "MES", "TotalOperaciones"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas en operaciones aéreas: {missing}")

    df["ANIO"] = pd.to_numeric(df["ANIO"], errors="coerce")
    df["MES"] = pd.to_numeric(df["MES"], errors="coerce")
    df["TotalOperaciones"] = pd.to_numeric(df["TotalOperaciones"], errors="coerce")

    df = df.dropna(subset=["ANIO", "MES", "TotalOperaciones"])
    df["fecha_mes"] = make_month_end(df["ANIO"], df["MES"])

    # Caso 1: sí tenemos tabla aeropuerto -> departamento
    if airport_map_path and airport_map_path.exists():
        print(f"[INFO] Usando mapa de aeropuertos: {airport_map_path.name}")
        amap = pd.read_csv(airport_map_path)
        amap.columns = [c.lower() for c in amap.columns]

        expected = {"aeropuerto_operacion", "departamento"}
        if not expected.issubset(set(amap.columns)):
            raise ValueError(
                "El archivo airport_department_map.csv debe tener columnas "
                "'aeropuerto_operacion' y 'departamento'."
            )

        amap["departamento"] = amap["departamento"].map(normalize_text)

        merged = df.merge(
            amap,
            left_on="AEROPUERTO_OPERACION",
            right_on="aeropuerto_operacion",
            how="left"
        )

        merged = merged.dropna(subset=["departamento"])

        out = (
            merged.groupby(["departamento", "fecha_mes"], as_index=False)
            .agg(operaciones_aereas=("TotalOperaciones", "sum"))
        )
        return out

    # Caso 2: no hay mapa, se deja nacional
    out = (
        df.groupby("fecha_mes", as_index=False)
        .agg(operaciones_aereas_nacionales=("TotalOperaciones", "sum"))
    )
    return out


def process_ise(path: Path) -> pd.DataFrame:
    """
    Procesa ISE desde CSV o Excel.
    Busca columnas que contengan:
    - fecha / periodo / mes
    - ise / indice / índice
    """
    print(f"[INFO] Procesando ISE: {path.name}")

    if path.suffix.lower() in [".xlsx", ".xls"]:
        raw = pd.read_excel(path)
    else:
        raw = pd.read_csv(path, low_memory=False)

    cols_lower = [c.lower() for c in raw.columns]
    date_col = next(
        (raw.columns[i] for i, c in enumerate(cols_lower)
         if "fecha" in c or "periodo" in c or c == "mes"),
        None
    )
    value_col = next(
        (raw.columns[i] for i, c in enumerate(cols_lower)
         if "ise" in c or "indice" in c or "índice" in c),
        None
    )

    if not all([date_col, value_col]):
        raise ValueError("No se encontraron las columnas esperadas en ISE.")

    out = raw[[date_col, value_col]].copy()
    out["fecha"] = pd.to_datetime(out[date_col], errors="coerce")
    out["ise_mensual"] = pd.to_numeric(out[value_col], errors="coerce")

    out = out.dropna(subset=["fecha", "ise_mensual"])
    out["fecha_mes"] = out["fecha"].dt.to_period("M").dt.to_timestamp("M")

    out = (
        out.groupby("fecha_mes", as_index=False)
        .agg(ise_mensual=("ise_mensual", "last"))
    )

    return out


# =========================================================
# FEATURES
# =========================================================
def add_calendar_features(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()

    out["year"] = out["fecha_mes"].dt.year
    out["month"] = out["fecha_mes"].dt.month
    out["mes"] = out["month"]
    out["trimestre"] = out["fecha_mes"].dt.quarter

    out["temporada_alta_baja"] = np.where(
        out["month"].isin([1, 6, 7, 12]),
        "ALTA",
        "BAJA"
    )

    # Aproximación simple de número de festivos por mes
    # Aquí se puede reemplazar luego por un calendario oficial de Colombia.
    out["festivos_mes"] = np.where(out["month"].isin([1, 6, 12]), 2, 1)

    return out


def add_target_features(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.sort_values(["departamento", "fecha_mes"]).copy()
    group = out.groupby("departamento", group_keys=False)

    for lag in [1, 3, 6, 12]:
        out[f"lag_{lag}"] = group["visitantes_no_residentes"].shift(lag)

    for window in [3, 6, 12]:
        out[f"rolling_mean_{window}"] = (
            group["visitantes_no_residentes"]
            .shift(1)
            .rolling(window)
            .mean()
            .reset_index(level=0, drop=True)
        )

    out["var_mensual"] = group["visitantes_no_residentes"].pct_change(1)
    out["var_anual"] = group["visitantes_no_residentes"].pct_change(12)

    return out


# =========================================================
# FUNCIÓN PRINCIPAL DE CONSTRUCCIÓN DEL PANEL
# =========================================================
def build_panel(input_dir: Path, output_dir: Path) -> pd.DataFrame:
    ensure_output_dir(output_dir)

    enr_path = find_file(input_dir, ["extranjeros_no_residentes", "extranjeros no residentes"])
    trm_path = find_file(input_dir, ["tasa de cambio del peso colombiano", "trm"])
    rnt_path = find_file(input_dir, ["registro_nacional_de_turismo", "registro nacional de turismo", "rnt"])
    ops_path = find_file(input_dir, ["operaciones_aereas", "operaciones aereas", "operaciones_aereas_acumuladas"])
    ise_path = find_file(input_dir, ["ise"])
    airport_map_path = find_file(input_dir, ["airport_department_map", "aeropuerto_departamento"])

    if enr_path is None:
        raise FileNotFoundError("No encontré el archivo de Extranjeros No Residentes.")
    if trm_path is None:
        raise FileNotFoundError("No encontré el archivo de TRM.")
    if rnt_path is None:
        raise FileNotFoundError("No encontré el archivo de RNT.")

    # Procesar archivos obligatorios
    enr = process_enr(enr_path)
    trm = process_trm(trm_path)
    rnt = process_rnt(rnt_path)

    # Construcción base
    panel = (
        enr.merge(trm, on="fecha_mes", how="left")
           .merge(rnt, on=["departamento", "fecha_mes"], how="left")
    )

    # Procesar operaciones aéreas si existe
    ops_summary = None
    if ops_path is not None:
        ops_summary = process_ops(ops_path, airport_map_path)

        if "departamento" in ops_summary.columns:
            panel = panel.merge(ops_summary, on=["departamento", "fecha_mes"], how="left")
        else:
            panel = panel.merge(ops_summary, on="fecha_mes", how="left")

    # Procesar ISE si existe
    ise = None
    if ise_path is not None:
        try:
            ise = process_ise(ise_path)
            panel = panel.merge(ise, on="fecha_mes", how="left")
        except Exception as exc:
            print(f"[ADVERTENCIA] No se pudo procesar ISE: {exc}")

    # Features
    panel = add_calendar_features(panel)
    panel = add_target_features(panel)

    panel = panel.sort_values(["departamento", "fecha_mes"]).reset_index(drop=True)

    # Guardar resultados intermedios
    enr.to_csv(output_dir / "target_enr_departamento_mes.csv", index=False)
    trm.to_csv(output_dir / "trm_mensual.csv", index=False)
    rnt.to_csv(output_dir / "rnt_departamento_mes.csv", index=False)

    if ops_summary is not None:
        ops_summary.to_csv(output_dir / "operaciones_aereas_transformadas.csv", index=False)

    if ise is not None:
        ise.to_csv(output_dir / "ise_mensual.csv", index=False)

    panel.to_csv(output_dir / "panel_modelo_turismo.csv", index=False)

    resumen = pd.DataFrame([{
        "filas_panel": len(panel),
        "departamentos_panel": int(panel["departamento"].nunique()),
        "fecha_min": str(panel["fecha_mes"].min().date()),
        "fecha_max": str(panel["fecha_mes"].max().date()),
        "tiene_ise": bool(ise is not None),
        "ops_por_departamento": bool(ops_summary is not None and "departamento" in ops_summary.columns)
    }])
    resumen.to_csv(output_dir / "resumen_preparacion.csv", index=False)

    return panel


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    pd.set_option("display.max_columns", None)

    print("[INFO] Iniciando preparación de datos...")
    panel = build_panel(INPUT_DIR, OUTPUT_DIR)

    print("\n[OK] Panel construido correctamente")
    print(f"Filas: {len(panel):,}")
    print(f"Departamentos: {panel['departamento'].nunique()}")
    print(f"Periodo: {panel['fecha_mes'].min().date()} a {panel['fecha_mes'].max().date()}")
    print(f"Archivo principal: {OUTPUT_DIR / 'panel_modelo_turismo.csv'}")