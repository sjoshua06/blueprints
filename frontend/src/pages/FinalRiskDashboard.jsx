import { useState, useMemo, useContext, useCallback } from "react";
import { predictAllFinalRisk, getFinalRiskById } from "../services/api";
import { AuthContext } from "../App";
import {
  Brain, ShieldAlert, ShieldCheck, Activity, Zap, Globe,
  Newspaper, TrendingUp, RefreshCw, X, ChevronDown, ChevronUp,
  AlertTriangle, Anchor, Wind, Cpu, Package, Clock, BarChart3,
  Radar, Sparkles, ArrowUpRight
} from "lucide-react";

/* ─── Helpers ────────────────────────────────────────────────── */

const RISK_CONFIG = {
  CRITICAL: { color: "#ef4444", bg: "rgba(239,68,68,0.12)", border: "rgba(239,68,68,0.35)", glow: "0 0 20px rgba(239,68,68,0.3)" },
  HIGH:     { color: "#f97316", bg: "rgba(249,115,22,0.12)", border: "rgba(249,115,22,0.35)", glow: "0 0 20px rgba(249,115,22,0.25)" },
  MEDIUM:   { color: "#eab308", bg: "rgba(234,179,8,0.12)",  border: "rgba(234,179,8,0.35)",  glow: "0 0 16px rgba(234,179,8,0.2)"  },
  LOW:      { color: "#22c55e", bg: "rgba(34,197,94,0.12)",  border: "rgba(34,197,94,0.35)",  glow: "0 0 16px rgba(34,197,94,0.2)"  },
};

const SIGNAL_META = {
  reliability_risk:  { label: "Reliability",    icon: <ShieldCheck size={14} />, desc: "Based on historical reliability score" },
  defect_risk:       { label: "Defect Rate",     icon: <AlertTriangle size={14} />, desc: "Defective units per batch" },
  otd_risk:          { label: "On-Time Delivery",icon: <Clock size={14} />, desc: "Orders delivered on schedule" },
  lead_time_risk:    { label: "Lead Time",       icon: <TrendingUp size={14} />, desc: "Average procurement lead time" },
  availability_risk: { label: "Availability",   icon: <Package size={14} />, desc: "Component availability at supplier" },
  news_risk:         { label: "News Sentiment",  icon: <Newspaper size={14} />, desc: "Real-time global news VADER sentiment" },
  shipping_risk:     { label: "Shipping Risk",   icon: <Anchor size={14} />, desc: "Weather · Earthquake · Political · Conflict" },
};

function getRiskConfig(level) {
  return RISK_CONFIG[level] || RISK_CONFIG.LOW;
}

/* ─── Sub-components ─────────────────────────────────────────── */

function RiskPill({ level }) {
  const cfg = getRiskConfig(level);
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: "5px",
      padding: "3px 10px", borderRadius: "99px", fontSize: "0.72rem",
      fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase",
      background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.border}`,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: "50%", background: cfg.color, boxShadow: `0 0 6px ${cfg.color}` }} />
      {level}
    </span>
  );
}

function RadarChart({ weights, scores }) {
  const keys = Object.keys(weights);
  const cx = 90, cy = 90, r = 70;
  const n = keys.length;

  const points = (arr, scale) => keys.map((k, i) => {
    const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
    const val = (arr[k] ?? 0) * scale;
    return [cx + r * val * Math.cos(angle), cy + r * val * Math.sin(angle)];
  });

  const scorePoints  = points(scores, 1);
  const weightPoints = points(weights, 1);

  const toPath = (pts) => pts.map((p, i) => `${i === 0 ? "M" : "L"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ") + "Z";

  const gridLevels = [0.25, 0.5, 0.75, 1.0];
  const axisEnds = keys.map((_, i) => {
    const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
    return [cx + r * Math.cos(angle), cy + r * Math.sin(angle)];
  });
  const labelPos = keys.map((_, i) => {
    const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
    return [cx + (r + 16) * Math.cos(angle), cy + (r + 16) * Math.sin(angle)];
  });

  return (
    <svg viewBox="0 0 180 180" style={{ width: "100%", maxWidth: 220 }}>
      {gridLevels.map(level =>
        <polygon key={level}
          points={keys.map((_, i) => {
            const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
            return `${(cx + r * level * Math.cos(angle)).toFixed(1)},${(cy + r * level * Math.sin(angle)).toFixed(1)}`;
          }).join(" ")}
          fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="1"
        />
      )}
      {axisEnds.map(([x, y], i) => <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="rgba(255,255,255,0.08)" strokeWidth="1" />)}
      <path d={toPath(weightPoints)} fill="rgba(99,102,241,0.15)" stroke="#6366f1" strokeWidth="1.5" />
      <path d={toPath(scorePoints)}  fill="rgba(239,68,68,0.15)"  stroke="#ef4444" strokeWidth="1.5" strokeDasharray="4 2" />
      {labelPos.map(([x, y], i) => (
        <text key={i} x={x} y={y} textAnchor="middle" dominantBaseline="middle"
          fontSize="7" fill="rgba(255,255,255,0.55)">{keys[i].replace("_risk","")}</text>
      ))}
    </svg>
  );
}

function GaugeArc({ score }) {
  const pct = Math.min(100, Math.max(0, score));
  const startAngle = -225;
  const sweep = 270;
  const angle = startAngle + (sweep * pct) / 100;
  const r = 52, cx = 64, cy = 64;
  const toXY = (a) => {
    const rad = (a * Math.PI) / 180;
    return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)];
  };
  const [sx, sy] = toXY(startAngle);
  const [ex, ey] = toXY(angle);
  const largeArc = pct > 50 ? 1 : 0;

  const color = pct >= 75 ? "#ef4444" : pct >= 50 ? "#f97316" : pct >= 25 ? "#eab308" : "#22c55e";

  return (
    <svg viewBox="0 0 128 90" style={{ width: 120 }}>
      <path d={`M ${toXY(-225)[0]} ${toXY(-225)[1]} A ${r} ${r} 0 1 1 ${toXY(45)[0]} ${toXY(45)[1]}`}
        fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="8" strokeLinecap="round" />
      {pct > 0 && (
        <path d={`M ${sx} ${sy} A ${r} ${r} 0 ${largeArc} 1 ${ex} ${ey}`}
          fill="none" stroke={color} strokeWidth="8" strokeLinecap="round"
          style={{ filter: `drop-shadow(0 0 6px ${color})` }} />
      )}
      <text x={cx} y={cy + 4} textAnchor="middle" dominantBaseline="middle"
        fontSize="18" fontWeight="800" fill="white">{pct.toFixed(0)}</text>
      <text x={cx} y={cy + 20} textAnchor="middle" fontSize="8" fill="rgba(255,255,255,0.4)">/ 100</text>
    </svg>
  );
}

function SignalBar({ label, icon, value, weight, isWinner }) {
  const pct = Math.min(100, value * 100);
  const wPct = Math.min(100, weight * 100);
  const color = pct >= 75 ? "#ef4444" : pct >= 50 ? "#f97316" : pct >= 25 ? "#eab308" : "#22c55e";

  return (
    <div style={{
      padding: "10px 14px", borderRadius: 10,
      background: isWinner ? "rgba(99,102,241,0.1)" : "rgba(255,255,255,0.03)",
      border: `1px solid ${isWinner ? "rgba(99,102,241,0.4)" : "rgba(255,255,255,0.06)"}`,
      transition: "all 0.2s",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
        <span style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.8rem", color: isWinner ? "#818cf8" : "#9ca3af", fontWeight: isWinner ? 700 : 500 }}>
          {icon} {label}
          {isWinner && <Sparkles size={11} color="#818cf8" />}
        </span>
        <span style={{ fontSize: "0.78rem", color, fontWeight: 700 }}>{pct.toFixed(1)}%</span>
      </div>
      <div style={{ position: "relative", height: 5, borderRadius: 99, background: "rgba(255,255,255,0.07)", overflow: "hidden" }}>
        <div style={{ position: "absolute", left: 0, top: 0, height: "100%", width: `${pct}%`, background: color, borderRadius: 99, transition: "width 0.8s cubic-bezier(0.4,0,0.2,1)" }} />
      </div>
      <div style={{ marginTop: 4, display: "flex", justifyContent: "flex-end" }}>
        <span style={{ fontSize: "0.68rem", color: "rgba(255,255,255,0.3)" }}>attn: {wPct.toFixed(1)}%</span>
      </div>
    </div>
  );
}

function SupplierCard({ s, rank, onClick }) {
  const cfg = getRiskConfig(s.risk_level);
  const dominantMeta = SIGNAL_META[s.dominant_signal] || {};

  return (
    <div
      onClick={() => onClick(s)}
      style={{
        background: "rgba(15,15,25,0.7)", border: `1px solid ${cfg.border}`,
        borderRadius: 16, padding: "1.25rem 1.5rem", cursor: "pointer",
        transition: "all 0.25s cubic-bezier(0.4,0,0.2,1)",
        boxShadow: `inset 0 0 0 1px ${cfg.border}, ${cfg.glow}`,
        backdropFilter: "blur(10px)",
        position: "relative", overflow: "hidden",
      }}
      onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-3px)"; e.currentTarget.style.boxShadow = `inset 0 0 0 1px ${cfg.color}, ${cfg.glow}`; }}
      onMouseLeave={e => { e.currentTarget.style.transform = "translateY(0)"; e.currentTarget.style.boxShadow = `inset 0 0 0 1px ${cfg.border}, ${cfg.glow}`; }}
    >
      {/* Rank badge */}
      <span style={{ position: "absolute", top: 10, right: 12, fontSize: "0.65rem", color: "rgba(255,255,255,0.2)", fontWeight: 700 }}>#{rank}</span>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.75rem" }}>
        <div>
          <h3 style={{ margin: 0, fontSize: "1rem", fontWeight: 700, color: "#f3f4f6" }}>{s.supplier_name}</h3>
          <span style={{ fontSize: "0.75rem", color: "rgba(255,255,255,0.35)" }}>
            {s.shipping_details?.destination_port || "—"}
          </span>
        </div>
        <RiskPill level={s.risk_level} />
      </div>

      {/* Score gauge */}
      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        <GaugeArc score={s.risk_score} />
        <div style={{ flex: 1 }}>
          <p style={{ margin: "0 0 4px 0", fontSize: "0.7rem", color: "rgba(255,255,255,0.4)", textTransform: "uppercase", letterSpacing: "0.08em" }}>Dominant Signal</p>
          <div style={{ display: "flex", alignItems: "center", gap: 5, color: cfg.color, fontSize: "0.82rem", fontWeight: 600 }}>
            {dominantMeta.icon} {dominantMeta.label || s.dominant_signal}
          </div>
          <div style={{ marginTop: 8, display: "flex", gap: 6, flexWrap: "wrap" }}>
            <span style={{ fontSize: "0.7rem", background: "rgba(255,255,255,0.05)", padding: "2px 8px", borderRadius: 6, color: "#9ca3af" }}>
              📰 News {s.external_score}%
            </span>
            <span style={{ fontSize: "0.7rem", background: "rgba(255,255,255,0.05)", padding: "2px 8px", borderRadius: 6, color: "#9ca3af" }}>
              🚢 Ship {s.shipping_score}%
            </span>
          </div>
        </div>
      </div>

      <div style={{ position: "absolute", bottom: 10, right: 14, color: "rgba(255,255,255,0.15)" }}>
        <ArrowUpRight size={14} />
      </div>
    </div>
  );
}

function DetailModal({ s, onClose }) {
  const [expandShipping, setExpandShipping] = useState(false);
  if (!s) return null;
  const cfg = getRiskConfig(s.risk_level);

  const topArticles = s.news_details?.top_articles || [];

  return (
    <div onClick={onClose} style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)",
      backdropFilter: "blur(8px)", zIndex: 9999, display: "flex",
      alignItems: "center", justifyContent: "center", padding: "1.5rem"
    }}>
      <div onClick={e => e.stopPropagation()} style={{
        background: "#0d0d18", border: `1px solid ${cfg.border}`,
        borderRadius: 20, width: "100%", maxWidth: 860,
        maxHeight: "92vh", overflowY: "auto",
        boxShadow: `0 30px 80px -20px rgba(0,0,0,0.9), ${cfg.glow}`,
        display: "flex", flexDirection: "column",
      }}>

        {/* Header */}
        <div style={{
          padding: "1.5rem 2rem", borderBottom: "1px solid rgba(255,255,255,0.07)",
          display: "flex", justifyContent: "space-between", alignItems: "center",
          position: "sticky", top: 0, background: "rgba(13,13,24,0.97)", backdropFilter: "blur(20px)", zIndex: 10,
        }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 4 }}>
              <h2 style={{ margin: 0, fontSize: "1.4rem", fontWeight: 800 }}>{s.supplier_name}</h2>
              <RiskPill level={s.risk_level} />
            </div>
            <p style={{ margin: 0, fontSize: "0.82rem", color: "rgba(255,255,255,0.4)" }}>
              Softmax Attention BOM Shock Analysis · dest: {s.shipping_details?.destination_port || "—"}
            </p>
          </div>
          <button onClick={onClose} style={{
            background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)",
            color: "#9ca3af", cursor: "pointer", padding: "8px", borderRadius: "10px",
            display: "flex", alignItems: "center", transition: "all 0.2s"
          }}
            onMouseEnter={e => e.currentTarget.style.background = "rgba(255,255,255,0.1)"}
            onMouseLeave={e => e.currentTarget.style.background = "rgba(255,255,255,0.06)"}
          >
            <X size={20} />
          </button>
        </div>

        <div style={{ padding: "1.75rem 2rem", display: "flex", flexDirection: "column", gap: "1.75rem" }}>

          {/* Score overview row */}
          <div style={{ display: "grid", gridTemplateColumns: "auto 1fr 1fr 1fr", gap: "1.25rem", alignItems: "center" }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
              <GaugeArc score={s.risk_score} />
              <span style={{ fontSize: "0.7rem", color: "rgba(255,255,255,0.4)", textTransform: "uppercase", letterSpacing: "0.08em" }}>Total Risk</span>
            </div>
            {[
              { label: "Internal", value: `${Object.values(s.internal_scores || {}).reduce((a, v) => a + v, 0) / 5 * 100 | 0}%`, sub: "Avg of 5 internal metrics", color: "#818cf8" },
              { label: "News Sentiment", value: `${s.external_score}%`, sub: "VADER NLP on live news", color: "#22d3ee" },
              { label: "Shipping Risk", value: `${s.shipping_score}%`, sub: `${s.shipping_details?.total_delay_days ?? 0} delay days`, color: "#f97316" },
            ].map(({ label, value, sub, color }) => (
              <div key={label} style={{
                padding: "1rem 1.25rem", borderRadius: 12,
                background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)"
              }}>
                <p style={{ margin: "0 0 2px", fontSize: "0.7rem", color: "rgba(255,255,255,0.4)", textTransform: "uppercase", letterSpacing: "0.08em" }}>{label}</p>
                <p style={{ margin: "0 0 4px", fontSize: "1.75rem", fontWeight: 800, color }}>{value}</p>
                <p style={{ margin: 0, fontSize: "0.72rem", color: "rgba(255,255,255,0.3)" }}>{sub}</p>
              </div>
            ))}
          </div>

          {/* Radar + Signals */}
          <div style={{ display: "grid", gridTemplateColumns: "220px 1fr", gap: "1.5rem" }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "1rem", borderRadius: 14, background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)" }}>
              <RadarChart weights={s.adaptive_weights || {}} scores={s.internal_scores || {}} />
              <div style={{ display: "flex", gap: 16, marginTop: 8, fontSize: "0.68rem", color: "rgba(255,255,255,0.4)" }}>
                <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                  <span style={{ width: 14, height: 2, background: "#6366f1", display: "inline-block" }} /> Attention Wt
                </span>
                <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                  <span style={{ width: 14, height: 2, background: "#ef4444", borderTop: "2px dashed #ef4444", display: "inline-block" }} /> Risk Score
                </span>
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <p style={{ margin: "0 0 6px", fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.08em", color: "rgba(255,255,255,0.35)" }}>
                7-Signal Softmax Breakdown
              </p>
              {Object.entries(s.adaptive_weights || {}).sort((a, b) => b[1] - a[1]).map(([key, w]) => {
                const meta = SIGNAL_META[key] || { label: key, icon: <Activity size={14} /> };
                return (
                  <SignalBar
                    key={key}
                    label={meta.label}
                    icon={meta.icon}
                    value={s.internal_scores?.[key] ?? (key === "news_risk" ? s.external_score / 100 : key === "shipping_risk" ? s.shipping_score / 100 : 0)}
                    weight={w}
                    isWinner={key === s.dominant_signal}
                  />
                );
              })}
            </div>
          </div>

          {/* Shipping Details */}
          <div style={{ borderRadius: 14, border: "1px solid rgba(255,255,255,0.07)", overflow: "hidden" }}>
            <button
              onClick={() => setExpandShipping(p => !p)}
              style={{
                width: "100%", padding: "1rem 1.25rem", background: "rgba(255,255,255,0.03)",
                border: "none", color: "#f3f4f6", cursor: "pointer",
                display: "flex", alignItems: "center", justifyContent: "space-between", fontSize: "0.9rem", fontWeight: 600
              }}
            >
              <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Anchor size={15} color="#f97316" /> Shipping Intelligence
                <span style={{ fontSize: "0.72rem", background: "rgba(249,115,22,0.1)", color: "#f97316", padding: "2px 8px", borderRadius: 6, fontWeight: 500 }}>
                  {s.shipping_details?.total_delay_days ?? 0} delay days
                </span>
              </span>
              {expandShipping ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>
            {expandShipping && (
              <div style={{ padding: "1rem 1.25rem", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
                {[
                  ["Origin Weather",    s.shipping_details?.origin_risks?.origin_weather],
                  ["Origin Earthquake", s.shipping_details?.origin_risks?.origin_quake],
                  ["Political Risk",    s.shipping_details?.origin_risks?.origin_politics],
                  ["Conflict Risk",     s.shipping_details?.origin_risks?.origin_conflict],
                  ["Dest Weather",      s.shipping_details?.dest_risks?.dest_weather],
                  ["Disasters",         s.shipping_details?.dest_risks?.dest_disasters],
                ].map(([name, data]) => data && (
                  <div key={name} style={{ padding: "0.75rem 1rem", borderRadius: 10, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
                    <p style={{ margin: "0 0 2px", fontSize: "0.72rem", color: "rgba(255,255,255,0.4)", textTransform: "uppercase", letterSpacing: "0.06em" }}>{name}</p>
                    <p style={{ margin: 0, fontSize: "1rem", fontWeight: 700, color: data.delay_days > 2 ? "#f97316" : "#22c55e" }}>
                      {data.delay_days ?? 0} days delay
                    </p>
                    {data.risk_level && <span style={{ fontSize: "0.7rem", color: "rgba(255,255,255,0.3)" }}>{data.risk_level}</span>}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* News Articles */}
          {topArticles.length > 0 && (
            <div>
              <p style={{ margin: "0 0 0.75rem", fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.08em", color: "rgba(255,255,255,0.35)", display: "flex", alignItems: "center", gap: 6 }}>
                <Newspaper size={13} /> Live News Signals
              </p>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px,1fr))", gap: "0.75rem" }}>
                {topArticles.map((a, i) => {
                  const sentColor = a.sentiment === "NEGATIVE" ? "#ef4444" : a.sentiment === "POSITIVE" ? "#22c55e" : "#9ca3af";
                  return (
                    <a key={i} href={a.url || "#"} target="_blank" rel="noopener noreferrer"
                      style={{
                        display: "flex", flexDirection: "column", textDecoration: "none", color: "inherit",
                        padding: "1rem", borderRadius: 12, background: "rgba(255,255,255,0.03)",
                        border: `1px solid rgba(255,255,255,0.07)`, transition: "all 0.2s"
                      }}
                      onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-2px)"; e.currentTarget.style.background = "rgba(255,255,255,0.06)"; }}
                      onMouseLeave={e => { e.currentTarget.style.transform = "translateY(0)"; e.currentTarget.style.background = "rgba(255,255,255,0.03)"; }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                        <span style={{ fontSize: "0.68rem", fontWeight: 700, color: sentColor, textTransform: "uppercase", letterSpacing: "0.06em" }}>{a.sentiment || "NEUTRAL"}</span>
                        <span style={{ fontSize: "0.68rem", color: "rgba(255,255,255,0.3)" }}>{a.published_at ? new Date(a.published_at).toLocaleDateString() : ""}</span>
                      </div>
                      <h4 style={{ margin: "0 0 auto", fontSize: "0.85rem", lineHeight: 1.4, color: "#f3f4f6" }}>{a.title}</h4>
                      <p style={{ margin: "8px 0 0", fontSize: "0.72rem", color: "rgba(255,255,255,0.3)" }}>{a.source}</p>
                    </a>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ─── Main Page ───────────────────────────────────────────────── */

export default function FinalRiskDashboard() {
  const { session } = useContext(AuthContext);
  const userId = session?.user?.id;

  const [loading, setLoading]   = useState(false);
  const [data, setData]         = useState(() => {
    const cached = sessionStorage.getItem("finalRiskData");
    return cached ? JSON.parse(cached) : null;
  });
  const [error, setError]       = useState(null);
  const [selected, setSelected] = useState(null);
  const [sortBy, setSortBy]     = useState("risk_score");
  const [filterLevel, setFilter] = useState("ALL");
  const [search, setSearch]     = useState("");

  async function runAnalysis() {
    if (!userId) { setError("Not logged in."); return; }
    setLoading(true);
    setError(null);
    try {
      const res = await predictAllFinalRisk(userId);
      const list = res.data || [];
      setData(list);
      sessionStorage.setItem("finalRiskData", JSON.stringify(list));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const stats = useMemo(() => {
    if (!data?.length) return null;
    const n = data.length;
    const avg = data.reduce((s, d) => s + d.risk_score, 0) / n;
    const critCount  = data.filter(d => d.risk_level === "CRITICAL").length;
    const highCount  = data.filter(d => d.risk_level === "HIGH").length;
    const safeCount  = data.filter(d => d.risk_level === "LOW").length;
    const topSignal  = (() => {
      const counts = {};
      data.forEach(d => { counts[d.dominant_signal] = (counts[d.dominant_signal] || 0) + 1; });
      return Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] || "—";
    })();
    return { n, avg, critCount, highCount, safeCount, topSignal };
  }, [data]);

  const filtered = useMemo(() => {
    if (!data) return [];
    return data
      .filter(d => filterLevel === "ALL" || d.risk_level === filterLevel)
      .filter(d => !search || d.supplier_name.toLowerCase().includes(search.toLowerCase()))
      .sort((a, b) => {
        if (sortBy === "risk_score") return b.risk_score - a.risk_score;
        if (sortBy === "name") return a.supplier_name.localeCompare(b.supplier_name);
        if (sortBy === "news") return b.external_score - a.external_score;
        if (sortBy === "shipping") return b.shipping_score - a.shipping_score;
        return 0;
      });
  }, [data, filterLevel, search, sortBy]);

  const STAT_CARDS = stats ? [
    { icon: <BarChart3 size={22} />, color: "#818cf8", value: stats.n,                  label: "Suppliers Analyzed" },
    { icon: <AlertTriangle size={22} />, color: "#ef4444", value: `${stats.critCount + stats.highCount}`,  label: "High Risk Flags" },
    { icon: <ShieldCheck size={22} />, color: "#22c55e", value: stats.safeCount,         label: "Low Risk Suppliers" },
    { icon: <Activity size={22} />, color: "#eab308", value: `${stats.avg.toFixed(1)}`,  label: "Avg Risk Score" },
    { icon: <Radar size={22} />, color: "#22d3ee", value: SIGNAL_META[stats.topSignal]?.label || stats.topSignal, label: "Most Common Threat", small: true },
  ] : [];

  return (
    <div style={{ minHeight: "100vh", padding: "2rem 2.5rem", background: "transparent" }}>

      {/* ── Header ── */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "2rem" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 6 }}>
            <div style={{ width: 42, height: 42, borderRadius: 12, background: "linear-gradient(135deg,#6366f1,#8b5cf6)", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 0 20px rgba(99,102,241,0.4)" }}>
              <Brain size={22} color="white" />
            </div>
            <h1 style={{ margin: 0, fontSize: "1.7rem", fontWeight: 800, background: "linear-gradient(135deg, #fff 30%, #818cf8)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
              Agentic BOM Shock Predictor
            </h1>
          </div>
          <p style={{ margin: 0, color: "rgba(255,255,255,0.4)", fontSize: "0.88rem" }}>
            Softmax Attention · 7 Signals · Internal × News × Shipping
          </p>
        </div>
        {data && (
          <button onClick={runAnalysis} disabled={loading}
            style={{
              display: "flex", alignItems: "center", gap: 8, padding: "10px 20px",
              borderRadius: 10, border: "1px solid rgba(99,102,241,0.4)",
              background: "rgba(99,102,241,0.12)", color: "#818cf8",
              cursor: "pointer", fontSize: "0.85rem", fontWeight: 600, transition: "all 0.2s"
            }}
            onMouseEnter={e => e.currentTarget.style.background = "rgba(99,102,241,0.22)"}
            onMouseLeave={e => e.currentTarget.style.background = "rgba(99,102,241,0.12)"}
          >
            <RefreshCw size={15} className={loading ? "spin" : ""} /> Re-Run Analysis
          </button>
        )}
      </div>

      {/* ── Empty / Hero state ── */}
      {!data && !loading && (
        <div style={{
          textAlign: "center", padding: "5rem 2rem",
          background: "rgba(13,13,24,0.8)", border: "1px solid rgba(99,102,241,0.2)",
          borderRadius: 24, backdropFilter: "blur(20px)",
          boxShadow: "0 0 60px -20px rgba(99,102,241,0.3)"
        }}>
          <div style={{ width: 80, height: 80, borderRadius: "50%", background: "linear-gradient(135deg,#6366f1,#8b5cf6)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 1.75rem", boxShadow: "0 0 40px rgba(99,102,241,0.5)" }}>
            <Zap size={36} color="white" />
          </div>
          <h2 style={{ fontSize: "2rem", fontWeight: 800, marginBottom: "1rem", background: "linear-gradient(135deg,#fff,#818cf8)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            Activate BOM Shock Intelligence
          </h2>
          <p style={{ color: "rgba(255,255,255,0.45)", maxWidth: 520, margin: "0 auto 2.5rem", lineHeight: 1.7, fontSize: "0.95rem" }}>
            Fuses <strong style={{ color: "#818cf8" }}>internal supplier metrics</strong>, live{" "}
            <strong style={{ color: "#22d3ee" }}>news sentiment</strong>, and real-time{" "}
            <strong style={{ color: "#f97316" }}>shipping signals</strong> through a Softmax Attention engine
            to expose the dominant risk driver for every supplier.
          </p>
          <div style={{ display: "flex", justifyContent: "center", gap: "1.5rem", marginBottom: "2.5rem", flexWrap: "wrap" }}>
            {[
              { icon: <Cpu size={18} />, label: "5 Internal Metrics", color: "#818cf8" },
              { icon: <Newspaper size={18} />, label: "Live News VADER", color: "#22d3ee" },
              { icon: <Globe size={18} />, label: "6 Shipping APIs", color: "#f97316" },
            ].map(({ icon, label, color }) => (
              <div key={label} style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 16px", borderRadius: 99, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.09)", fontSize: "0.82rem", color }}>
                {icon} {label}
              </div>
            ))}
          </div>
          <button onClick={runAnalysis}
            style={{
              padding: "14px 36px", borderRadius: 99, border: "none",
              background: "linear-gradient(135deg,#6366f1,#8b5cf6)",
              color: "white", fontSize: "1rem", fontWeight: 700, cursor: "pointer",
              boxShadow: "0 0 30px rgba(99,102,241,0.5)", transition: "all 0.2s"
            }}
            onMouseEnter={e => e.currentTarget.style.boxShadow = "0 0 50px rgba(99,102,241,0.7)"}
            onMouseLeave={e => e.currentTarget.style.boxShadow = "0 0 30px rgba(99,102,241,0.5)"}
          >
            Run Agentic Risk Analysis
          </button>
          {error && (
            <div style={{ marginTop: "1.5rem", padding: "12px 20px", borderRadius: 10, background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171", fontSize: "0.88rem" }}>
              {error}
            </div>
          )}
        </div>
      )}

      {/* ── Loading ── */}
      {loading && (
        <div style={{ textAlign: "center", padding: "6rem 2rem" }}>
          <div style={{ width: 64, height: 64, borderRadius: "50%", border: "3px solid rgba(99,102,241,0.2)", borderTop: "3px solid #6366f1", animation: "spin 1s linear infinite", margin: "0 auto 1.5rem" }} />
          <h2 style={{ fontSize: "1.4rem", marginBottom: "0.5rem" }}>Running Softmax Attention Engine…</h2>
          <p style={{ color: "rgba(255,255,255,0.4)", maxWidth: 400, margin: "0 auto", lineHeight: 1.6 }}>
            Fetching live news sentiment, shipping delay signals, and cross-referencing internal supplier DB.
          </p>
        </div>
      )}

      {/* ── Dashboard ── */}
      {data && !loading && (
        <div style={{ animation: "fadeIn 0.5s ease-out" }}>

          {/* Stat cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px,1fr))", gap: "1rem", marginBottom: "2rem" }}>
            {STAT_CARDS.map(({ icon, color, value, label, small }) => (
              <div key={label} style={{
                padding: "1.1rem 1.25rem", borderRadius: 14,
                background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)",
                backdropFilter: "blur(10px)"
              }}>
                <div style={{ color, marginBottom: 8, opacity: 0.85 }}>{icon}</div>
                <p style={{ margin: "0 0 2px", fontSize: small ? "1rem" : "1.6rem", fontWeight: 800, color }}>{value}</p>
                <p style={{ margin: 0, fontSize: "0.75rem", color: "rgba(255,255,255,0.4)", lineHeight: 1.3 }}>{label}</p>
              </div>
            ))}
          </div>

          {/* Filters */}
          <div style={{ display: "flex", gap: "0.75rem", marginBottom: "1.5rem", flexWrap: "wrap", alignItems: "center" }}>
            <input
              placeholder="Search suppliers…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{
                padding: "8px 14px", borderRadius: 10, border: "1px solid rgba(255,255,255,0.1)",
                background: "rgba(255,255,255,0.05)", color: "white", fontSize: "0.85rem",
                outline: "none", minWidth: 200
              }}
            />
            {["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map(lvl => {
              const cfg = lvl === "ALL" ? { color: "#9ca3af" } : getRiskConfig(lvl);
              return (
                <button key={lvl} onClick={() => setFilter(lvl)}
                  style={{
                    padding: "6px 14px", borderRadius: 99, border: `1px solid ${filterLevel === lvl ? cfg.color : "rgba(255,255,255,0.1)"}`,
                    background: filterLevel === lvl ? `${cfg.color}20` : "transparent",
                    color: filterLevel === lvl ? cfg.color : "rgba(255,255,255,0.4)",
                    cursor: "pointer", fontSize: "0.78rem", fontWeight: 600, transition: "all 0.2s"
                  }}
                >{lvl}</button>
              );
            })}
            <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8, fontSize: "0.8rem", color: "rgba(255,255,255,0.4)" }}>
              Sort:
              {[["risk_score", "Risk"], ["name", "Name"], ["news", "News"], ["shipping", "Ship"]].map(([k, l]) => (
                <button key={k} onClick={() => setSortBy(k)}
                  style={{
                    padding: "5px 10px", borderRadius: 8, border: "1px solid rgba(255,255,255,0.1)",
                    background: sortBy === k ? "rgba(99,102,241,0.15)" : "transparent",
                    color: sortBy === k ? "#818cf8" : "rgba(255,255,255,0.4)",
                    cursor: "pointer", fontSize: "0.78rem", transition: "all 0.2s"
                  }}
                >{l}</button>
              ))}
            </div>
          </div>

          {/* Cards grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(290px, 1fr))", gap: "1.1rem" }}>
            {filtered.map((s, i) => (
              <SupplierCard key={s.supplier_id || s.supplier_name} s={s} rank={i + 1} onClick={setSelected} />
            ))}
            {filtered.length === 0 && (
              <div style={{ gridColumn: "1/-1", padding: "3rem", textAlign: "center", color: "rgba(255,255,255,0.3)" }}>
                No suppliers match the current filter.
              </div>
            )}
          </div>

          {error && (
            <div style={{ marginTop: "1rem", padding: "12px 20px", borderRadius: 10, background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171", fontSize: "0.88rem" }}>
              {error}
            </div>
          )}
        </div>
      )}

      {/* Detail Modal */}
      {selected && <DetailModal s={selected} onClose={() => setSelected(null)} />}

      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes spin   { to { transform: rotate(360deg); } }
        .spin { animation: spin 1s linear infinite; }
      `}</style>
    </div>
  );
}
