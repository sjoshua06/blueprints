import { useState, useMemo } from "react";
import { predictAllSuppliersRisk } from "../services/api";
import ResultsTable from "../components/ResultsTable";
import RiskBadge from "../components/RiskBadge";
import { 
  Building2, ShieldAlert, ShieldCheck, TrendingUp, RefreshCw, 
  ShieldHalf, X, Newspaper, ArrowRight, Activity 
} from "lucide-react";

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

  // Modal State
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [showModal, setShowModal] = useState(false);

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
    // Risk score from array is now 0-100
    const avgRisk = results.reduce((sum, item) => sum + item.risk_score, 0) / count;
    const highRiskCount = results.filter(item => item.risk_score >= 60).length;
    const lowRiskCount = results.filter(item => item.risk_score < 30).length;

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
      // Divide by 100 since the RiskBadge component expects 0-1
      render: (v) => (v != null ? <RiskBadge score={v / 100} /> : "—") 
    },
    {
      key: "actions",
      label: "",
      render: (_, row) => (
        <button 
          className="btn btn--outline" 
          onClick={() => { setSelectedSupplier(row); setShowModal(true); }}
          style={{ padding: "6px 12px", fontSize: "0.8rem", borderRadius: "6px", display: "flex", alignItems: "center", gap: "6px" }}
        >
          View Insights <ArrowRight size={14} />
        </button>
      )
    }
  ];

  return (
    <div className="setup-page">
      <div className="setup-page__container" style={{ maxWidth: "1200px", width: "100%" }}>
        
        {/* State 1: Before Prediction (Hero) */}
        {!results && !loading && (
          <div style={{ textAlign: "center", padding: "4rem 2rem", background: "var(--glass-bg)", border: "1px solid var(--glass-border)", borderRadius: "var(--radius-lg)", backdropFilter: "blur(20px)", boxShadow: "var(--glass-shadow)", marginTop: "2rem" }}>
            <div style={{ fontSize: "4rem", marginBottom: "1.5rem", display: 'flex', justifyContent: 'center' }}><ShieldHalf size={64} color="#818cf8" /></div>
            <h1 style={{ fontSize: "2.5rem", fontWeight: "800", marginBottom: "1rem", background: "linear-gradient(135deg, #FFF, #818cf8)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
              AI Supplier Risk Intelligence
            </h1>
            <p style={{ fontSize: "1.1rem", color: "var(--text-secondary)", maxWidth: "600px", margin: "0 auto 2.5rem", lineHeight: "1.6" }}>
              Deploy our hybrid AI engine to instantly cross-reference internal supplier history with external global news sentiment, forecasting future supply chain disruptions.
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
            <p style={{ color: "var(--text-secondary)" }}>Fetching real-time global news sentiment and compiling internal heuristic models. This will take a moment.</p>
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
                <span className="sidebar__icon" style={{display: 'flex'}}><RefreshCw size={18} /></span> Re-Run Analysis
              </button>
            </div>

            {/* Dashboard Summary Cards */}
            {insights && (
              <div className="summary-cards" style={{ marginBottom: "2.5rem" }}>
                <div className="summary-card">
                  <span className="summary-card__icon"><Building2 size={24} color="#818cf8" /></span>
                  <div>
                    <p className="summary-card__value">{insights.count}</p>
                    <p className="summary-card__label">Suppliers Assessed</p>
                  </div>
                </div>
                
                <div className="summary-card">
                  <span className="summary-card__icon"><ShieldAlert size={24} color="#f87171" /></span>
                  <div>
                    <p className="summary-card__value" style={{ color: insights.highRiskCount > 0 ? "#f87171" : "inherit" }}>
                      {insights.highRiskCount}
                    </p>
                    <p className="summary-card__label">Critical Risk Flags</p>
                  </div>
                </div>

                <div className="summary-card">
                  <span className="summary-card__icon"><ShieldCheck size={24} color="#34d399" /></span>
                  <div>
                    <p className="summary-card__value" style={{ color: "#34d399" }}>
                      {insights.lowRiskCount}
                    </p>
                    <p className="summary-card__label">Safe Suppliers</p>
                  </div>
                </div>

                <div className="summary-card">
                  <span className="summary-card__icon"><Activity size={24} color="#fbbf24" /></span>
                  <div>
                    <p className="summary-card__value">
                      {(insights.avgRisk).toFixed(1)} / 100
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

      {/* Slide-out or centered Modal for Insights */}
      {showModal && selectedSupplier && (
        <div 
          onClick={() => setShowModal(false)}
          style={{
            position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
            background: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)",
            zIndex: 9999, display: "flex", alignItems: "center", justifyContent: "center",
            padding: "2rem"
          }}
        >
          <div 
            onClick={(e) => e.stopPropagation()}
            style={{ 
              background: "#1e1e24", border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: "16px", width: "100%", maxWidth: "800px",
              maxHeight: "90vh", overflowY: "auto", boxShadow: "0 25px 50px -12px rgba(0,0,0,0.5)",
              display: "flex", flexDirection: "column"
            }}
          >
            {/* Modal Header */}
            <div style={{ padding: "1.5rem 2rem", borderBottom: "1px solid rgba(255,255,255,0.05)", display: "flex", justifyContent: "space-between", alignItems: "center", position: "sticky", top: 0, background: "rgba(30, 30, 36, 0.95)", backdropFilter: "blur(10px)", zIndex: 10 }}>
              <div>
                <h2 style={{ margin: 0, fontSize: "1.5rem", display: "flex", alignItems: "center", gap: "12px" }}>
                  {selectedSupplier.supplier_name} 
                  <RiskBadge score={(selectedSupplier.risk_score || 0) / 100} />
                </h2>
                <p style={{ margin: "5px 0 0 0", color: "#9ca3af", fontSize: "0.9rem" }}>AI Risk Analysis Breakdown</p>
              </div>
              <button 
                onClick={() => setShowModal(false)}
                style={{ background: "transparent", border: "none", color: "#9ca3af", cursor: "pointer", padding: "8px", borderRadius: "8px" }}
                onMouseOver={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.1)"}
                onMouseOut={(e) => e.currentTarget.style.background = "transparent"}
              >
                <X size={24} />
              </button>
            </div>

            {/* Modal Content */}
            <div style={{ padding: "2rem", display: "grid", gridTemplateColumns: "1fr", gap: "2rem" }}>
              
              {/* Internal vs External Scores */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                <div style={{ background: "rgba(255,255,255,0.03)", padding: "1.5rem", borderRadius: "12px", border: "1px solid rgba(255,255,255,0.05)" }}>
                   <p style={{ margin: "0 0 0.5rem 0", color: "#9ca3af", fontSize: "0.9rem", textTransform: "uppercase", letterSpacing: "1px" }}>Data Profile</p>
                   <h3 style={{ margin: 0, fontSize: "2.5rem", fontWeight: "700", color: "white" }}>
                     {selectedSupplier.internal_risk_score?.toFixed(1) || "0.0"} <span style={{ fontSize: "1rem", color: "#6b7280" }}>/100</span>
                   </h3>
                   <p style={{ margin: "1rem 0 0 0", fontSize: "0.85rem", color: "#9ca3af" }}>Driven by internal DB metrics (Defect rates, OTD, Lead time).</p>
                </div>

                <div style={{ background: "rgba(255,255,255,0.03)", padding: "1.5rem", borderRadius: "12px", border: "1px solid rgba(255,255,255,0.05)" }}>
                   <p style={{ margin: "0 0 0.5rem 0", color: "#9ca3af", fontSize: "0.9rem", textTransform: "uppercase", letterSpacing: "1px" }}>Global Sentiment</p>
                   <h3 style={{ margin: 0, fontSize: "2.5rem", fontWeight: "700", color: "white" }}>
                     {selectedSupplier.external_risk_score?.toFixed(1) || "0.0"} <span style={{ fontSize: "1rem", color: "#6b7280" }}>/100</span>
                   </h3>
                   <p style={{ margin: "1rem 0 0 0", fontSize: "0.85rem", color: "#9ca3af" }}>Driven by real-time News API analysis of country & company.</p>
                </div>
              </div>

              {/* Factors */}
              <div>
                <h3 style={{ borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: "0.5rem", marginBottom: "1rem" }}>Contributing Factors</h3>
                <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                  {selectedSupplier.factors?.length > 0 ? selectedSupplier.factors.map((f, i) => (
                    <li key={i} style={{ background: "rgba(0,0,0,0.2)", padding: "1rem", borderRadius: "8px", display: "flex", alignItems: "flex-start", gap: "1rem", borderLeft: f.impact >= 20 ? "3px solid #f87171" : f.impact >= 10 ? "3px solid #fbbf24" : "3px solid #34d399" }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                          <strong style={{ fontSize: "1.05rem", color: "#f3f4f6" }}>{f.factor}</strong>
                          <span style={{ fontSize: "0.85rem", background: "rgba(255,255,255,0.1)", padding: "2px 8px", borderRadius: "12px", color: "#d1d5db" }}>Impact: {f.impact.toFixed(1)}%</span>
                        </div>
                        <p style={{ margin: 0, color: "#9ca3af", fontSize: "0.9rem", lineHeight: "1.5" }}>{f.detail}</p>
                      </div>
                    </li>
                  )) : (
                    <li style={{ color: "#9ca3af", fontStyle: "italic" }}>No specific risk factors detected.</li>
                  )}
                </ul>
              </div>

              {/* News Articles */}
              <div>
                <h3 style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: "0.5rem", marginBottom: "1rem" }}>
                  <Newspaper size={18} /> Related Public News
                </h3>
                
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "1rem" }}>
                  {selectedSupplier.news_articles?.length > 0 ? (
                    selectedSupplier.news_articles.map((news, i) => (
                      <a href={news.url || "#"} target="_blank" rel="noopener noreferrer" key={i} style={{ display: "flex", flexDirection: "column", background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)", borderRadius: "10px", padding: "1.25rem", textDecoration: "none", color: "inherit", transition: "transform 0.2s, background 0.2s" }} onMouseOver={(e) => { e.currentTarget.style.transform = "translateY(-2px)"; e.currentTarget.style.background = "rgba(255,255,255,0.06)"; }} onMouseOut={(e) => { e.currentTarget.style.transform = "translateY(0)"; e.currentTarget.style.background = "rgba(255,255,255,0.03)"; }}>
                        
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                            <span style={{ fontSize: "0.7rem", fontWeight: "bold", padding: "4px 8px", borderRadius: "4px", background: news.sentiment === "NEGATIVE" ? "rgba(239,68,68,0.1)" : news.sentiment === "POSITIVE" ? "rgba(52,211,153,0.1)" : "rgba(255,255,255,0.1)", color: news.sentiment === "NEGATIVE" ? "#f87171" : news.sentiment === "POSITIVE" ? "#34d399" : "#9ca3af", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                              {news.sentiment}
                            </span>
                            <span style={{ fontSize: "0.75rem", color: "#6b7280" }}>
                              {new Date(news.published_at).toLocaleDateString()}
                            </span>
                        </div>
                        
                        <h4 style={{ margin: "0 0 0.5rem 0", fontSize: "1rem", lineHeight: "1.4", color: "#f3f4f6" }}>{news.title}</h4>
                        <p style={{ margin: "auto 0 0 0", fontSize: "0.8rem", color: "#9ca3af", fontWeight: "500" }}>{news.source}</p>
                      </a>
                    ))
                  ) : (
                     <p style={{ color: "#9ca3af", fontStyle: "italic", padding: "1rem", background: "rgba(255,255,255,0.02)", borderRadius: "8px", border: "1px dashed rgba(255,255,255,0.1)" }}>No significant news articles detected for this supplier in the last 30 days.</p>
                  )}
                </div>
              </div>

            </div>
          </div>
        </div>
      )}
      
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
