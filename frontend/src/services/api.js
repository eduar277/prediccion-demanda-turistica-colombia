import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export const api = axios.create({
  baseURL: API_URL,
  timeout: 15000,
});

export async function getHealth() {
  const response = await api.get("/health");
  return response.data;
}

export async function getMetadataModelo() {
  const response = await api.get("/modelo/metadata");
  return response.data;
}

export async function getDepartamentos() {
  const response = await api.get("/departamentos");
  return response.data;
}

export async function predictDepartamento(departamento) {
  const response = await api.post(`/predict/${encodeURIComponent(departamento)}`);
  return response.data;
}

export async function getHistoricoDepartamento(departamento) {
  const response = await api.get(`/historico/${encodeURIComponent(departamento)}`);
  return response.data;
}

export async function getPrediccionesMapa() {
  const response = await api.get("/predicciones/mapa");
  return response.data;
}

export async function getGeojson() {
  const response = await api.get("/geojson");
  return response.data;
}