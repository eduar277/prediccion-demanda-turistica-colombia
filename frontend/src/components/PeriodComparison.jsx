import { useEffect, useMemo, useState } from "react";
import { getComparacionPeriodos } from "../services/api";
import { exportToCsv, fechaArchivo } from "../utils/exportCsv";

function convertirNumero(valor) {
  if (valor === null || valor === undefined) return null;

  const numero = Number(valor);

  return Number.isFinite(numero) ? numero : null;
}

function formatearNumero(valor) {
  const numero = convertirNumero(valor);

  if (numero === null) return "-";

  return new Intl.NumberFormat("es-CO").format(Math.round(numero));
}

function formatearPorcentaje(valor) {
  const numero = convertirNumero(valor);

  if (numero === null) return "-";

  return `${numero.toFixed(2)}%`;
}

function sumar(data, campo) {
  return data.reduce((acc, item) => {
    const valor = convertirNumero(item[campo]);
    return acc + (valor === null ? 0 : valor);
  }, 0);
}

export default function PeriodComparison({ periodos = [] }) {
  const [periodoA, setPeriodoA] = useState("");
  const [periodoB, setPeriodoB] = useState("");
  const [comparacion, setComparacion] = useState([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  const periodosOrdenados = useMemo(() => {
    return [...periodos].sort();
  }, [periodos]);

  useEffect(() => {
    if (!periodosOrdenados.length || periodoA || periodoB) return;

    const ultimo = periodosOrdenados[periodosOrdenados.length - 1];
    const indiceReferencia = Math.max(periodosOrdenados.length - 13, 0);
    const referencia = periodosOrdenados[indiceReferencia];

    setPeriodoA(referencia);
    setPeriodoB(ultimo);

    cargarComparacion(referencia, ultimo);
  }, [periodosOrdenados, periodoA, periodoB]);

  async function cargarComparacion(fechaA = periodoA, fechaB = periodoB) {
    if (!fechaA || !fechaB) return;

    try {
      setCargando(true);
      setError("");

      const data = await getComparacionPeriodos(fechaA, fechaB);
      setComparacion(data);
    } catch (err) {
      console.error(err);
      setError("No se pudo cargar la comparación de periodos.");
      setComparacion([]);
    } finally {
      setCargando(false);
    }
  }
  function exportarComparacionPeriodos() {
  exportToCsv(
    `comparacion_periodos_${periodoA}_vs_${periodoB}_${fechaArchivo()}.csv`,
    comparacion,
    [
      { key: "departamento", label: "Departamento" },
      { key: "periodo_a", label: "Periodo base" },
      { key: "periodo_b", label: "Periodo comparación" },
      { key: "fecha_a", label: "Fecha base" },
      { key: "fecha_b", label: "Fecha comparación" },
      { key: "valor_a", label: "Valor periodo base" },
      { key: "valor_b", label: "Valor periodo comparación" },
      { key: "diferencia", label: "Diferencia" },
      { key: "variacion_pct", label: "Variación porcentual" },
      { key: "estado", label: "Estado" },
    ]
  );
}
  const resumen = useMemo(() => {
    const totalA = sumar(comparacion, "valor_a");
    const totalB = sumar(comparacion, "valor_b");
    const diferencia = totalB - totalA;
    const variacion = totalA !== 0 ? (diferencia / totalA) * 100 : null;

    return {
      totalA,
      totalB,
      diferencia,
      variacion,
    };
  }, [comparacion]);

  const topCrecimiento = useMemo(() => {
    return [...comparacion]
      .filter((item) => convertirNumero(item.variacion_pct) !== null)
      .sort((a, b) => Number(b.variacion_pct) - Number(a.variacion_pct))
      .slice(0, 5);
  }, [comparacion]);

  const topDisminucion = useMemo(() => {
    return [...comparacion]
      .filter((item) => convertirNumero(item.variacion_pct) !== null)
      .sort((a, b) => Number(a.variacion_pct) - Number(b.variacion_pct))
      .slice(0, 5);
  }, [comparacion]);

  const tablaPrincipal = useMemo(() => {
    return [...comparacion]
      .filter((item) => convertirNumero(item.diferencia) !== null)
      .sort(
        (a, b) =>
          Math.abs(Number(b.diferencia)) - Math.abs(Number(a.diferencia))
      )
      .slice(0, 12);
  }, [comparacion]);

  return (
    <article className="card period-comparison-card">
      <div className="section-heading">
        <div>
          <p className="section-kicker">Comparación de periodos</p>
          <h2>Análisis de variación temporal por departamento</h2>
        </div>

        <span className="soft-badge">
          {periodoA || "-"} vs {periodoB || "-"}
        </span>
      </div>

      <p className="muted period-comparison-intro">
        Esta sección compara la demanda turística observada entre dos meses.
        Permite identificar departamentos con crecimiento, disminución o cambios
        relevantes entre periodos específicos del año.
      </p>

      <div className="period-controls">
        <div className="form-group">
          <label>Periodo base</label>
          <select
            value={periodoA}
            onChange={(e) => setPeriodoA(e.target.value)}
          >
            {periodosOrdenados.map((periodo) => (
              <option key={periodo} value={periodo}>
                {periodo}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Periodo comparación</label>
          <select
            value={periodoB}
            onChange={(e) => setPeriodoB(e.target.value)}
          >
            {periodosOrdenados.map((periodo) => (
              <option key={periodo} value={periodo}>
                {periodo}
              </option>
            ))}
          </select>
        </div>

        <div className="period-action-buttons">
  <button
    className="primary-button period-button"
    type="button"
    onClick={() => cargarComparacion()}
    disabled={cargando}
  >
    {cargando ? "Comparando..." : "Comparar periodos"}
  </button>

  <button
    className="secondary-button period-button"
    type="button"
    onClick={exportarComparacionPeriodos}
    disabled={!comparacion.length}
  >
    Exportar comparación
  </button>
</div>
      </div>

      {error && <div className="alert">{error}</div>}

      <div className="period-summary-grid">
        <div>
          <span>Total periodo base</span>
          <strong>{formatearNumero(resumen.totalA)}</strong>
          <small>{periodoA || "-"}</small>
        </div>

        <div>
          <span>Total comparación</span>
          <strong>{formatearNumero(resumen.totalB)}</strong>
          <small>{periodoB || "-"}</small>
        </div>

        <div>
          <span>Diferencia</span>
          <strong
            className={
              resumen.diferencia >= 0 ? "positive" : "negative"
            }
          >
            {formatearNumero(resumen.diferencia)}
          </strong>
          <small>Visitantes no residentes</small>
        </div>

        <div>
          <span>Variación</span>
          <strong
            className={
              resumen.variacion === null
                ? ""
                : resumen.variacion >= 0
                  ? "positive"
                  : "negative"
            }
          >
            {formatearPorcentaje(resumen.variacion)}
          </strong>
          <small>Cambio relativo total</small>
        </div>
      </div>

      <div className="period-ranking-grid">
        <div className="period-ranking-card">
          <h3>Mayores crecimientos</h3>

          <div className="period-ranking-list">
            {topCrecimiento.map((item, index) => (
              <div key={item.departamento} className="period-ranking-row">
                <span>{index + 1}</span>
                <strong>{item.departamento}</strong>
                <em className="positive">
                  {formatearPorcentaje(item.variacion_pct)}
                </em>
              </div>
            ))}
          </div>
        </div>

        <div className="period-ranking-card">
          <h3>Mayores disminuciones</h3>

          <div className="period-ranking-list">
            {topDisminucion.map((item, index) => (
              <div key={item.departamento} className="period-ranking-row">
                <span>{index + 1}</span>
                <strong>{item.departamento}</strong>
                <em className="negative">
                  {formatearPorcentaje(item.variacion_pct)}
                </em>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="period-table-wrapper">
        <table className="period-table">
          <thead>
            <tr>
              <th>Departamento</th>
              <th>{periodoA}</th>
              <th>{periodoB}</th>
              <th>Diferencia</th>
              <th>Variación</th>
              <th>Estado</th>
            </tr>
          </thead>

          <tbody>
            {tablaPrincipal.map((item) => (
              <tr key={item.departamento}>
                <td>{item.departamento}</td>
                <td>{formatearNumero(item.valor_a)}</td>
                <td>{formatearNumero(item.valor_b)}</td>
                <td>{formatearNumero(item.diferencia)}</td>
                <td>{formatearPorcentaje(item.variacion_pct)}</td>
                <td>
                  <span
                    className={
                      item.estado === "crecimiento"
                        ? "status-chip good"
                        : item.estado === "disminucion"
                          ? "status-chip danger"
                          : "status-chip neutral"
                    }
                  >
                    {item.estado === "crecimiento"
                      ? "Crecimiento"
                      : item.estado === "disminucion"
                        ? "Disminución"
                        : item.estado === "sin_cambio"
                          ? "Sin cambio"
                          : "Sin dato"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="note">
        La comparación por periodos permite analizar estacionalidad, cambios
        interanuales y comportamiento turístico entre meses específicos.
      </p>
    </article>
  );
}