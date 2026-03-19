import { getAccessToken } from "./auth";

const BASE_URL = import.meta.env.VITE_API_URL

/* ── Internal helper ──────────────────────────────────────────── */

async function authHeaders() {
  const token = await getAccessToken();
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

async function request(path, options = {}) {
  const headers = await authHeaders();
  Object.assign(headers, options.headers ?? {});

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed (${res.status})`);
  }

  return res.json();
}

/* ── Profile ──────────────────────────────────────────────────── */

export function createProfile(data) {
  return request("/users/profile", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function getProfile() {
  return request("/users/profile");
}

/* ── Setup uploads ────────────────────────────────────────────── */

export function uploadSetupFile(endpoint, file) {
  const form = new FormData();
  form.append("file", file);
  return request(`/setup/${endpoint}`, { method: "POST", body: form });
}

export function buildIndexes() {
  return request("/setup/build-indexes", { method: "POST" });
}

export function getSetupStatus() {
  return request("/setup/status");
}

/* ── Project ──────────────────────────────────────────────────── */

export function createProject(data) {
  return request("/setup/project", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

/* ── Dashboard ────────────────────────────────────────────────── */

export function getDashboardSummary() {
  return request("/dashboard/summary");
}

export function getDashboardComponents() {
  return request("/dashboard/components");
}

export function getDashboardSuppliers() {
  return request("/dashboard/suppliers");
}

export function getDashboardInventory() {
  return request("/dashboard/inventory");
}

/* ── BOM Analysis ─────────────────────────────────────────────── */

export function analyzeBom(bomFile, receiptFile) {
  const form = new FormData();
  form.append("bom_file", bomFile);
  form.append("receipt_file", receiptFile);
  return request("/analysis/bom", { method: "POST", body: form });
}

/* ── Risk ──────────────────────────────────────────────────────── */

export function predictRisk(data) {
  return request("/risk/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function predictAllSuppliersRisk() {
  return request("/risk/predict-all", { method: "POST" });
}

/* ── Internal Risk (Inventory Risk) ───────────────────────────── */

export function getInternalRiskPredictions() {
  return request("/api/risk/predictions");
}

export function getInternalRiskByComponent(componentId) {
  return request(`/api/risk/predictions/${componentId}`);
}

export function getInternalHighRisk() {
  return request("/api/risk/high-risk");
}

export function getInternalRiskSummary() {
  return request("/api/risk/summary");
}

export function runProphetForecast() {
  return request("/api/risk/run-prophet", { method: "POST" });
}

export function getProphetForecastData(componentId) {
  return request(`/api/risk/forecast/${componentId}`);
}