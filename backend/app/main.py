from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import DEFAULT_HORIZON
from app.services.model_service import service


app = FastAPI(
    title="API Predicción Demanda Turística Colombia",
    description="Backend para predicción de visitantes no residentes por departamento usando modelos XGBoost multihorizonte.",
    version="2.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    service.load_all()


@app.get("/")
def root():
    return {
        "mensaje": "API de predicción de demanda turística funcionando",
        "modelo": "XGBoost multihorizonte",
        "horizonte_default": DEFAULT_HORIZON,
    }


@app.get("/health")
def health():
    return service.get_health()


@app.get("/horizontes")
def horizontes():
    return service.get_horizontes()


@app.get("/modelo/metadata")
def modelo_metadata(horizonte: str = DEFAULT_HORIZON):
    try:
        return service.get_metadata(horizonte)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/modelo/metadata/all")
def modelo_metadata_all():
    return service.get_metadata_all()


@app.get("/modelo/metadata/{horizonte}")
def modelo_metadata_horizonte(horizonte: str):
    try:
        return service.get_metadata(horizonte)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/departamentos")
def departamentos():
    return service.get_departamentos()


@app.get("/geojson")
def geojson():
    data = service.get_geojson()

    if data is None:
        raise HTTPException(status_code=404, detail="GeoJSON no encontrado")

    return data


@app.get("/predicciones")
def predicciones(
    horizonte: str = DEFAULT_HORIZON,
    departamento: Optional[str] = None,
):
    try:
        return service.get_predicciones(
            horizonte=horizonte,
            departamento=departamento,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/predicciones/mapa")
def predicciones_mapa(horizonte: str = DEFAULT_HORIZON):
    try:
        return service.get_predicciones_mapa(horizonte=horizonte)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/predicciones/mapa/{horizonte}")
def predicciones_mapa_horizonte(horizonte: str):
    try:
        return service.get_predicciones_mapa(horizonte=horizonte)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/predicciones/{horizonte}")
def predicciones_horizonte(
    horizonte: str,
    departamento: Optional[str] = None,
):
    try:
        return service.get_predicciones(
            horizonte=horizonte,
            departamento=departamento,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/historico/{departamento}")
def historico_departamento(departamento: str):
    datos = service.get_historico_departamento(departamento)

    if not datos:
        raise HTTPException(status_code=404, detail=f"No hay histórico para {departamento}")

    return datos


# Endpoint anterior para compatibilidad. Usa H6 por defecto.
@app.post("/predict/{departamento}")
def predict_departamento_default(departamento: str):
    try:
        return service.predict_departamento(
            departamento=departamento,
            horizonte=DEFAULT_HORIZON,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Nuevo endpoint multihorizonte.
@app.post("/predict/{horizonte}/{departamento}")
def predict_departamento_horizonte(horizonte: str, departamento: str):
    try:
        return service.predict_departamento(
            departamento=departamento,
            horizonte=horizonte,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))