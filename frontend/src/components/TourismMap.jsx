import { MapContainer, TileLayer, GeoJSON } from "react-leaflet";
import { useMemo } from "react";

function normalizarTexto(texto) {
  if (!texto) return "";

  return texto
    .toString()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replaceAll(".", "")
    .replaceAll(",", "")
    .replace(/\s+/g, " ")
    .trim()
    .toUpperCase();
}

function normalizarDepartamento(texto) {
  const nombre = normalizarTexto(texto);

  const equivalencias = {
    "SANTAFE DE BOGOTA DC": "BOGOTA DC",
    "BOGOTA DC": "BOGOTA DC",
    "BOGOTA D C": "BOGOTA DC",
    "ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA CATALINA":
      "SAN ANDRES PROVIDENCIA Y SANTA CATALINA",
    "SAN ANDRES PROVIDENCIA Y SANTA CATALINA":
      "SAN ANDRES PROVIDENCIA Y SANTA CATALINA",
    NARINO: "NARINO",
  };

  return equivalencias[nombre] || nombre;
}

function obtenerNombreDepartamento(feature) {
  const props = feature.properties || {};

  return (
    props.departamento_modelo ||
    props.departamento_join ||
    props.departamento_original ||
    props.NOMBRE_DPT ||
    props.nombre ||
    props.name ||
    ""
  );
}

function formatearNumero(valor) {
  if (valor === null || valor === undefined || Number.isNaN(Number(valor))) {
    return "Sin dato";
  }

  return new Intl.NumberFormat("es-CO").format(Math.round(Number(valor)));
}

function obtenerColor(valor, min, max) {
  if (valor === null || valor === undefined || Number.isNaN(Number(valor))) {
    return "#d1d5db";
  }

  if (max === min) {
    return "#60a5fa";
  }

  const ratio = (valor - min) / (max - min);

  if (ratio >= 0.8) return "#0f172a";
  if (ratio >= 0.6) return "#1d4ed8";
  if (ratio >= 0.4) return "#2563eb";
  if (ratio >= 0.2) return "#60a5fa";
  return "#bfdbfe";
}

export default function TourismMap({
  geojson,
  prediccionesMapa,
  onSelectDepartamento,
}) {
  const prediccionesPorDepartamento = useMemo(() => {
    const mapa = new Map();

    prediccionesMapa.forEach((item) => {
      const key = normalizarDepartamento(item.departamento);
      mapa.set(key, item);
    });

    return mapa;
  }, [prediccionesMapa]);

  const valores = useMemo(() => {
    return prediccionesMapa
      .map((item) => Number(item.prediccion))
      .filter((valor) => !Number.isNaN(valor));
  }, [prediccionesMapa]);

  const min = valores.length ? Math.min(...valores) : 0;
  const max = valores.length ? Math.max(...valores) : 0;

  if (!geojson) {
    return <div className="map-placeholder">Cargando mapa de Colombia...</div>;
  }

  function estiloDepartamento(feature) {
    const nombreGeo = obtenerNombreDepartamento(feature);
    const key = normalizarDepartamento(nombreGeo);
    const pred = prediccionesPorDepartamento.get(key);
    const valor = pred ? Number(pred.prediccion) : null;

    return {
      fillColor: obtenerColor(valor, min, max),
      weight: 1,
      opacity: 1,
      color: "#ffffff",
      fillOpacity: 0.82,
    };
  }

  function onEachFeature(feature, layer) {
    const nombreGeo = obtenerNombreDepartamento(feature);
    const key = normalizarDepartamento(nombreGeo);
    const pred = prediccionesPorDepartamento.get(key);

    const valorPredicho = pred?.prediccion;
    const fecha = pred?.fecha;

    layer.bindTooltip(
      `
      <strong>${nombreGeo}</strong><br/>
      Predicción: ${formatearNumero(valorPredicho)} visitantes<br/>
      Fecha: ${fecha || "Sin fecha"}
      `,
      {
        sticky: true,
      }
    );

    layer.on({
      mouseover: (e) => {
        e.target.setStyle({
          weight: 3,
          color: "#111827",
          fillOpacity: 0.95,
        });
      },
      mouseout: (e) => {
        e.target.setStyle(estiloDepartamento(feature));
      },
      click: () => {
        if (onSelectDepartamento) {
          const departamentoModelo =
            pred?.departamento ||
            feature.properties?.departamento_modelo ||
            nombreGeo;

          onSelectDepartamento(departamentoModelo);
        }
      },
    });
  }

  return (
    <div className="map-card">
      <div className="map-header">
        <div>
          <h2>Mapa predictivo por departamento</h2>
          <p>Color más oscuro indica mayor demanda turística pronosticada.</p>
        </div>

        <div className="legend">
          <span>Baja</span>
          <div className="legend-scale" />
          <span>Alta</span>
        </div>
      </div>

      <MapContainer
        center={[4.5709, -74.2973]}
        zoom={5}
        scrollWheelZoom={false}
        className="map-container"
      >
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <GeoJSON
          key={JSON.stringify(prediccionesMapa)}
          data={geojson}
          style={estiloDepartamento}
          onEachFeature={onEachFeature}
        />
      </MapContainer>
    </div>
  );
}