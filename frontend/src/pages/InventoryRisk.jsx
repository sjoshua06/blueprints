import { useEffect, useState, useMemo } from "react";
import {
  getInternalRiskPredictions,
  getInternalHighRisk,
  getInternalRiskSummary,
  runProphetForecast,
} from "../services/api";
import ProphetChart from "../components/ProphetChart";

/* ── Helpers ──────────────────────────────────────────────────── */

function riskColor(level) {
  switch ((level || "").toUpperCase()) {
    case "HIGH":
      return { bg: "var(--error-bg)", color: "var(--error)", border: "rgba(239,68,68,0.25)" };
    case "MEDIUM":
      return { bg: "var(--warning-bg)", color: "var(--warning)", border: "rgba(245,158,11,0.25)" };
    case "LOW":
      return { bg: "var(--success-bg)", color: "var(--success)", border: "rgba(34,197,94,0.25)" };
    default:
      return { bg: "var(--bg-card)", color: "var(--text-muted)", border: "var(--glass-border)" };
  }
}

function fmt(val, fallback = "—") {
  if (val === null || val === undefined || val === "") return fallback;
  if (typeof val === "number") return val.toLocaleString(undefined, { maximumFractionDigits: 2 });
  return String(val);
}

function formatDays(val) {
  if (val === null || val === undefined || val === "") return "—";
  const num = Number(val);
  if (num >= 999) return "> 90";
  return num.toString();
}

function fmtCurrency(val) {
  if (val === null || val === undefined) return "—";
  return "$" + Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtDate(val) {
  if (!val || val === "None" || val === "null") return "—";
  try {
    const d = new Date(val);
    if (isNaN(d.getTime())) return val;
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  } catch {
    return val;
  }
}

/* ── Risk Level Badge ─────────────────────────────────────────── */

function RiskLevelBadge({ level }) {
  const c = riskColor(level);
  return (
    <span
      className="ir-risk-badge"
      style={{
        background: c.bg,
        color: c.color,
        border: `1px solid ${c.border}`,
      }}
    >
      {(level || "UNKNOWN").toUpperCase()}
    </span>
  );
}

/* ── Confidence Bar ───────────────────────────────────────────── */

function ConfidenceBar({ value }) {
  const pct = Math.min(100, Math.max(0, Number(value || 0) * 100));
  const hue = pct > 70 ? 142 : pct > 40 ? 38 : 0;
  return (
    <div className="ir-confidence-bar">
      <div
        className="ir-confidence-bar__fill"
        style={{
          width: `${pct}%`,
          background: `linear-gradient(90deg, hsl(${hue}, 72%, 45%), hsl(${hue}, 72%, 55%))`,
        }}
      />
      <span className="ir-confidence-bar__label">{pct.toFixed(0)}%</span>
    </div>
  );
}

/* ── Main Page ────────────────────────────────────────────────── */

export default function InventoryRisk() {
  const [predictions, setPredictions] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeFilter, setActiveFilter] = useState("ALL");
  const [search, setSearch] = useState("");
  const [expandedId, setExpandedId] = useState(null);
  const [isForecasting, setIsForecasting] = useState(false);

  async function loadData() {
    try {
      setLoading(true);
      const [predRes, sumRes] = await Promise.all([
        getInternalRiskPredictions(),
        getInternalRiskSummary(),
      ]);
      setPredictions(predRes.data || []);
      setSummary(sumRes.summary || null);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleForceForecast() {
    try {
      setIsForecasting(true);
      await runProphetForecast();
      await loadData(); // reload dashboard
    } catch (err) {
      alert("Forecast error: " + err.message);
    } finally {
      setIsForecasting(false);
    }
  }

  /* ── Filtering & search ─────────────────────────────────────── */

  const filtered = useMemo(() => {
    let items = predictions;
    if (activeFilter !== "ALL") {
      items = items.filter((p) => (p.risk_level || "").toUpperCase() === activeFilter);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      items = items.filter((p) =>
        (p.component_name || "").toLowerCase().includes(q)
      );
    }
    return items;
  }, [predictions, activeFilter, search]);

  /* ── Loading / Error states ─────────────────────────────────── */

  if (loading) {
    return (
      <div className="dash-loading">
        <span className="spinner spinner--lg" />
        <p>Loading risk predictions…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dash-error">
        <h2>Something went wrong</h2>
        <p>{error}</p>
      </div>
    );
  }

  /* ── Summary stats ──────────────────────────────────────────── */

  const highCount = summary?.high_risk_count ?? 0;
  const medCount = summary?.medium_risk_count ?? 0;
  const lowCount = summary?.low_risk_count ?? 0;
  const totalComp = summary?.total_components ?? 0;
  const totalExposure = summary?.total_exposure ?? 0;

  const FILTER_TABS = [
    { key: "ALL", label: "All", count: totalComp },
    { key: "HIGH", label: "High Risk", count: highCount },
    { key: "MEDIUM", label: "Medium", count: medCount },
    { key: "LOW", label: "Low", count: lowCount },
  ];

  /* ── Distribution bar widths ────────────────────────────────── */

  const barTotal = highCount + medCount + lowCount || 1;
  const highPct = ((highCount / barTotal) * 100).toFixed(1);
  const medPct = ((medCount / barTotal) * 100).toFixed(1);
  const lowPct = ((lowCount / barTotal) * 100).toFixed(1);

  return (
    <div className="ir-page">
      {/* ── Header ────────────────────────────────────────────── */}
      <div className="ir-header">
        <div>
          <h1 className="ir-header__title">Inventory Risk & Prophet Insights</h1>
          <p className="ir-header__subtitle">
            AI-powered stockout predictions, reorder recommendations, and cost-risk analysis
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          {summary?.last_predicted_at && (
            <div className="ir-header__timestamp">
              <span className="ir-header__ts-icon">🕐</span>
              Last predicted: {fmtDate(summary.last_predicted_at)}
            </div>
          )}
          <button
            className="btn btn--primary"
            onClick={handleForceForecast}
            disabled={isForecasting}
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            {isForecasting ? (
              <>
                <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
                Forecasting...
              </>
            ) : (
              <>
                <span>🚀</span> Train Prophet
              </>
            )}
          </button>
        </div>
      </div>

      {/* ── Summary Cards ─────────────────────────────────────── */}
      <div className="ir-summary-cards">
        <div className="ir-summary-card ir-summary-card--total">
          <span className="ir-summary-card__icon">📊</span>
          <div>
            <p className="ir-summary-card__value">{totalComp}</p>
            <p className="ir-summary-card__label">Total Components</p>
          </div>
        </div>
        <div className="ir-summary-card ir-summary-card--high">
          <span className="ir-summary-card__icon">🔴</span>
          <div>
            <p className="ir-summary-card__value">{highCount}</p>
            <p className="ir-summary-card__label">High Risk</p>
          </div>
        </div>
        <div className="ir-summary-card ir-summary-card--medium">
          <span className="ir-summary-card__icon">🟡</span>
          <div>
            <p className="ir-summary-card__value">{medCount}</p>
            <p className="ir-summary-card__label">Medium Risk</p>
          </div>
        </div>
        <div className="ir-summary-card ir-summary-card--low">
          <span className="ir-summary-card__icon">🟢</span>
          <div>
            <p className="ir-summary-card__value">{lowCount}</p>
            <p className="ir-summary-card__label">Low Risk</p>
          </div>
        </div>
        <div className="ir-summary-card ir-summary-card--exposure">
          <span className="ir-summary-card__icon">💰</span>
          <div>
            <p className="ir-summary-card__value">{fmtCurrency(totalExposure)}</p>
            <p className="ir-summary-card__label">Total Risk Exposure</p>
          </div>
        </div>
      </div>

      {/* ── Risk Distribution Bar ─────────────────────────────── */}
      <div className="ir-distribution">
        <h3 className="ir-distribution__title">Risk Distribution</h3>
        <div className="ir-distribution__bar">
          {highCount > 0 && (
            <div
              className="ir-distribution__segment ir-distribution__segment--high"
              style={{ width: `${highPct}%` }}
              title={`High: ${highCount} (${highPct}%)`}
            >
              {highPct > 8 && <span>{highCount}</span>}
            </div>
          )}
          {medCount > 0 && (
            <div
              className="ir-distribution__segment ir-distribution__segment--medium"
              style={{ width: `${medPct}%` }}
              title={`Medium: ${medCount} (${medPct}%)`}
            >
              {medPct > 8 && <span>{medCount}</span>}
            </div>
          )}
          {lowCount > 0 && (
            <div
              className="ir-distribution__segment ir-distribution__segment--low"
              style={{ width: `${lowPct}%` }}
              title={`Low: ${lowCount} (${lowPct}%)`}
            >
              {lowPct > 8 && <span>{lowCount}</span>}
            </div>
          )}
        </div>
        <div className="ir-distribution__legend">
          <span className="ir-distribution__legend-item">
            <span className="ir-distribution__dot ir-distribution__dot--high" /> High
          </span>
          <span className="ir-distribution__legend-item">
            <span className="ir-distribution__dot ir-distribution__dot--medium" /> Medium
          </span>
          <span className="ir-distribution__legend-item">
            <span className="ir-distribution__dot ir-distribution__dot--low" /> Low
          </span>
        </div>
      </div>

      {/* ── Filter Tabs + Search ──────────────────────────────── */}
      <div className="ir-toolbar">
        <div className="ir-tabs">
          {FILTER_TABS.map((tab) => (
            <button
              key={tab.key}
              className={`ir-tab ${activeFilter === tab.key ? "ir-tab--active" : ""}`}
              onClick={() => setActiveFilter(tab.key)}
            >
              {tab.label}
              <span className="ir-tab__badge">{tab.count}</span>
            </button>
          ))}
        </div>
        <div className="ir-search">
          <span className="ir-search__icon">🔍</span>
          <input
            type="text"
            className="ir-search__input"
            placeholder="Search component…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* ── Predictions List ──────────────────────────────────── */}
      {filtered.length === 0 ? (
        <div className="ir-empty">
          <span className="ir-empty__icon">📭</span>
          <p>No predictions match your filters</p>
        </div>
      ) : (
        <div className="ir-predictions">
          {filtered.map((p, idx) => {
            const isExpanded = expandedId === (p.id ?? idx);
            const rc = riskColor(p.risk_level);

            return (
              <div
                key={p.id ?? idx}
                className={`ir-card ${isExpanded ? "ir-card--expanded" : ""}`}
                style={{ borderLeftColor: rc.color }}
              >
                {/* Card Header — always visible */}
                <div
                  className="ir-card__header"
                  onClick={() => setExpandedId(isExpanded ? null : (p.id ?? idx))}
                >
                  <div className="ir-card__primary">
                    <h3 className="ir-card__name">{p.component_name || "Unknown"}</h3>
                    <RiskLevelBadge level={p.risk_level} />
                  </div>

                  <div className="ir-card__metrics">
                    <div className="ir-card__metric">
                      <span className="ir-card__metric-label">Stockout In</span>
                      <span className={`ir-card__metric-value ${Number(p.days_until_stockout) <= 7 ? "ir-card__metric-value--danger" : ""}`}>
                        {formatDays(p.days_until_stockout)} days
                      </span>
                    </div>
                    <div className="ir-card__metric">
                      <span className="ir-card__metric-label">Impact</span>
                      <span className="ir-card__metric-value">{fmt(p.production_impact)}</span>
                    </div>
                    <div className="ir-card__metric">
                      <span className="ir-card__metric-label">Risk Cost</span>
                      <span className="ir-card__metric-value">{fmtCurrency(p.total_risk_cost)}</span>
                    </div>
                    <div className="ir-card__metric">
                      <span className="ir-card__metric-label">Confidence</span>
                      <ConfidenceBar value={p.confidence} />
                    </div>
                  </div>

                  <span className={`ir-card__chevron ${isExpanded ? "ir-card__chevron--open" : ""}`}>
                    ▾
                  </span>
                </div>

                {/* Card Details — collapsible */}
                {isExpanded && (
                  <div className="ir-card__details">
                    <div className="ir-card__detail-grid">
                      <div className="ir-card__detail-item">
                        <span className="ir-card__detail-icon">📅</span>
                        <div>
                          <p className="ir-card__detail-label">Prophet Stockout Date</p>
                          <p className="ir-card__detail-value">{fmtDate(p.prophet_stockout_date)}</p>
                        </div>
                      </div>
                      <div className="ir-card__detail-item">
                        <span className="ir-card__detail-icon">🔄</span>
                        <div>
                          <p className="ir-card__detail-label">Prophet Reorder Date</p>
                          <p className="ir-card__detail-value">{fmtDate(p.prophet_reorder_date)}</p>
                        </div>
                      </div>
                      <div className="ir-card__detail-item">
                        <span className="ir-card__detail-icon">⏱️</span>
                        <div>
                          <p className="ir-card__detail-label">Days Until Stockout</p>
                          <p className="ir-card__detail-value">{formatDays(p.days_until_stockout)}</p>
                        </div>
                      </div>
                      <div className="ir-card__detail-item">
                        <span className="ir-card__detail-icon">🏭</span>
                        <div>
                          <p className="ir-card__detail-label">Production Impact</p>
                          <p className="ir-card__detail-value">{fmt(p.production_impact)}</p>
                        </div>
                      </div>
                      <div className="ir-card__detail-item">
                        <span className="ir-card__detail-icon">💵</span>
                        <div>
                          <p className="ir-card__detail-label">Total Risk Cost</p>
                          <p className="ir-card__detail-value ir-card__detail-value--highlight">
                            {fmtCurrency(p.total_risk_cost)}
                          </p>
                        </div>
                      </div>
                      <div className="ir-card__detail-item">
                        <span className="ir-card__detail-icon">🎯</span>
                        <div>
                          <p className="ir-card__detail-label">Confidence Score</p>
                          <p className="ir-card__detail-value">{fmt(p.confidence)}</p>
                        </div>
                      </div>
                    </div>
                    <div className="ir-card__predicted-at">
                      Predicted at: {fmtDate(p.predicted_at)}
                    </div>
                    <div style={{ marginTop: "24px", paddingTop: "16px", borderTop: "1px dashed var(--glass-border)" }}>
                      <ProphetChart componentId={p.component_id} />
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
