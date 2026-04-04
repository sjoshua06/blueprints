import { useState, useEffect, useRef } from "react";
import {
  Ship, Clock, AlertTriangle, Upload, X, TrendingUp,
  MapPin, Package, Calendar, Activity
} from "lucide-react";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Cell
} from "recharts";
import { getAccessToken } from "../services/auth";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function apiRequest(path, options = {}) {
  const token = await getAccessToken();
  const headers = { ...(options.headers || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed (${res.status})`);
  }
  return res.json();
}

// ── Risk level → color ────────────────────────────────────────────
function riskColor(level) {
  if (!level) return "#6b7280";
  const l = level.toLowerCase();
  if (l === "high")    return "#ef4444";
  if (l === "medium")  return "#f59e0b";
  if (l === "low")     return "#10b981";
  return "#6b7280";
}

function delayBadge(days) {
  if (days === 0) return { label: "On Time", color: "#10b981", bg: "rgba(16,185,129,0.12)" };
  if (days <= 2)  return { label: `+${days}d`, color: "#f59e0b", bg: "rgba(245,158,11,0.12)" };
  return            { label: `+${days}d`, color: "#ef4444", bg: "rgba(239,68,68,0.12)" };
}

// ── Parse risk factor label from "🌧 Weather (HIGH): detail" ──────
function parseRiskFactor(factor) {
  const match = factor.match(/^(.*?)\(([^)]+)\):\s*(.*)$/);
  if (match) {
    return { label: match[1].trim(), level: match[2].trim().toLowerCase(), detail: match[3].trim() };
  }
  return { label: factor, level: "unknown", detail: "" };
}

// ─────────────────────────────────────────────────────────────────
export default function ShippingDashboard() {
  const [data, setData] = useState(() => {
    const saved = sessionStorage.getItem("shipping_data");
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(!sessionStorage.getItem("shipping_data"));
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [selected, setSelected] = useState(null);   // selected shipment for drawer
  const fileInputRef = useRef(null);

  const fetchShippingData = async () => {
    setLoading(true); setError(null);
    try {
      const response = await apiRequest("/api/shipping/dashboard");
      setData(response);
      sessionStorage.setItem("shipping_data", JSON.stringify(response));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!data) {
      fetchShippingData();
    } else {
      setLoading(false);
    }
  }, []);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    try {
      await apiRequest("/api/shipping/upload", { method: "POST", body: formData });
      await fetchShippingData();
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (err) {
      alert("Upload failed: " + err.message);
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "70vh", flexDirection: "column", gap: "1rem" }}>
        <span className="spinner spinner--lg" />
        <p style={{ opacity: 0.5, fontSize: "0.9rem" }}>Fetching live risk intelligence…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard">
        <header className="dashboard__header">
          <h1 className="dashboard__title">Shipping & Transportation</h1>
        </header>
        <div className="card" style={{ padding: "2rem", color: "#ef4444" }}>
          <strong>Error:</strong> {error}
        </div>
      </div>
    );
  }

  const shipments = data?.shipments || [];
  const avgDelay  = shipments.length > 0
    ? (shipments.reduce((a, s) => a + (s.predicted_delay_days || 0), 0) / shipments.length).toFixed(1)
    : 0;
  const highRiskCount = shipments.filter(s => (s.predicted_delay_days || 0) >= 3).length;

  return (
    <div className="dashboard" style={{ position: "relative" }}>

      {/* ── Header ─────────────────────────────────────────────────── */}
      <header className="dashboard__header">
        <div>
          <h1 className="dashboard__title">Shipping & Transportation Intelligence</h1>
          <p className="dashboard__subtitle">
            Live risk predictions for <strong>{data?.destination_port || "your port"}</strong> using real-world APIs
          </p>
        </div>
      </header>

      {/* ── Upload Bar ──────────────────────────────────────────────── */}
      <div style={{
        background: "linear-gradient(135deg, rgba(99,102,241,0.1), rgba(139,92,246,0.08))",
        border: "1px dashed rgba(139,92,246,0.4)",
        borderRadius: "14px", padding: "1rem 1.5rem", marginBottom: "1.5rem",
        display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem"
      }}>
        <div>
          <p style={{ margin: 0, fontWeight: 600 }}>📦 Upload Shipments File</p>
          <p style={{ margin: 0, fontSize: "0.78rem", opacity: 0.55 }}>
            .xlsx / .xls / .csv — columns: component_name, estimated_date, mode, mode_details, quantity_received, project_id
          </p>
        </div>
        <div>
          <input type="file" accept=".xlsx,.xls,.csv" style={{ display: "none" }} ref={fileInputRef} onChange={handleFileUpload} />
          <button
            className="btn btn--primary"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            style={{ display: "inline-flex", gap: "8px", alignItems: "center" }}
          >
            {uploading ? <span className="spinner spinner--sm" /> : <Upload size={16} />}
            {uploading ? "Uploading…" : "Upload Shipments"}
          </button>
        </div>
      </div>

      {/* ── Summary Cards ───────────────────────────────────────────── */}
      <div className="dashboard__stats-grid" style={{ marginBottom: "1.5rem" }}>
        {[
          { icon: <Ship size={22} />, label: "Total Shipments",    value: shipments.length, color: "#6366f1" },
          { icon: <Clock size={22} />, label: "Avg Predicted Delay", value: `${avgDelay} days`, color: "#f59e0b" },
          { icon: <AlertTriangle size={22} />, label: "High Risk Shipments", value: highRiskCount, color: "#ef4444" },
          { icon: <MapPin size={22} />, label: "Destination Port", value: data?.destination_port || "—", color: "#10b981" },
        ].map((card, i) => (
          <div key={i} className="stat-card" style={{ borderTop: `3px solid ${card.color}` }}>
            <div style={{ width: 42, height: 42, borderRadius: "10px", background: card.color + "22", display: "flex", alignItems: "center", justifyContent: "center", color: card.color }}>
              {card.icon}
            </div>
            <div className="stat-card__content">
              <h3 style={{ fontSize: "0.78rem", opacity: 0.6, margin: 0 }}>{card.label}</h3>
              <p style={{ fontSize: "1.6rem", fontWeight: 700, margin: 0, color: card.color }}>{card.value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* ── Shipments Table ─────────────────────────────────────────── */}
      <div className="card">
        <div className="card__header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2 style={{ margin: 0 }}>Active Shipments</h2>
          <span style={{ fontSize: "0.78rem", opacity: 0.5 }}>Click a row to see risk breakdown</span>
        </div>
        <div className="card__body" style={{ padding: 0 }}>
          {shipments.length === 0 ? (
            <div style={{ padding: "3rem", textAlign: "center", opacity: 0.5 }}>
              <Ship size={40} style={{ marginBottom: "1rem" }} />
              <p>No shipments yet. Upload your file to get started!</p>
            </div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>Component</th>
                    <th>Qty</th>
                    <th>Mode</th>
                    <th>Est. Arrival</th>
                    <th>Predicted Arrival</th>
                    <th>Delay</th>
                    <th>Risk Score</th>
                  </tr>
                </thead>
                <tbody>
                  {shipments.map((s, i) => {
                    const badge = delayBadge(s.predicted_delay_days || 0);
                    const highFactors = (s.risk_factors || []).filter(f => f.toLowerCase().includes("high")).length;
                    const riskScore = Math.min(10, (s.predicted_delay_days || 0) * 1.5 + highFactors);
                    return (
                      <tr
                        key={i}
                        onClick={() => setSelected(s)}
                        style={{ cursor: "pointer", transition: "background 0.15s" }}
                        onMouseEnter={e => e.currentTarget.style.background = "rgba(99,102,241,0.08)"}
                        onMouseLeave={e => e.currentTarget.style.background = ""}
                      >
                        <td style={{ fontWeight: 600 }}>{s.component_name || `Component #${s.component_id}`}</td>
                        <td>{s.quantity_received ?? "—"}</td>
                        <td>
                          <span className="badge badge--neutral">{s.mode ? s.mode.toUpperCase() : "UNKNOWN"}</span>
                          {s.mode_details && <div style={{ fontSize: "0.72rem", opacity: 0.5, marginTop: 2 }}>{s.mode_details}</div>}
                        </td>
                        <td style={{ opacity: 0.7 }}>{s.estimated_date ? new Date(s.estimated_date).toLocaleDateString() : "TBD"}</td>
                        <td style={{ fontWeight: 500 }}>{s.predicted_arrival_date ? new Date(s.predicted_arrival_date).toLocaleDateString() : "TBD"}</td>
                        <td>
                          <span style={{
                            display: "inline-flex", alignItems: "center", gap: 4, fontWeight: 700,
                            fontSize: "0.85rem", padding: "3px 10px", borderRadius: 20,
                            color: badge.color, background: badge.bg
                          }}>
                            {(s.predicted_delay_days || 0) > 0 && <AlertTriangle size={13} />}
                            {badge.label}
                          </span>
                        </td>
                        <td>
                          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                            <div style={{ flex: 1, height: 6, background: "rgba(255,255,255,0.1)", borderRadius: 3, overflow: "hidden", minWidth: 60 }}>
                              <div style={{ width: `${riskScore * 10}%`, height: "100%", background: riskColor(riskScore > 6 ? "high" : riskScore > 3 ? "medium" : "low"), borderRadius: 3 }} />
                            </div>
                            <span style={{ fontSize: "0.78rem", opacity: 0.6 }}>{riskScore.toFixed(1)}/10</span>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* ── Detail Drawer ────────────────────────────────────────────── */}
      {selected && (
        <ShipmentDrawer shipment={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  );
}

// ─── Shipment Detail Drawer ───────────────────────────────────────────────────
function ShipmentDrawer({ shipment: s, onClose }) {
  const factors = (s.risk_factors || []).map(parseRiskFactor);

  // Radar data
  const radarData = factors.map(f => ({
    subject: f.label.replace(/[^\w\s]/g, "").trim(),
    value: f.level === "high" ? 90 : f.level === "medium" ? 50 : f.level === "unknown" ? 30 : 10,
  }));

  // Bar chart: delay contribution per factor
  const barData = factors.map(f => {
    const delayMap = { high: 3, medium: 1, low: 0, unknown: 0 };
    return { name: f.label.replace(/[^\w\s]/g, "").trim(), delay: delayMap[f.level] || 0, fill: riskColor(f.level) };
  }).filter(d => d.delay > 0);

  const badge = delayBadge(s.predicted_delay_days || 0);

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", backdropFilter: "blur(4px)", zIndex: 100 }}
      />

      {/* Drawer */}
      <div style={{
        position: "fixed", top: 0, right: 0, bottom: 0, width: "min(600px, 95vw)",
        background: "var(--surface, #1a1a2e)", borderLeft: "1px solid rgba(255,255,255,0.1)",
        overflowY: "auto", zIndex: 101, padding: "2rem",
        boxShadow: "-20px 0 60px rgba(0,0,0,0.4)"
      }}>

        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1.5rem" }}>
          <div>
            <h2 style={{ margin: 0, fontSize: "1.3rem" }}>{s.component_name || `Component #${s.component_id}`}</h2>
            <p style={{ margin: "4px 0 0", opacity: 0.5, fontSize: "0.85rem" }}>
              <span className="badge badge--neutral" style={{ marginRight: 6 }}>{s.mode?.toUpperCase() || "UNKNOWN"}</span>
              {s.mode_details}
            </p>
          </div>
          <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", color: "inherit", opacity: 0.6, padding: 4 }}>
            <X size={22} />
          </button>
        </div>

        {/* Key stats */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "2rem" }}>
          {[
            { icon: <Calendar size={16} />, label: "Estimated Arrival",  value: s.estimated_date        ? new Date(s.estimated_date).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "TBD" },
            { icon: <TrendingUp size={16} />, label: "Predicted Arrival", value: s.predicted_arrival_date ? new Date(s.predicted_arrival_date).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "TBD" },
            { icon: <Package size={16} />, label: "Quantity",            value: s.quantity_received ?? "—" },
            { icon: <Activity size={16} />, label: "Predicted Delay",    value: (
              <span style={{ color: badge.color, fontWeight: 700 }}>{badge.label}</span>
            )},
          ].map((item, i) => (
            <div key={i} style={{ background: "rgba(255,255,255,0.04)", borderRadius: 10, padding: "0.8rem 1rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, opacity: 0.5, fontSize: "0.75rem", marginBottom: 4 }}>
                {item.icon} {item.label}
              </div>
              <div style={{ fontWeight: 600, fontSize: "0.95rem" }}>{item.value}</div>
            </div>
          ))}
        </div>

        {/* Radar Chart */}
        <div className="card" style={{ marginBottom: "1.5rem", padding: "1rem" }}>
          <h3 style={{ margin: "0 0 1rem", fontSize: "0.95rem", opacity: 0.8 }}>🎯 Risk Factor Radar</h3>
          <ResponsiveContainer width="100%" height={260}>
            <RadarChart data={radarData} cx="50%" cy="50%" outerRadius={90}>
              <PolarGrid stroke="rgba(255,255,255,0.1)" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: "rgba(255,255,255,0.6)", fontSize: 11 }} />
              <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
              <Radar name="Risk" dataKey="value" stroke="#6366f1" fill="#6366f1" fillOpacity={0.3} strokeWidth={2} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Bar Chart: Delay contribution */}
        {barData.length > 0 && (
          <div className="card" style={{ marginBottom: "1.5rem", padding: "1rem" }}>
            <h3 style={{ margin: "0 0 1rem", fontSize: "0.95rem", opacity: 0.8 }}>📊 Delay Contribution by Factor</h3>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={barData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="name" tick={{ fill: "rgba(255,255,255,0.55)", fontSize: 11 }} />
                <YAxis tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 10 }} unit="d" />
                <Tooltip
                  contentStyle={{ background: "#1e1e3a", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 12 }}
                  formatter={(v) => [`${v} day(s)`, "Delay"]}
                />
                <Bar dataKey="delay" radius={[6, 6, 0, 0]}>
                  {barData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Risk Factor Details */}
        <div className="card" style={{ padding: "1rem" }}>
          <h3 style={{ margin: "0 0 1rem", fontSize: "0.95rem", opacity: 0.8 }}>📋 Risk Intelligence Breakdown</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
            {factors.map((f, i) => (
              <div key={i} style={{
                display: "flex", gap: "0.75rem", alignItems: "flex-start",
                padding: "0.65rem 0.8rem", borderRadius: 10,
                background: "rgba(255,255,255,0.03)",
                borderLeft: `3px solid ${riskColor(f.level)}`
              }}>
                <div style={{ minWidth: 55 }}>
                  <span style={{
                    fontSize: "0.68rem", fontWeight: 700, padding: "2px 7px", borderRadius: 10,
                    background: riskColor(f.level) + "33", color: riskColor(f.level)
                  }}>
                    {f.level.toUpperCase()}
                  </span>
                </div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: "0.85rem" }}>{f.label}</div>
                  <div style={{ fontSize: "0.78rem", opacity: 0.55, marginTop: 2 }}>{f.detail}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
