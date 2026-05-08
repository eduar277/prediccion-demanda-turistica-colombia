import { useEffect, useState } from "react";
import {
  getDepartamentos,
  getHealth,
  getMetadataModelo,
  predictDepartamento,
} from "./services/api";
import "./App.css";

function App() {
  const [health, setHealth] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [departamentos, setDepartamentos] = useState([]);
  const [departamentoSeleccionado, setDepartamentoSeleccionado] = useState("ANTIOQUIA");
  const [prediccion, setPrediccion] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    cargarDatosIniciales();
  }, []);

  async function cargarDatosIniciales() {
    try {
      setError("");

      const healthData = await getHealth();
      const metadataData = await getMetadataModelo();
      const departamentosData = await getDepartamentos();

      setHealth(healthData);
      setMetadata(metadataData);
      setDepartamentos(departamentosData);

      if (departamentosData.includes("ANTIOQUIA")) {
        await generarPrediccion("ANTIOQUIA");
      }
    } catch (err) {
      console.error(err);
      setError("No se pudo conectar con el backend. Verifica que FastAPI esté corriendo en http://127.0.0.1:8000");
    }
  }

  async function generarPrediccion(departamento = departamentoSeleccionado) {
    try {
      setCargando(true);
      setError("");

      const data = await predictDepartamento(departamento);
      setPrediccion(data);
    } catch (err) {
      console.error(err);
      setError("No se pudo generar la predicción para el departamento seleccionado.");
    } finally {
      setCargando(false);
    }
  }

  function formatearNumero(valor) {
    if (valor === null || valor === undefined) return "-";
    return new Intl.NumberFormat("es-CO").format(Math.round(valor));
  }

  return (
    <main className="app">
      <section className="hero">
        <div>
          <p className="eyebrow">Sistema de IA para turismo</p>
          <h1>Predicción de demanda turística departamental</h1>
          <p className="subtitle">
            Aplicación web conectada a un modelo XGBoost entrenado para estimar
            visitantes no residentes por departamento en Colombia.
          </p>
        </div>

        <div className="status-card">
          <span className={health?.modelo_cargado ? "status ok" : "status bad"} />
          <div>
            <strong>{health?.modelo_cargado ? "Modelo cargado" : "Modelo no cargado"}</strong>
            <p>Backend FastAPI + XGBoost H6</p>
          </div>
        </div>
      </section>

      {error && <div className="alert">{error}</div>}

      <section className="grid">
        <article className="card">
          <h2>Estado del sistema</h2>
          <div className="info-list">
            <div>
              <span>API</span>
              <strong>{health?.status || "-"}</strong>
            </div>
            <div>
              <span>Modelo</span>
              <strong>{health?.modelo_cargado ? "Activo" : "No disponible"}</strong>
            </div>
            <div>
              <span>Features cargadas</span>
              <strong>{health?.features_cargadas ?? "-"}</strong>
            </div>
            <div>
              <span>GeoJSON</span>
              <strong>{health?.geojson_cargado ? "Cargado" : "No cargado"}</strong>
            </div>
          </div>
        </article>

        <article className="card">
          <h2>Metadata del modelo</h2>
          <div className="info-list">
            <div>
              <span>Modelo</span>
              <strong>{metadata?.modelo || "XGBoost Regressor"}</strong>
            </div>
            <div>
              <span>Horizonte</span>
              <strong>{metadata?.horizonte || "6 meses"}</strong>
            </div>
            <div>
              <span>wMAPE test</span>
              <strong>
                {metadata?.metricas_test?.wMAPE
                  ? `${metadata.metricas_test.wMAPE}%`
                  : "-"}
              </strong>
            </div>
            <div>
              <span>MAE test</span>
              <strong>
                {metadata?.metricas_test?.MAE
                  ? formatearNumero(metadata.metricas_test.MAE)
                  : "-"}
              </strong>
            </div>
          </div>
        </article>
      </section>

      <section className="prediction-panel">
        <div className="card">
          <h2>Generar predicción</h2>
          <p className="muted">
            Selecciona un departamento y consulta la estimación de visitantes no residentes
            a 6 meses usando el modelo guardado.
          </p>

          <div className="form-row">
            <select
              value={departamentoSeleccionado}
              onChange={(e) => setDepartamentoSeleccionado(e.target.value)}
            >
              {departamentos.map((dep) => (
                <option key={dep} value={dep}>
                  {dep}
                </option>
              ))}
            </select>

            <button onClick={() => generarPrediccion()} disabled={cargando}>
              {cargando ? "Calculando..." : "Predecir"}
            </button>
          </div>
        </div>

        <div className="card result-card">
          <h2>Resultado</h2>

          {prediccion ? (
            <>
              <p className="result-label">{prediccion.departamento}</p>
              <p className="result-number">
                {formatearNumero(prediccion.prediccion_visitantes)}
              </p>
              <p className="muted">visitantes no residentes estimados</p>

              <div className="result-details">
                <div>
                  <span>Modelo</span>
                  <strong>{prediccion.modelo}</strong>
                </div>
                <div>
                  <span>Fecha base</span>
                  <strong>{prediccion.fecha_base}</strong>
                </div>
                <div>
                  <span>Fecha predicha</span>
                  <strong>{prediccion.fecha_predicha}</strong>
                </div>
                <div>
                  <span>Horizonte</span>
                  <strong>{prediccion.horizonte}</strong>
                </div>
              </div>
            </>
          ) : (
            <p className="muted">Todavía no hay predicción generada.</p>
          )}
        </div>
      </section>
    </main>
  );
}

export default App;