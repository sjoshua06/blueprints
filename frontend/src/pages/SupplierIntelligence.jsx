import { useState, useEffect } from "react";
import { Bot, Sparkles, Clock, DollarSign } from "lucide-react";
import { getSupplierInsights } from "../services/api";

export default function SupplierIntelligence() {
  const [globalInsightsLoading, setGlobalInsightsLoading] = useState(false);
  const [globalInsights, setGlobalInsights] = useState(null);
  const [analysisState, setAnalysisState] = useState([]);

  useEffect(() => {
     const stored = localStorage.getItem("globalSupplierState");
     if (stored) {
         setAnalysisState(JSON.parse(stored));
     }
  }, []);

  async function handleExtractGlobalInsights() {
    if (!analysisState || analysisState.length === 0) return;
    
    setGlobalInsightsLoading(true);
    try {
      const insightsArray = [];
      for (const item of analysisState) {
        if (item.missing > 0) {
          const data = await getSupplierInsights(item.component_id, item.component);
          insightsArray.push({
            componentId: item.component_id,
            componentName: item.component,
            data
          });
        }
      }
      setGlobalInsights(insightsArray);
    } catch (e) {
      console.error("Failed to extract insights", e);
    } finally {
      setGlobalInsightsLoading(false);
    }
  }

  const hasMissing = analysisState.some(i => i.missing > 0);

  return (
    <div className="setup-page">
      <div className="setup-page__container" style={{ maxWidth: "1000px" }}>
        
        {/* Global AI Intelligence Dashboard Section */}
        <div style={{ marginTop: "2rem", padding: "2rem", backgroundColor: "rgba(167, 139, 250, 0.05)", border: "1px solid rgba(167, 139, 250, 0.2)", borderRadius: "12px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem", borderBottom: "1px solid rgba(167, 139, 250, 0.2)", paddingBottom: "1rem" }}>
            <h3 style={{ fontSize: "1.35rem", fontWeight: "bold", color: "#A78BFA", display: "flex", alignItems: "center", gap: "0.5rem", margin: 0 }}>
              <Bot size={24} /> Supplier Intelligence Dashboard
            </h3>
            <div style={{ display: "flex", gap: "1rem" }}>
              <button
                onClick={handleExtractGlobalInsights}
                disabled={globalInsightsLoading || !hasMissing}
                style={{ 
                  display: "flex", alignItems: "center", gap: "0.4rem", padding: "0.5rem 1rem", fontSize: "0.9rem", fontWeight: "600",
                  backgroundColor: !hasMissing ? "rgba(255,255,255,0.1)" : "#8B5CF6", color: !hasMissing ? "#9CA3AF" : "white", border: "none", borderRadius: "6px", cursor: !hasMissing ? "not-allowed" : "pointer", boxShadow: !hasMissing ? "none" : "0 4px 6px -1px rgba(139, 92, 246, 0.3)"
                }}
              >
                <Sparkles size={16} /> {globalInsightsLoading ? "Analyzing Worldwide Data..." : "Extract Insights"}
              </button>
            </div>
          </div>

          {!hasMissing && (
             <div style={{ textAlign: "center", color: "#F87171", padding: "2rem 0" }}>
               You do not have any active missing components from your latest BOM Analysis. 
               Run a new BOM Analysis first.
             </div>
          )}

          {hasMissing && !globalInsights && !globalInsightsLoading && (
            <div style={{ textAlign: "center", color: "#9CA3AF", padding: "2rem 0" }}>
              Once suppliers start replying to RFQs, click "Extract Insights" to aggregate their bids.
            </div>
          )}
          
          {globalInsightsLoading && (
            <div style={{ textAlign: "center", padding: "3rem", color: "#A78BFA" }}>
              <span className="spinner spinner--md" style={{ marginBottom: "1rem", borderColor: "#A78BFA", borderTopColor: "transparent" }}></span>
              <p>Connecting to AI... Evaluating incoming constraints & optimal supplier matches...</p>
            </div>
          )}

          {globalInsights && globalInsights.length > 0 && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              {globalInsights.map((g, idx) => (
                <div key={idx} style={{ backgroundColor: "rgba(0,0,0,0.2)", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.05)", padding: "1.5rem" }}>
                   <h4 style={{ fontSize: "1.1rem", fontWeight: "bold", color: "#E5E7EB", marginBottom: "1rem", margin: 0 }}>{g.componentName}</h4>
                   
                   {(!g.data || !g.data.insights || g.data.insights.length === 0) ? (
                      <div style={{ color: "#F87171", fontSize: "0.9rem", marginTop: "1rem" }}>No insights or replies received for this component yet.</div>
                   ) : (
                     <div style={{ marginTop: "1rem" }}>
                       <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1rem", backgroundColor: "rgba(16, 185, 129, 0.1)", border: "1px solid rgba(16, 185, 129, 0.2)", padding: "1rem", borderRadius: "8px" }}>
                          <span style={{ fontSize: "0.9rem", color: "#9CA3AF" }}>AI Recommended Match:</span>
                          <span style={{ fontWeight: "800", color: "#34D399", fontSize: "1.1rem" }}>{g.data.recommended_supplier}</span>
                          <span style={{ fontSize: "0.9rem", color: "#D1D5DB", marginLeft: "auto", fontStyle: "italic" }}>"{g.data.reason}"</span>
                       </div>

                       <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem" }}>
                          {g.data.insights.map((ins, iIdx) => (
                            <div key={iIdx} style={{ backgroundColor: "rgba(255,255,255,0.02)", padding: "1rem", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.05)" }}>
                              <div style={{ fontWeight: "bold", color: "#F3F4F6", fontSize: "0.95rem", marginBottom: "0.5rem" }}>{ins.supplier_name}</div>
                              <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem", fontSize: "0.85rem", color: "#9CA3AF" }}>
                                <span style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}><DollarSign size={14} color="#60A5FA"/> ${ins.price && typeof ins.price === 'number' ? ins.price.toFixed(2) : ins.price} per unit</span>
                                <span style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}><Clock size={14} color="#FBBF24"/> {ins.lead_time_days} days lead</span>
                              </div>
                            </div>
                          ))}
                       </div>
                     </div>
                   )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
