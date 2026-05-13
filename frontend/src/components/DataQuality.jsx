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

function formatearDecimal(valor, decimales = 2) {
  const numero = convertirNumero(valor);

  if (numero === null) return "-";

  return numero.toFixed(decimales);
}

function formatearPorcentaje(valor) {
  const numero = convertirNumero(valor);

  if (numero === null) return "-";

  return `${numero.toFixed(2)}%`;
}

function estadoDuplicados(cantidad) {
  const numero = convertirNumero(cantidad);

  if (numero === null) return "Sin información";
  if (numero === 0) return "Sin duplicados";

  return `${formatearNumero(numero)} duplicados`;
}

function DatasetRow({ item }) {
  const duplicadosClave = item.duplicados_clave_temporal?.duplicados;

  return (
    <tr>
      <td>{item.nombre}</td>
      <td>{formatearNumero(item.filas)}</td>
      <td>{formatearNumero(item.columnas)}</td>
      <td>{formatearNumero(item.departamentos)}</td>
      <td>
        {item.rango_fechas
          ? `${item.rango_fechas.min} a ${item.rango_fechas.max}`
          : "-"}
      </td>
      <td>{formatearNumero(item.nulos_totales)}</td>
      <td>{formatearPorcentaje(item.porcentaje_nulos)}</td>
      <td>{estadoDuplicados(duplicadosClave ?? item.duplicados)}</td>
    </tr>
  );
}

export default function DataQuality({ calidadDatos }) {
  if (!calidadDatos) {
    return (
      <article className="card data-quality-card">
        <div className="section-heading">
          <div>
            <p className="section-kicker">Calidad de datos</p>
            <h2>Resumen de preparación y validación</h2>
          </div>
        </div>

        <p className="muted">Cargando información de calidad de datos...</p>
      </article>
    );
  }

  const panel = calidadDatos.panel;
  const desbalance = calidadDatos.desbalance_territorial;
  const datasets = calidadDatos.datasets_modelado || [];
  const predicciones = calidadDatos.predicciones || [];
  const geojson = calidadDatos.geojson || {};
  const criterios = calidadDatos.criterios_calidad || [];

  const columnasConNulos = panel?.columnas_con_nulos || [];

  return (
    <article className="card data-quality-card">
      <div className="section-heading">
        <div>
          <p className="section-kicker">Calidad de datos</p>
          <h2>Resumen de preparación, limpieza y validación</h2>
        </div>

        <span className="soft-badge">
          Estado: {calidadDatos.estado === "ok" ? "Validado" : "Revisar"}
        </span>
      </div>

      <p className="muted data-quality-intro">
        Esta sección resume la calidad de los datos usados por el sistema:
        cobertura temporal, cobertura territorial, valores faltantes,
        duplicados, datasets por horizonte y desbalance de la demanda turística.
      </p>

      <div className="quality-kpi-grid">
        <div>
          <span>Filas panel</span>
          <strong>{formatearNumero(panel?.filas)}</strong>
          <small>Registros departamento-mes</small>
        </div>

        <div>
          <span>Columnas panel</span>
          <strong>{formatearNumero(panel?.columnas)}</strong>
          <small>Variables disponibles</small>
        </div>

        <div>
          <span>Departamentos</span>
          <strong>{formatearNumero(panel?.departamentos)}</strong>
          <small>Cobertura territorial</small>
        </div>

        <div>
          <span>GeoJSON</span>
          <strong>{formatearNumero(geojson.features)}</strong>
          <small>Geometrías disponibles</small>
        </div>
      </div>

      <div className="quality-two-columns">
        <section className="quality-panel">
          <h3>Panel histórico</h3>

          <div className="quality-detail-list">
            <div>
              <span>Rango de fechas</span>
              <strong>
                {panel?.rango_fechas
                  ? `${panel.rango_fechas.min} a ${panel.rango_fechas.max}`
                  : "-"}
              </strong>
            </div>

            <div>
              <span>Nulos totales</span>
              <strong>{formatearNumero(panel?.nulos_totales)}</strong>
            </div>

            <div>
              <span>Porcentaje de nulos</span>
              <strong>{formatearPorcentaje(panel?.porcentaje_nulos)}</strong>
            </div>

            <div>
              <span>Duplicados generales</span>
              <strong>{estadoDuplicados(panel?.duplicados)}</strong>
            </div>

            <div>
              <span>Duplicados fecha-departamento</span>
              <strong>
                {estadoDuplicados(
                  panel?.duplicados_clave_temporal?.duplicados
                )}
              </strong>
            </div>
          </div>
        </section>

        <section className="quality-panel">
          <h3>Desbalance territorial</h3>

          <div className="quality-detail-list">
            <div>
              <span>Total visitantes</span>
              <strong>{formatearNumero(desbalance?.total_visitantes)}</strong>
            </div>

            <div>
              <span>Máximo departamental</span>
              <strong>{formatearNumero(desbalance?.maximo)}</strong>
            </div>

            <div>
              <span>Mínimo departamental</span>
              <strong>{formatearNumero(desbalance?.minimo)}</strong>
            </div>

            <div>
              <span>Razón máximo / mínimo</span>
              <strong>{formatearDecimal(desbalance?.razon_max_min, 2)}</strong>
            </div>

            <div>
              <span>Mediana</span>
              <strong>{formatearNumero(desbalance?.mediana)}</strong>
            </div>
          </div>
        </section>
      </div>

      <div className="quality-table-wrapper">
        <h3>Datasets de modelado por horizonte</h3>

        <table className="quality-table">
          <thead>
            <tr>
              <th>Archivo</th>
              <th>Filas</th>
              <th>Columnas</th>
              <th>Departamentos</th>
              <th>Rango fechas</th>
              <th>Nulos</th>
              <th>% nulos</th>
              <th>Duplicados</th>
            </tr>
          </thead>

          <tbody>
            {datasets.map((item) => (
              <DatasetRow key={item.nombre} item={item} />
            ))}
          </tbody>
        </table>
      </div>

      <div className="quality-table-wrapper">
        <h3>Archivos de predicciones generadas</h3>

        <table className="quality-table">
          <thead>
            <tr>
              <th>Archivo</th>
              <th>Filas</th>
              <th>Columnas</th>
              <th>Departamentos</th>
              <th>Rango fechas</th>
              <th>Nulos</th>
              <th>% nulos</th>
              <th>Duplicados</th>
            </tr>
          </thead>

          <tbody>
            {predicciones.map((item) => (
              <DatasetRow key={item.nombre} item={item} />
            ))}
          </tbody>
        </table>
      </div>

      <div className="quality-two-columns">
        <section className="quality-panel">
          <h3>Columnas con más valores faltantes</h3>

          {columnasConNulos.length ? (
            <div className="missing-list">
              {columnasConNulos.map((item) => (
                <div key={item.columna}>
                  <span>{item.columna}</span>
                  <strong>
                    {formatearNumero(item.nulos)} ({formatearPorcentaje(item.porcentaje)})
                  </strong>
                </div>
              ))}
            </div>
          ) : (
            <p className="muted">No se detectaron valores faltantes en el panel.</p>
          )}
        </section>

        <section className="quality-panel">
          <h3>Criterios de validación aplicados</h3>

          <ul className="quality-check-list">
            {criterios.map((criterio) => (
              <li key={criterio}>{criterio}</li>
            ))}
          </ul>
        </section>
      </div>

    </article>
  );
}