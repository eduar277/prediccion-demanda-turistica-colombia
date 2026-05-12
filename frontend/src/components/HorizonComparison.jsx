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

function obtenerMetricas(horizonte) {
  return horizonte?.metricas_test || {};
}

export default function HorizonComparison({
  horizontes = [],
  horizonteSeleccionado = "h6",
  onSelectHorizonte,
}) {
  const horizontesOrdenados = [...horizontes].sort(
    (a, b) => Number(a.meses) - Number(b.meses)
  );

  const mejorWMAPE = horizontesOrdenados.reduce((mejor, actual) => {
    const actualWMAPE = convertirNumero(obtenerMetricas(actual).wMAPE);
    const mejorValor = convertirNumero(obtenerMetricas(mejor).wMAPE);

    if (actualWMAPE === null) return mejor;
    if (mejorValor === null) return actual;

    return actualWMAPE < mejorValor ? actual : mejor;
  }, horizontesOrdenados[0]);

  const maxWMAPE = Math.max(
    ...horizontesOrdenados
      .map((h) => convertirNumero(obtenerMetricas(h).wMAPE))
      .filter((v) => v !== null),
    1
  );

  return (
    <article className="card horizon-comparison-card">
      <div className="section-heading">
        <div>
          <p className="section-kicker">Comparación multihorizonte</p>
          <h2>Desempeño de modelos por plazo de predicción</h2>
        </div>

        {mejorWMAPE && (
          <span className="soft-badge">
            Mejor wMAPE: {mejorWMAPE.label}
          </span>
        )}
      </div>

      <p className="muted horizon-comparison-intro">
        Esta comparación permite evaluar el comportamiento del modelo según el
        plazo de predicción. Un menor wMAPE indica mejor desempeño global,
        especialmente cuando existe desbalance entre departamentos de alta y
        baja demanda turística.
      </p>

      <div className="horizon-cards-grid">
        {horizontesOrdenados.map((horizonte) => {
          const metricas = obtenerMetricas(horizonte);
          const wmape = convertirNumero(metricas.wMAPE);
          const esActivo = horizonte.id === horizonteSeleccionado;
          const esMejor = mejorWMAPE?.id === horizonte.id;

          const barWidth = wmape === null ? 0 : Math.max((wmape / maxWMAPE) * 100, 4);

          return (
            <button
              key={horizonte.id}
              className={
                esActivo
                  ? "horizon-model-card active"
                  : "horizon-model-card"
              }
              onClick={() => onSelectHorizonte?.(horizonte.id)}
              type="button"
            >
              <div className="horizon-model-header">
                <div>
                  <span className="horizon-code">{horizonte.id.toUpperCase()}</span>
                  <strong>{horizonte.label}</strong>
                </div>

                {esMejor && <span className="best-badge">Mejor</span>}
              </div>

              <div className="horizon-main-metric">
                <span>wMAPE</span>
                <strong>{formatearPorcentaje(metricas.wMAPE)}</strong>
              </div>

              <div className="error-bar">
                <div style={{ width: `${barWidth}%` }} />
              </div>

              <div className="horizon-mini-metrics">
                <div>
                  <span>MAE</span>
                  <strong>{formatearNumero(metricas.MAE)}</strong>
                </div>
                <div>
                  <span>RMSE</span>
                  <strong>{formatearNumero(metricas.RMSE)}</strong>
                </div>
                <div>
                  <span>MAPE</span>
                  <strong>{formatearPorcentaje(metricas.MAPE)}</strong>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      <div className="horizon-table-wrapper">
        <table className="horizon-table">
          <thead>
            <tr>
              <th>Horizonte</th>
              <th>Meses</th>
              <th>MAE</th>
              <th>RMSE</th>
              <th>MAPE</th>
              <th>wMAPE</th>
              <th>Lectura</th>
            </tr>
          </thead>

          <tbody>
            {horizontesOrdenados.map((horizonte) => {
              const metricas = obtenerMetricas(horizonte);
              const esActivo = horizonte.id === horizonteSeleccionado;
              const esMejor = mejorWMAPE?.id === horizonte.id;

              return (
                <tr key={horizonte.id} className={esActivo ? "active-row" : ""}>
                  <td>
                    <button
                      className="table-link-button"
                      type="button"
                      onClick={() => onSelectHorizonte?.(horizonte.id)}
                    >
                      {horizonte.label}
                    </button>
                  </td>
                  <td>{horizonte.meses}</td>
                  <td>{formatearNumero(metricas.MAE)}</td>
                  <td>{formatearNumero(metricas.RMSE)}</td>
                  <td>{formatearPorcentaje(metricas.MAPE)}</td>
                  <td>{formatearPorcentaje(metricas.wMAPE)}</td>
                  <td>
                    {esMejor ? (
                      <span className="status-chip good">Mejor desempeño</span>
                    ) : esActivo ? (
                      <span className="status-chip active">Seleccionado</span>
                    ) : (
                      <span className="status-chip neutral">Disponible</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="note">
        Para la toma de decisiones, H1 y H3 pueden apoyar decisiones operativas
        de corto plazo; H6 ofrece un balance sólido para planeación semestral; y
        H12 permite una mirada más estratégica anual.
      </p>
    </article>
  );
}