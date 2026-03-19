import { useState, useMemo } from "react";
import { predictAllSuppliersRisk } from "../services/api";
import ResultsTable from "../components/ResultsTable";
import RiskBadge from "../components/RiskBadge";

// Helper component for a little gauge or progress bar in the table
function ProgressBar({ value, max = 100, colorClass = "success" }) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));
  
  // Choose gradient based on color string
  let gradient = "linear-gradient(90deg, #34d399, #10b981)"; // default Green
  if (colorClass === "warning") gradient = "linear-gradient(90deg, #fbbf24, #f59e0b)";
  if (colorClass === "error") gradient = "linear-gradient(90deg, #f87171, #ef4444)";

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "8px", minWidth: "120px" }}>
      <div style={{ flex: 1, height: "6px", background: "rgba(255,255,255,0.1)", borderRadius: "3px", overflow: "hidden" }}>
        <div style={{ width: `${percentage}%`, height: "100%", background: gradient, borderRadius: "3px" }} />
      </div>
      <span style={{ fontSize: "0.8rem", color: "#9CA3AF", minWidth: "30px" }}>{value.toFixed(0)}</span>
    </div>
  );
}

export default function SupplierRisk() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  async function handlePredict() {
    setLoading(true);
    setError(null);
    try {
      const resp = await predictAllSuppliersRisk();
      setResults(resp.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  // Calculate Insights metrics if we have results
  const insights = useMemo(() => {
    if (!results || results.length === 0) return null;
    
    const count = results.length;
    const avgRisk = results.reduce((sum, item) => sum + item.risk_score, 0) / count;
    const highRiskCount = results.filter(item => item.risk_score >= 0.6).length;
    const lowRiskCount = results.filter(item => item.risk_score < 0.3).length;

    return { count, avgRisk, highRiskCount, lowRiskCount };
  }, [results]);

  const columns = [
    { key: "supplier_id", label: "##" },
    { key: "supplier_name", label: "Supplier Entity", render: (v) => <strong style={{color: "#F3F4F6"}}>{v}</strong> },
    { 
      key: "reliability_score", 
      label: "Reliability", 
      render: (v) => <ProgressBar value={v} max={100} colorClass={v < 50 ? "error" : v < 80 ? "warning" : "success"} />
    },
    { key: "defect_rate", label: "Defect Rate (%)", render: (v) => v?.toFixed(2) + "%" },
    { 
      key: "on_time_delivery_rate", 
      label: "On-Time Delivery", 
      render: (v) => <ProgressBar value={v} max={100} colorClass={v < 50 ? "error" : v < 80 ? "warning" : "success"} />
    },
    { key: "avg_lead_time_days", label: "Lead Time", render: (v) => `${v?.toFixed(0)} days` },
    { 
      key: "risk_score", 
      label: "AI Risk Prediction", 
      render: (v) => (v != null ? <RiskBadge score={v} /> : "—") 
    },
  ];

  return (
    <div className="setup-page">
      <div className="setup-page__container" style={{ maxWidth: "1200px", width: "100%" }}>
        
        {/* State 1: Before Prediction (Hero) */}
        {!results && !loading && (
          <div style={{ textAlign: "center", padding: "4rem 2rem", background: "var(--glass-bg)", border: "1px solid var(--glass-border)", borderRadius: "var(--radius-lg)", backdropFilter: "blur(20px)", boxShadow: "var(--glass-shadow)", marginTop: "2rem" }}>
            <div style={{ fontSize: "4rem", marginBottom: "1.5rem" }}>🛡️</div>
            <h1 style={{ fontSize: "2.5rem", fontWeight: "800", marginBottom: "1rem", background: "linear-gradient(135deg, #FFF, #818cf8)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
              AI Supplier Risk Intelligence
            </h1>
            <p style={{ fontSize: "1.1rem", color: "var(--text-secondary)", maxWidth: "600px", margin: "0 auto 2.5rem", lineHeight: "1.6" }}>
              Deploy our machine learning model to instantly cross-reference delivery history, defect rates, and reliability scores across your entire supplier base to forecast future fulfillment risks.
            </p>
            
            <button 
              className="btn btn--primary btn--lg"
              onClick={handlePredict}
              style={{ padding: "16px 36px", fontSize: "1.1rem", borderRadius: "99px", letterSpacing: "0.02em" }}
            >
              Run Global Risk Prediction
            </button>
            
            {error && (
              <div className="setup-page__error" style={{ marginTop: "2rem", display: "inline-block", padding: "12px 24px", background: "var(--error-bg)", borderRadius: "8px" }}>
                <strong>Failed to run model:</strong> {error}
              </div>
            )}
          </div>
        )}

        {/* State 2: Loading Indicator */}
        {loading && (
          <div style={{ textAlign: "center", padding: "6rem 2rem" }}>
            <div className="spinner spinner--lg" style={{ marginBottom: "1.5rem", borderColor: "rgba(99, 102, 241, 0.2)", borderTopColor: "var(--accent)" }}></div>
            <h2 style={{ fontSize: "1.4rem", color: "var(--text-primary)", marginBottom: "0.5rem" }}>Analyzing Supply Chain Vectors...</h2>
            <p style={{ color: "var(--text-secondary)" }}>Running data through the supplier-risk heuristic model. This will only take a moment.</p>
          </div>
        )}

        {/* State 3: Results Dash */}
        {results && !loading && (
          <div className="fade-in" style={{ animation: "fadeIn 0.5s ease-out forwards" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
              <div>
                <h1 style={{ fontSize: "2rem", fontWeight: "700" }}>Risk Intelligence Report</h1>
                <p style={{ color: "var(--text-secondary)", marginTop: "0.5rem" }}>Latest model output across your active supplier base.</p>
              </div>
              <button className="btn btn--primary" onClick={handlePredict} style={{ borderRadius: "8px" }}>
                <span className="sidebar__icon">🔄</span> Re-Run Analysis
              </button>
            </div>

            {/* Dashboard Summary Cards */}
            {insights && (
              <div className="summary-cards" style={{ marginBottom: "2.5rem" }}>
                <div className="summary-card">
                  <span className="summary-card__icon" style={{ background: "rgba(99, 102, 241, 0.15)", color: "#818cf8" }}>🏢</span>
                  <div>
                    <p className="summary-card__value">{insights.count}</p>
                    <p className="summary-card__label">Suppliers Assessed</p>
                  </div>
                </div>
                
                <div className="summary-card">
                  <span className="summary-card__icon" style={{ background: "rgba(239, 68, 68, 0.15)", color: "#f87171" }}>⚠️</span>
                  <div>
                    <p className="summary-card__value" style={{ color: insights.highRiskCount > 0 ? "#f87171" : "inherit" }}>
                      {insights.highRiskCount}
                    </p>
                    <p className="summary-card__label">Critical Risk Flags</p>
                  </div>
                </div>

                <div className="summary-card">
                  <span className="summary-card__icon" style={{ background: "rgba(34, 197, 94, 0.15)", color: "#34d399" }}>🛡️</span>
                  <div>
                    <p className="summary-card__value" style={{ color: "#34d399" }}>
                      {insights.lowRiskCount}
                    </p>
                    <p className="summary-card__label">Safe Suppliers</p>
                  </div>
                </div>

                <div className="summary-card">
                  <span className="summary-card__icon" style={{ background: "rgba(245, 158, 11, 0.15)", color: "#fbbf24" }}>📈</span>
                  <div>
                    <p className="summary-card__value">
                      {(insights.avgRisk * 100).toFixed(1)}%
                    </p>
                    <p className="summary-card__label">Global Avg Risk</p>
                  </div>
                </div>
              </div>
            )}

            {/* Dynamic Table */}
            <div style={{ boxShadow: "var(--glass-shadow)", borderRadius: "var(--radius-lg)" }}>
              <ResultsTable 
                columns={columns} 
                data={results}
                emptyMessage="No suppliers found to analyze."
              />
            </div>

            {/* Visual key/Legend */}
            <div style={{ marginTop: "1rem", display: "flex", gap: "1.5rem", fontSize: "0.85rem", color: "var(--text-muted)", justifyContent: "center" }}>
              <span style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}><span style={{ width: "10px", height: "10px", borderRadius: "50%", background: "#ef4444" }}></span> High Risk ({">="} 60%)</span>
              <span style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}><span style={{ width: "10px", height: "10px", borderRadius: "50%", background: "#f59e0b" }}></span> Medium Risk (30 - 59%)</span>
              <span style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}><span style={{ width: "10px", height: "10px", borderRadius: "50%", background: "#22c55e" }}></span> Low Risk ({"<"} 30%)</span>
            </div>
            
          </div>
        )}
        
      </div>
      
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
