import { useEffect, useMemo, useState } from "react";
import {
  getDepartamentos,
  getGeojson,
  getHealth,
  getHorizontes,
  getMetadataModelo,
  getPrediccionesMapa,
  predictDepartamento,
  getHistoricoDepartamento,
  getPeriodosDisponibles,
} from "./services/api";
import TourismMap from "./components/TourismMap";
import "./App.css";
import DepartmentChart from "./components/DepartmentChart";
import HorizonComparison from "./components/HorizonComparison";
import PeriodComparison from "./components/PeriodComparison";
function App() {
  const [health, setHealth] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [horizontes, setHorizontes] = useState([]);

  const [departamentos, setDepartamentos] = useState([]);
  const [departamentoSeleccionado, setDepartamentoSeleccionado] =
    useState("ANTIOQUIA");

  const [horizonteSeleccionado, setHorizonteSeleccionado] = useState("h6");

  const [prediccion, setPrediccion] = useState(null);
  const [geojson, setGeojson] = useState(null);
  const [prediccionesMapa, setPrediccionesMapa] = useState([]);

  const [cargando, setCargando] = useState(false);
  const [cargandoInicial, setCargandoInicial] = useState(true);
  const [error, setError] = useState("");
  const [historicoDepartamento, setHistoricoDepartamento] = useState([]);
  const [periodosDisponibles, setPeriodosDisponibles] = useState([]);
  useEffect(() => {
    cargarDatosIniciales();
  }, []);

  async function cargarDatosIniciales() {
    try {
      setError("");
      setCargandoInicial(true);

      const [
  healthData,
  horizontesData,
  departamentosData,
  geojsonData,
  periodosData,
] = await Promise.all([
  getHealth(),
  getHorizontes(),
  getDepartamentos(),
  getGeojson(),
  getPeriodosDisponibles(),
]);

      setHealth(healthData);
      setHorizontes(horizontesData);
      setDepartamentos(departamentosData);
      setGeojson(geojsonData);
      setPeriodosDisponibles(periodosData);
      const departamentoInicial = departamentosData.includes("ANTIOQUIA")
        ? "ANTIOQUIA"
        : departamentosData[0];

      setDepartamentoSeleccionado(departamentoInicial);

      await Promise.all([
  cargarDatosHorizonte("h6", departamentoInicial),
  cargarHistoricoDepartamento(departamentoInicial),
]);
    } catch (err) {
      console.error(err);
      setError(
        "No se pudo conectar con el backend. Verifica que FastAPI esté corriendo en http://127.0.0.1:8000"
      );
    } finally {
      setCargandoInicial(false);
    }
  }

  async function cargarDatosHorizonte(horizonte, departamento) {
    try {
      setCargando(true);
      setError("");

      const [metadataData, prediccionesMapaData, prediccionData] =
        await Promise.all([
          getMetadataModelo(horizonte),
          getPrediccionesMapa(horizonte),
          predictDepartamento(departamento, horizonte),
        ]);

      setMetadata(metadataData);
      setPrediccionesMapa(prediccionesMapaData);
      setPrediccion(prediccionData);
    } catch (err) {
      console.error(err);
      setError("No se pudieron cargar los datos para el horizonte seleccionado.");
    } finally {
      setCargando(false);
    }
  }

  async function cambiarHorizonte(nuevoHorizonte) {
    setHorizonteSeleccionado(nuevoHorizonte);
    await cargarDatosHorizonte(nuevoHorizonte, departamentoSeleccionado);
  }

  async function generarPrediccion(
    departamento = departamentoSeleccionado,
    horizonte = horizonteSeleccionado
  ) {
    try {
      setCargando(true);
      setError("");

      const data = await predictDepartamento(departamento, horizonte);
      setPrediccion(data);
    } catch (err) {
      console.error(err);
      setError(
        "No se pudo generar la predicción para el departamento seleccionado."
      );
    } finally {
      setCargando(false);
    }
  }
async function cargarHistoricoDepartamento(departamento) {
  try {
    const historico = await getHistoricoDepartamento(departamento);
    setHistoricoDepartamento(historico);
  } catch (err) {
    console.error(err);
    setHistoricoDepartamento([]);
  }
}
  async function seleccionarDepartamento(departamento) {
  setDepartamentoSeleccionado(departamento);

  await Promise.all([
    generarPrediccion(departamento, horizonteSeleccionado),
    cargarHistoricoDepartamento(departamento),
  ]);
}

  async function seleccionarDesdeMapa(departamento) {
    await seleccionarDepartamento(departamento);
  }

  function formatearNumero(valor) {
    if (valor === null || valor === undefined || Number.isNaN(Number(valor))) {
      return "-";
    }

    return new Intl.NumberFormat("es-CO").format(Math.round(Number(valor)));
  }

  function formatearDecimal(valor, decimales = 2) {
    if (valor === null || valor === undefined || Number.isNaN(Number(valor))) {
      return "-";
    }

    return Number(valor).toFixed(decimales);
  }

  const horizonteActivo = useMemo(() => {
    return (
      horizontes.find((item) => item.id === horizonteSeleccionado) || {
        id: "h6",
        label: "6 meses",
        meses: 6,
      }
    );
  }, [horizontes, horizonteSeleccionado]);

  const fechaMapa = useMemo(() => {
    if (!prediccionesMapa.length) return "-";
    return prediccionesMapa[0]?.fecha_predicha || prediccionesMapa[0]?.fecha || "-";
  }, [prediccionesMapa]);

  const topDepartamentos = useMemo(() => {
    return [...prediccionesMapa]
      .filter((item) => item.prediccion !== null && item.prediccion !== undefined)
      .sort((a, b) => Number(b.prediccion) - Number(a.prediccion))
      .slice(0, 5);
  }, [prediccionesMapa]);

  const totalPredicho = useMemo(() => {
    return prediccionesMapa.reduce((acc, item) => {
      const valor = Number(item.prediccion);
      return acc + (Number.isNaN(valor) ? 0 : valor);
    }, 0);
  }, [prediccionesMapa]);

  const wmape = metadata?.metricas_test?.wMAPE;
  const mae = metadata?.metricas_test?.MAE;
  const rmse = metadata?.metricas_test?.RMSE;
  const mape = metadata?.metricas_test?.MAPE;

  return (
    <main className="app">
      <header className="topbar">
        <div>
          <p className="eyebrow">Sistema de IA para turismo</p>
          <h1>Predicción de demanda turística departamental</h1>
          <p className="subtitle">
            Dashboard conectado a FastAPI y modelos XGBoost multihorizonte para
            estimar visitantes no residentes por departamento en Colombia.
          </p>
        </div>

        <div className="topbar-actions">
          <span className={health?.modelo_cargado ? "pill online" : "pill offline"}>
            {health?.modelo_cargado ? "Modelo activo" : "Modelo no disponible"}
          </span>
          <span className="pill">XGBoost multihorizonte</span>
        </div>
      </header>

      {error && <div className="alert">{error}</div>}

      <section className="toolbar-card">
        <div>
          <p className="section-kicker">Horizonte de predicción</p>
          <h2>Selecciona el plazo de análisis</h2>
        </div>

        <div className="horizon-switch">
          {horizontes.map((horizonte) => (
            <button
              key={horizonte.id}
              className={
                horizonteSeleccionado === horizonte.id
                  ? "horizon-button active"
                  : "horizon-button"
              }
              onClick={() => cambiarHorizonte(horizonte.id)}
              disabled={cargando || cargandoInicial}
            >
              {horizonte.label}
            </button>
          ))}
        </div>
      </section>

      <section className="kpi-grid">
        <article className="kpi-card accent">
          <span className="kpi-label">Predicción total mapa</span>
          <strong className="kpi-value">{formatearNumero(totalPredicho)}</strong>
          <p>Visitantes estimados para la fecha activa del mapa</p>
        </article>

        <article className="kpi-card">
          <span className="kpi-label">wMAPE test</span>
          <strong className="kpi-value">
            {wmape ? `${formatearDecimal(wmape, 2)}%` : "-"}
          </strong>
          <p>Error porcentual ponderado del horizonte seleccionado</p>
        </article>

        <article className="kpi-card">
          <span className="kpi-label">Horizonte activo</span>
          <strong className="kpi-value">{horizonteActivo.label}</strong>
          <p>Modelo actualmente usado para predicción</p>
        </article>

        <article className="kpi-card">
          <span className="kpi-label">Departamentos</span>
          <strong className="kpi-value">{departamentos.length || "-"}</strong>
          <p>Territorios disponibles en el sistema</p>
        </article>
      </section>
      <section className="horizon-comparison-section">
  <HorizonComparison
    horizontes={horizontes}
    horizonteSeleccionado={horizonteSeleccionado}
    onSelectHorizonte={cambiarHorizonte}
  />
      </section>
      <section className="main-grid">
        <section className="map-panel">
          <TourismMap
            geojson={geojson}
            prediccionesMapa={prediccionesMapa}
            onSelectDepartamento={seleccionarDesdeMapa}
          />
        </section>

        <aside className="side-panel">
          <article className="card prediction-card">
            <div className="section-heading">
              <div>
                <p className="section-kicker">Consulta individual</p>
                <h2>Generar predicción</h2>
              </div>
            </div>

            <p className="muted">
              Selecciona un departamento y un horizonte para consultar la
              estimación de visitantes no residentes.
            </p>

            <div className="form-group">
              <label>Departamento</label>
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
            </div>

            <div className="form-group">
              <label>Horizonte</label>
              <select
                value={horizonteSeleccionado}
                onChange={(e) => cambiarHorizonte(e.target.value)}
              >
                {horizontes.map((h) => (
                  <option key={h.id} value={h.id}>
                    {h.label}
                  </option>
                ))}
              </select>
            </div>

            <button
              className="primary-button"
              onClick={() =>
                generarPrediccion(
                  departamentoSeleccionado,
                  horizonteSeleccionado
                )
              }
              disabled={cargando || cargandoInicial}
            >
              {cargando ? "Calculando..." : "Predecir demanda"}
            </button>
          </article>

          <article className="card result-card">
            <p className="section-kicker">Resultado del modelo</p>

            {prediccion ? (
              <>
                <h2>{prediccion.departamento}</h2>
                <div className="big-number">
                  {formatearNumero(prediccion.prediccion_visitantes)}
                </div>
                <p className="muted">visitantes no residentes estimados</p>

                <div className="detail-list">
                  <div>
                    <span>Modelo</span>
                    <strong>{prediccion.modelo}</strong>
                  </div>
                  <div>
                    <span>Horizonte</span>
                    <strong>{prediccion.horizonte_label}</strong>
                  </div>
                  <div>
                    <span>Fecha base</span>
                    <strong>{prediccion.fecha_base}</strong>
                  </div>
                  <div>
                    <span>Fecha predicha</span>
                    <strong>{prediccion.fecha_predicha}</strong>
                  </div>
                </div>
              </>
            ) : (
              <p className="muted">Todavía no hay predicción generada.</p>
            )}
          </article>
        </aside>
      </section>
      <section className="analysis-section">
  <DepartmentChart
    historico={historicoDepartamento}
    prediccion={prediccion}
    departamento={departamentoSeleccionado}
  />
</section>
      <section className="period-comparison-section">
  <PeriodComparison periodos={periodosDisponibles} />
</section>
      <section className="bottom-grid">
        <article className="card">
          <div className="section-heading">
            <div>
              <p className="section-kicker">Ranking territorial</p>
              <h2>Top 5 departamentos pronosticados</h2>
            </div>
            <span className="soft-badge">Fecha: {fechaMapa}</span>
          </div>

          <div className="ranking-list">
            {topDepartamentos.map((item, index) => (
              <button
                key={item.departamento}
                className="ranking-row"
                onClick={() => seleccionarDepartamento(item.departamento)}
              >
                <span className="ranking-index">{index + 1}</span>
                <span className="ranking-name">{item.departamento}</span>
                <strong>{formatearNumero(item.prediccion)}</strong>
              </button>
            ))}
          </div>
        </article>

        <article className="card">
          <div className="section-heading">
            <div>
              <p className="section-kicker">Desempeño técnico</p>
              <h2>Métricas del modelo seleccionado</h2>
            </div>
            <span className="soft-badge">{horizonteActivo.label}</span>
          </div>

          <div className="metrics-grid">
            <div>
              <span>MAE</span>
              <strong>{formatearNumero(mae)}</strong>
            </div>
            <div>
              <span>RMSE</span>
              <strong>{formatearNumero(rmse)}</strong>
            </div>
            <div>
              <span>MAPE</span>
              <strong>{mape ? `${formatearDecimal(mape, 2)}%` : "-"}</strong>
            </div>
            <div>
              <span>wMAPE</span>
              <strong>{wmape ? `${formatearDecimal(wmape, 2)}%` : "-"}</strong>
            </div>
          </div>

          <p className="note">
            El horizonte H6 mantiene el mejor desempeño global en wMAPE dentro
            de la comparación multihorizonte.
          </p>
        </article>
      </section>
    </main>
  );
}

export default App;