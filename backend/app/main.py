from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.services.model_service import service


app = FastAPI(
    title="API Predicción Demanda Turística Colombia",
    description="Backend para predicción de visitantes no residentes por departamento usando XGBoost.",
    version="1.0.0",
)


# Permite que React pueda conectarse al backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    """
    Al iniciar la API se carga:
    - modelo XGBoost
    - columnas del modelo
    - metadata
    - panel histórico
    - predicciones
    - GeoJSON
    """
    service.load_all()


@app.get("/")
def root():
    return {
        "mensaje": "API de predicción de demanda turística funcionando",
        "modelo": "XGBoost horizonte 6 meses",
    }


@app.get("/health")
def health():
    return service.get_health()


@app.get("/modelo/metadata")
def modelo_metadata():
    return service.get_metadata()


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
def predicciones(departamento: str | None = None):
    return service.get_predicciones(departamento=departamento)


@app.get("/predicciones/mapa")
def predicciones_mapa():
    return service.get_predicciones_mapa()


@app.get("/historico/{departamento}")
def historico_departamento(departamento: str):
    datos = service.get_historico_departamento(departamento)

    if not datos:
        raise HTTPException(status_code=404, detail=f"No hay histórico para {departamento}")

    return datos


@app.post("/predict/{departamento}")
def predict_departamento(departamento: str):
    try:
        return service.predict_departamento(departamento)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))