function limpiarValor(valor) {
  if (valor === null || valor === undefined) return "";

  const texto = String(valor);

  if (
    texto.includes(",") ||
    texto.includes(";") ||
    texto.includes('"') ||
    texto.includes("\n")
  ) {
    return `"${texto.replaceAll('"', '""')}"`;
  }

  return texto;
}

export function exportToCsv(nombreArchivo, filas = [], columnas = null) {
  if (!filas || filas.length === 0) {
    alert("No hay datos disponibles para exportar.");
    return;
  }

  const columnasFinales =
    columnas ||
    Object.keys(filas[0]).map((key) => ({
      key,
      label: key,
    }));

  const encabezado = columnasFinales.map((col) => limpiarValor(col.label)).join(";");

  const cuerpo = filas
    .map((fila) =>
      columnasFinales
        .map((col) => limpiarValor(fila[col.key]))
        .join(";")
    )
    .join("\n");

  const contenido = `\uFEFF${encabezado}\n${cuerpo}`;

  const blob = new Blob([contenido], {
    type: "text/csv;charset=utf-8;",
  });

  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", nombreArchivo);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  URL.revokeObjectURL(url);
}

export function fechaArchivo() {
  const ahora = new Date();

  const yyyy = ahora.getFullYear();
  const mm = String(ahora.getMonth() + 1).padStart(2, "0");
  const dd = String(ahora.getDate()).padStart(2, "0");
  const hh = String(ahora.getHours()).padStart(2, "0");
  const min = String(ahora.getMinutes()).padStart(2, "0");

  return `${yyyy}${mm}${dd}_${hh}${min}`;
}