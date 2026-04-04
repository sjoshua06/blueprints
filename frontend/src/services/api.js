import { getAccessToken } from "./auth";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

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
  return request("/api/users/profile", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function getProfile() {
  return request("/api/users/profile");
}

/* ── Setup uploads ────────────────────────────────────────────── */

export function uploadSetupFile(endpoint, file) {
  const form = new FormData();
  form.append("file", file);
  return request(`/api/setup/${endpoint}`, { method: "POST", body: form });
}

export function buildIndexes() {
  return request("/api/setup/build-indexes", { method: "POST" });
}

export function getSetupStatus() {
  return request("/api/setup/status");
}

/* ── Project ──────────────────────────────────────────────────── */

export function createProject(data) {
  return request("/api/setup/project", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

/* ── Dashboard ────────────────────────────────────────────────── */

export function getDashboardSummary() {
  return request("/api/dashboard/summary");
}

export function getDashboardComponents() {
  return request("/api/dashboard/components");
}

export function getDashboardSuppliers() {
  return request("/api/dashboard/suppliers");
}

export function getDashboardInventory() {
  return request("/api/dashboard/inventory");
}

/* ── BOM Analysis ─────────────────────────────────────────────── */

export function analyzeBom(bomFile, receiptFile) {
  const form = new FormData();
  form.append("bom_file", bomFile);
  form.append("receipt_file", receiptFile);
  return request("/api/analysis/bom", { method: "POST", body: form });
}

/* ── Risk ──────────────────────────────────────────────────────── */

export function predictRisk(data) {
  return request("/api/supplier-risk/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function predictAllSuppliersRisk() {
  return request("/api/supplier-risk/predict-all", { method: "POST" });
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

/* ── Supplier Mailing Agent ───────────────────────────────────── */

export function sendSupplierMailRequest(data) {
  return request("/api/suppliers/mail-request", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function processSupplierReply(data) {
  return request("/api/suppliers/process-reply", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function getSupplierInsights(componentId, componentName) {
  return request(`/api/suppliers/insights/${componentId}?component_name=${encodeURIComponent(componentName)}`);
}

/* ── Final Risk (Agentic BOM Shock Predictor) ─────────────────── */

export function getFinalRiskById(supplierId, userId) {
  const params = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
  return request(`/api/final-risk/${supplierId}${params}`);
}

export function predictFinalRisk(data) {
  return request("/api/final-risk/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function predictAllFinalRisk(userId) {
  return request(`/api/final-risk/predict-all?user_id=${encodeURIComponent(userId)}`, {
    method: "POST",
  });
}