# Preparación de Datos para la Predicción de Demanda Turística en Colombia

Este repositorio contiene el proceso de **carga, limpieza, transformación e integración de datos** para construir un panel analítico a nivel **departamento-mes**, orientado a la predicción de la demanda turística de visitantes no residentes en Colombia.

Por ahora, el foco del repositorio está en la **ingeniería y preparación de datos**, no en el entrenamiento de modelos.

---

## Propósito de este repositorio

El objetivo de este repositorio es construir una base de datos limpia, consistente y reproducible a partir de fuentes oficiales, de manera que pueda ser utilizada posteriormente en experimentos de predicción de demanda turística.

El pipeline implementado permite:

- cargar archivos provenientes de diferentes fuentes oficiales,
- limpiar y estandarizar nombres de columnas y valores territoriales,
- transformar fechas a una frecuencia mensual,
- agregar información a nivel **departamento-mes**,
- integrar múltiples fuentes en un solo panel,
- crear variables temporales útiles para modelado,
- exportar un dataset final listo para análisis y entrenamiento.

---

## Unidad de análisis

La unidad de análisis del dataset final es:

- **departamento + fecha_mes**

Cada fila del panel representa un departamento en un mes específico.

---

## Variable objetivo

La variable principal construida en esta fase es:

- `visitantes_no_residentes`

Definida como el **número mensual de visitantes no residentes por departamento en Colombia**.

---

## Fuentes de datos utilizadas

### 1. Extranjeros No Residentes
Fuente principal para construir la variable objetivo.

Se utiliza para obtener el número de visitantes no residentes y agregarlo por:
- departamento
- mes

### 2. Registro Nacional de Turismo (RNT)
Se utiliza como aproximación a la oferta turística formal.

Aporta variables como:
- número de prestadores turísticos activos
- variables complementarias disponibles en el registro, si existen

### 3. Tasa Representativa del Mercado (TRM)
Se incorpora como variable macroeconómica nacional.

Dado que su frecuencia original es diaria, el pipeline la transforma a:
- promedio mensual
- valor de cierre mensual

### 4. Operaciones aéreas
Se incluye como variable de movilidad y conectividad.

Dependiendo de la estructura disponible:
- puede integrarse como variable territorial, si existe tabla aeropuerto-departamento,
- o como variable nacional mensual, si no existe dicha tabla.

### 5. ISE (opcional)
Si el archivo está disponible, se integra como variable macroeconómica mensual.

---

## Estructura esperada de archivos

El script está diseñado para trabajar con archivos ubicados dentro de una carpeta local.

Ejemplo de estructura:

```text
proyecto/
│
├── preparar_datos_turismo.py
├── README.md
│
├── data/
│   ├── raw/
│   │   ├── Extranjeros_No_Residentes_20260311.csv
│   │   ├── Registro_Nacional_de_Turismo_-_RNT_20260311.csv
│   │   ├── Operaciones_aéreas_acumuladas_en_Colombia_20260311.csv
│   │   ├── Tasa de cambio del peso colombiano.csv
│   │   └── ISE.xlsx
│   │
│   └── processed/
│       ├── target_enr_departamento_mes.csv
│       ├── trm_mensual.csv
│       ├── rnt_departamento_mes.csv
│       ├── operaciones_aereas_transformadas.csv
│       ├── panel_modelo_turismo.csv
│       └── resumen_preparacion.csv
