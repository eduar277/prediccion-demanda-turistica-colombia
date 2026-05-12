function convertirNumero(valor) {
  if (valor === null || valor === undefined) return null;

  if (typeof valor === "number") {
    return Number.isFinite(valor) ? valor : null;
  }

  const limpio = String(valor)
    .replace(/\./g, "")
    .replace(",", ".")
    .trim();

  const numero = Number(limpio);
  return Number.isFinite(numero) ? numero : null;
}

function formatearNumero(valor) {
  const numero = convertirNumero(valor);

  if (numero === null) return "-";

  return new Intl.NumberFormat("es-CO").format(Math.round(numero));
}

function formatearFecha(fecha) {
  if (!fecha) return "-";

  const date = new Date(fecha);

  if (Number.isNaN(date.getTime())) {
    return fecha;
  }

  return date.toLocaleDateString("es-CO", {
    year: "numeric",
    month: "short",
  });
}

function calcularVariacion(ultimoReal, prediccion) {
  const real = convertirNumero(ultimoReal);
  const pred = convertirNumero(prediccion);

  if (real === null || pred === null || real === 0) return null;

  return ((pred - real) / real) * 100;
}

function construirSerie(historico, prediccion) {
  const historicoOrdenado = [...historico]
    .filter((item) => convertirNumero(item.visitantes_no_residentes) !== null)
    .sort((a, b) => new Date(a.fecha) - new Date(b.fecha))
    .map((item) => ({
      fecha: item.fecha,
      fechaLabel: formatearFecha(item.fecha),
      valor: convertirNumero(item.visitantes_no_residentes),
      tipo: "historico",
    }));

  const ultimoReal = historicoOrdenado.length
    ? historicoOrdenado[historicoOrdenado.length - 1]
    : null;

  const puntoPrediccion =
    prediccion?.fecha_predicha && convertirNumero(prediccion?.prediccion_visitantes) !== null
      ? {
          fecha: prediccion.fecha_predicha,
          fechaLabel: formatearFecha(prediccion.fecha_predicha),
          valor: convertirNumero(prediccion.prediccion_visitantes),
          tipo: "prediccion",
        }
      : null;

  return {
    historicoOrdenado,
    ultimoReal,
    puntoPrediccion,
  };
}

function crearPolyline(points) {
  return points.map((p) => `${p.x},${p.y}`).join(" ");
}

export default function DepartmentChart({
  historico = [],
  prediccion = null,
  departamento = "",
}) {
  const { historicoOrdenado, ultimoReal, puntoPrediccion } = construirSerie(
    historico,
    prediccion
  );

  const valorUltimoReal = ultimoReal?.valor ?? null;
  const valorPredicho = puntoPrediccion?.valor ?? null;
  const variacion = calcularVariacion(valorUltimoReal, valorPredicho);

  const todosLosValores = [
    ...historicoOrdenado.map((item) => item.valor),
    puntoPrediccion?.valor,
  ].filter((value) => value !== null && value !== undefined);

  const hayDatos = historicoOrdenado.length > 0;

  const width = 1100;
  const height = 420;

  const padding = {
    top: 34,
    right: 38,
    bottom: 56,
    left: 78,
  };

  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const maxValue = Math.max(...todosLosValores, 1);
  const minValue = 0;
  const maxPadded = maxValue * 1.12;

  const escalaY = (valor) => {
    return (
      padding.top +
      chartHeight -
      ((valor - minValue) / (maxPadded - minValue)) * chartHeight
    );
  };

  const totalPuntos = historicoOrdenado.length + (puntoPrediccion ? 1 : 0);

  const escalaX = (index) => {
    if (totalPuntos <= 1) return padding.left;

    return padding.left + (index / (totalPuntos - 1)) * chartWidth;
  };

  const puntosHistoricos = historicoOrdenado.map((item, index) => ({
    ...item,
    x: escalaX(index),
    y: escalaY(item.valor),
  }));

  const puntoPrediccionSvg = puntoPrediccion
    ? {
        ...puntoPrediccion,
        x: escalaX(historicoOrdenado.length),
        y: escalaY(puntoPrediccion.valor),
      }
    : null;

  const ultimoRealSvg = puntosHistoricos.length
    ? puntosHistoricos[puntosHistoricos.length - 1]
    : null;

  const yTicks = Array.from({ length: 5 }, (_, index) => {
    const valor = (maxPadded / 4) * index;
    return {
      valor,
      y: escalaY(valor),
    };
  }).reverse();

  const xLabels = puntosHistoricos.filter((_, index) => {
    if (puntosHistoricos.length <= 8) return true;
    const step = Math.ceil(puntosHistoricos.length / 6);
    return index % step === 0 || index === puntosHistoricos.length - 1;
  });

  return (
    <article className="card department-analysis-card">
      <div className="section-heading">
        <div>
          <p className="section-kicker">Análisis temporal</p>
          <h2>Histórico y predicción por departamento</h2>
        </div>

        <span className="soft-badge">{departamento || "Departamento"}</span>
      </div>

      <div className="department-summary-grid">
        <div className="department-summary-item">
          <span>Último dato real</span>
          <strong>{formatearNumero(valorUltimoReal)}</strong>
          <small>{ultimoReal ? ultimoReal.fechaLabel : "-"}</small>
        </div>

        <div className="department-summary-item">
          <span>Predicción</span>
          <strong>{formatearNumero(valorPredicho)}</strong>
          <small>{puntoPrediccion ? puntoPrediccion.fechaLabel : "-"}</small>
        </div>

        <div className="department-summary-item">
          <span>Variación estimada</span>
          <strong
            className={
              variacion === null
                ? ""
                : variacion >= 0
                  ? "positive"
                  : "negative"
            }
          >
            {variacion === null ? "-" : `${variacion.toFixed(2)}%`}
          </strong>
          <small>Frente al último dato real</small>
        </div>
      </div>

      <div className="department-chart-wrapper">
        {!hayDatos ? (
          <div className="chart-empty-state">
            No hay datos históricos disponibles para este departamento.
          </div>
        ) : (
          <svg
            className="department-svg-chart"
            viewBox={`0 0 ${width} ${height}`}
            role="img"
            aria-label={`Histórico y predicción para ${departamento}`}
          >
            <rect
              x="0"
              y="0"
              width={width}
              height={height}
              rx="18"
              fill="#ffffff"
            />

            {yTicks.map((tick) => (
              <g key={tick.valor}>
                <line
                  x1={padding.left}
                  x2={width - padding.right}
                  y1={tick.y}
                  y2={tick.y}
                  stroke="#e2e8f0"
                  strokeDasharray="4 4"
                />
                <text
                  x={padding.left - 12}
                  y={tick.y + 4}
                  textAnchor="end"
                  className="chart-axis-label"
                >
                  {formatearNumero(tick.valor)}
                </text>
              </g>
            ))}

            <line
              x1={padding.left}
              x2={padding.left}
              y1={padding.top}
              y2={height - padding.bottom}
              stroke="#cbd5e1"
            />

            <line
              x1={padding.left}
              x2={width - padding.right}
              y1={height - padding.bottom}
              y2={height - padding.bottom}
              stroke="#cbd5e1"
            />

            {xLabels.map((point) => (
              <text
                key={`${point.fecha}-${point.x}`}
                x={point.x}
                y={height - padding.bottom + 28}
                textAnchor="middle"
                className="chart-axis-label"
              >
                {point.fechaLabel}
              </text>
            ))}

            {prediccion?.fecha_base && (
              <g>
                <line
                  x1={ultimoRealSvg?.x || padding.left}
                  x2={ultimoRealSvg?.x || padding.left}
                  y1={padding.top}
                  y2={height - padding.bottom}
                  stroke="#94a3b8"
                  strokeDasharray="6 6"
                />
                <text
                  x={(ultimoRealSvg?.x || padding.left) - 8}
                  y={padding.top + 14}
                  textAnchor="end"
                  className="chart-reference-label"
                >
                  Fecha base
                </text>
              </g>
            )}

            {puntosHistoricos.length > 1 && (
              <polyline
                points={crearPolyline(puntosHistoricos)}
                fill="none"
                stroke="#2563eb"
                strokeWidth="4"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            )}

            {ultimoRealSvg && puntoPrediccionSvg && (
              <line
                x1={ultimoRealSvg.x}
                y1={ultimoRealSvg.y}
                x2={puntoPrediccionSvg.x}
                y2={puntoPrediccionSvg.y}
                stroke="#f97316"
                strokeWidth="4"
                strokeDasharray="10 8"
                strokeLinecap="round"
              />
            )}

            {puntosHistoricos
              .filter((_, index) => {
                if (puntosHistoricos.length <= 16) return true;
                return index % Math.ceil(puntosHistoricos.length / 14) === 0;
              })
              .map((point) => (
                <circle
                  key={`${point.fecha}-real`}
                  cx={point.x}
                  cy={point.y}
                  r="4"
                  fill="#2563eb"
                  stroke="#ffffff"
                  strokeWidth="2"
                >
                  <title>
                    {`${point.fechaLabel}: ${formatearNumero(point.valor)} visitantes`}
                  </title>
                </circle>
              ))}

            {ultimoRealSvg && (
              <circle
                cx={ultimoRealSvg.x}
                cy={ultimoRealSvg.y}
                r="6"
                fill="#2563eb"
                stroke="#ffffff"
                strokeWidth="3"
              >
                <title>
                  {`Último real ${ultimoRealSvg.fechaLabel}: ${formatearNumero(
                    ultimoRealSvg.valor
                  )}`}
                </title>
              </circle>
            )}

            {puntoPrediccionSvg && (
              <circle
                cx={puntoPrediccionSvg.x}
                cy={puntoPrediccionSvg.y}
                r="8"
                fill="#f97316"
                stroke="#ffffff"
                strokeWidth="3"
              >
                <title>
                  {`Predicción ${puntoPrediccionSvg.fechaLabel}: ${formatearNumero(
                    puntoPrediccionSvg.valor
                  )}`}
                </title>
              </circle>
            )}

            <g transform={`translate(${padding.left}, ${height - 16})`}>
              <circle cx="0" cy="0" r="6" fill="#2563eb" />
              <text x="14" y="5" className="chart-legend-text">
                Histórico real
              </text>

              <line
                x1="150"
                y1="0"
                x2="190"
                y2="0"
                stroke="#f97316"
                strokeWidth="4"
                strokeDasharray="10 8"
              />
              <circle cx="190" cy="0" r="6" fill="#f97316" />
              <text x="204" y="5" className="chart-legend-text">
                Predicción
              </text>
            </g>
          </svg>
        )}
      </div>

      <p className="note">
        La línea azul representa la demanda histórica observada. La línea naranja
        punteada conecta el último dato real con la predicción futura generada
        por el modelo para el horizonte seleccionado.
      </p>
    </article>
  );
}