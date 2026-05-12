import { exportToCsv, fechaArchivo } from "../utils/exportCsv";

function formatearHorizonte(id, horizontes) {
  const h = horizontes.find((item) => item.id === id);
  return h?.label || id;
}

export default function ExportTools({
  prediccionesMapa = [],
  horizontes = [],
  horizonteSeleccionado = "h6",
  prediccion = null,
}) {
  function exportarPrediccionesMapa() {
    exportToCsv(
      `predicciones_mapa_${horizonteSeleccionado}_${fechaArchivo()}.csv`,
      prediccionesMapa,
      [
        { key: "departamento", label: "Departamento" },
        { key: "horizonte", label: "Horizonte" },
        { key: "meses_horizonte", label: "Meses horizonte" },
        { key: "fecha", label: "Fecha base" },
        { key: "fecha_predicha", label: "Fecha predicha" },
        { key: "target", label: "Valor real" },
        { key: "prediccion", label: "Predicción" },
        { key: "error_abs", label: "Error absoluto" },
      ]
    );
  }

  function exportarMetricasHorizontes() {
    const filas = horizontes.map((h) => ({
      horizonte: h.id,
      horizonte_label: h.label,
      meses: h.meses,
      modelo_cargado: h.modelo_cargado,
      dataset_cargado: h.dataset_cargado,
      predicciones_cargadas: h.predicciones_cargadas,
      MAE: h.metricas_test?.MAE,
      RMSE: h.metricas_test?.RMSE,
      MAPE: h.metricas_test?.MAPE,
      wMAPE: h.metricas_test?.wMAPE,
    }));

    exportToCsv(
      `metricas_multihorizonte_${fechaArchivo()}.csv`,
      filas,
      [
        { key: "horizonte", label: "Horizonte" },
        { key: "horizonte_label", label: "Etiqueta" },
        { key: "meses", label: "Meses" },
        { key: "modelo_cargado", label: "Modelo cargado" },
        { key: "dataset_cargado", label: "Dataset cargado" },
        { key: "predicciones_cargadas", label: "Predicciones cargadas" },
        { key: "MAE", label: "MAE" },
        { key: "RMSE", label: "RMSE" },
        { key: "MAPE", label: "MAPE" },
        { key: "wMAPE", label: "wMAPE" },
      ]
    );
  }

  function exportarPrediccionActual() {
    if (!prediccion) {
      alert("No hay predicción individual disponible para exportar.");
      return;
    }

    exportToCsv(
      `prediccion_${prediccion.departamento}_${prediccion.horizonte}_${fechaArchivo()}.csv`,
      [
        {
          departamento: prediccion.departamento,
          modelo: prediccion.modelo,
          horizonte: prediccion.horizonte,
          horizonte_label:
            prediccion.horizonte_label ||
            formatearHorizonte(horizonteSeleccionado, horizontes),
          meses_horizonte: prediccion.meses_horizonte,
          fecha_base: prediccion.fecha_base,
          fecha_predicha: prediccion.fecha_predicha,
          prediccion_visitantes: prediccion.prediccion_visitantes,
          descripcion: prediccion.descripcion,
        },
      ],
      [
        { key: "departamento", label: "Departamento" },
        { key: "modelo", label: "Modelo" },
        { key: "horizonte", label: "Horizonte" },
        { key: "horizonte_label", label: "Horizonte etiqueta" },
        { key: "meses_horizonte", label: "Meses horizonte" },
        { key: "fecha_base", label: "Fecha base" },
        { key: "fecha_predicha", label: "Fecha predicha" },
        { key: "prediccion_visitantes", label: "Predicción visitantes" },
        { key: "descripcion", label: "Descripción" },
      ]
    );
  }

  return (
    <article className="card export-card">
      <div className="section-heading">
        <div>
          <p className="section-kicker">Exportación de resultados</p>
          <h2>Descargar información analítica</h2>
        </div>

        <span className="soft-badge">
          Horizonte activo: {formatearHorizonte(horizonteSeleccionado, horizontes)}
        </span>
      </div>

      <p className="muted export-intro">
        Exporta los resultados principales del dashboard para usarlos en Excel,
        informes técnicos o sustentaciones del proyecto.
      </p>

      <div className="export-actions">
        <button type="button" className="secondary-button" onClick={exportarPrediccionesMapa}>
          Exportar predicciones del mapa
        </button>

        <button type="button" className="secondary-button" onClick={exportarMetricasHorizontes}>
          Exportar métricas multihorizonte
        </button>

        <button type="button" className="secondary-button" onClick={exportarPrediccionActual}>
          Exportar predicción actual
        </button>
      </div>
    </article>
  );
}