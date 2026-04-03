import { useState } from "react";
import FileUploader from "../components/FileUploader";
import { analyzeBom, sendSupplierMailRequest } from "../services/api";
import { PartyPopper, Mail } from "lucide-react";

export default function BomAnalysis() {
  const [bomFile, setBomFile] = useState(null);
  const [receiptFile, setReceiptFile] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | analyzing | done | error
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [mailStatus, setMailStatus] = useState({}); // { supplierName: "sending" | "sent" | "error" }

  async function handleMail(componentId, componentName, reqQty, supplierName, supplierEmail) {
    setMailStatus(prev => ({ ...prev, [supplierName]: "sending" }));
    try {
      await sendSupplierMailRequest({
        component_id: componentId,
        component_name: componentName,
        required_quantity: reqQty,
        supplier_name: supplierName,
        supplier_email: supplierEmail
      });
      
      setMailStatus(prev => ({ ...prev, [supplierName]: "sent" }));
    } catch (e) {
      setMailStatus(prev => ({ ...prev, [supplierName]: "error" }));
    }
  }

  const [globalInsights, setGlobalInsights] = useState(null);
  const [globalInsightsLoading, setGlobalInsightsLoading] = useState(false);

  async function handleExtractGlobalInsights() {
    if (!results || !results.analysis) return;
    setGlobalInsightsLoading(true);
    const aggregated = [];
    for (const item of results.analysis) {
      if (item.missing > 0) {
        try {
          const data = await getSupplierInsights(item.component_id, item.component);
          aggregated.push({ componentId: item.component_id, componentName: item.component, data });
        } catch (e) {
             console.error("Insight Error:", e);
        }
      }
    }
    setGlobalInsights(aggregated);
    setGlobalInsightsLoading(false);
  }

  async function handleAnalyze() {
    if (!bomFile || !receiptFile) return;
    setStatus("analyzing");
    setError(null);
    try {
      const resp = await analyzeBom(bomFile, receiptFile);
      setResults(resp);
      localStorage.setItem("globalSupplierState", JSON.stringify(resp.analysis || []));
      setStatus("done");
    } catch (err) {
      setError(err.message);
      setStatus("error");
    }
  }

  return (
    <div className="setup-page">
      <div className="setup-page__container">
        <div className="setup-page__header">
          <h1>BOM Analysis & Compatibility</h1>
          <p className="setup-page__subtitle">
            Upload your Bill of Materials and Supplier Receipts. The AI engine will cross-reference your inventory, find missing quantities, and instantly match vector-compatible alternatives.
          </p>
        </div>

        {/* Upload grid similar to SetupPage */}
        <div className="setup-page__grid" style={{ gridTemplateColumns: "1fr 1fr", marginBottom: "2rem" }}>
          
          <div className="setup-page__upload-card">
            <h3>1. Bill of Materials (BOM)</h3>
            <p className="setup-page__card-desc">Your expected master component requirements.</p>
            <FileUploader 
              label={bomFile ? `Selected: ${bomFile.name}` : "Upload BOM Excel"} 
              onUpload={setBomFile} 
              disabled={status === "analyzing"} 
            />
          </div>
          
          <div className="setup-page__upload-card">
            <h3>2. Supplier Receipts</h3>
            <p className="setup-page__card-desc">Your received parts from suppliers so far.</p>
            <FileUploader 
              label={receiptFile ? `Selected: ${receiptFile.name}` : "Upload Receipts Excel"} 
              onUpload={setReceiptFile} 
              disabled={status === "analyzing"} 
            />
          </div>

        </div>

        <div className="setup-page__actions">
          <button 
            className={`btn btn--primary btn--lg ${(!bomFile || !receiptFile) ? 'btn--disabled' : ''}`}
            onClick={handleAnalyze}
            disabled={status === "analyzing" || !bomFile || !receiptFile}
            style={{ width: "100%", maxWidth: "800px", margin: "0 auto", display: "block" }}
          >
            {status === "analyzing" ? (
              <><span className="spinner spinner--sm" style={{ marginRight: "10px" }} /> Analyzing Compatibility & Database...</>
            ) : "Run AI Component Analysis"}
          </button>
        </div>

        {status === "error" && error && (
          <div className="setup-page__error" style={{ marginTop: "1.5rem" }}>
            <strong>Analysis Failed: </strong> {error}
          </div>
        )}

        {status === "done" && results && (
          <div style={{ marginTop: "3rem" }}>
            <h2 style={{ fontSize: "1.5rem", fontWeight: "bold", borderBottom: "2px solid rgba(255,255,255,0.1)", paddingBottom: "0.5rem", marginBottom: "1.5rem" }}>
              Analysis Results
            </h2>
            
            <div style={{ marginBottom: "2rem", padding: "1rem", backgroundColor: "rgba(16, 185, 129, 0.1)", color: "#34D399", borderRadius: "6px", display: "flex", gap: "2rem" }}>
              <div><strong>BOM rows imported:</strong> {results.saved.bom_rows_saved}</div>
              <div><strong>Receipt rows imported:</strong> {results.saved.receipt_rows_saved}</div>
            </div>

            {!results.analysis || results.analysis.length === 0 ? (
              <div style={{ padding: "3rem", textAlign: "center", backgroundColor: "rgba(255,255,255,0.05)", borderRadius: "8px", color: "#9CA3AF" }}>
                <PartyPopper color="#34D399" size={24} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '8px' }} />
                No missing components found! Your registered receipts fulfill all BOM requirements perfectly.
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
                {results.analysis.map((item, idx) => (
                  <div key={idx} style={{ border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px", overflow: "hidden", backgroundColor: "rgba(0,0,0,0.2)" }}>
                    <div style={{ backgroundColor: "rgba(255,255,255,0.05)", padding: "1rem", borderBottom: "1px solid rgba(255,255,255,0.05)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div>
                        <span style={{ fontWeight: "bold", fontSize: "1.1rem" }}>{item.component}</span>
                        <span style={{ fontSize: "0.85rem", color: "#9CA3AF", marginLeft: "0.5rem" }}>(ID: {item.component_id})</span>
                      </div>
                      <div style={{ display: "flex", gap: "1rem", fontSize: "0.9rem" }}>
                        <span style={{ padding: "0.25rem 0.75rem", backgroundColor: "rgba(59, 130, 246, 0.2)", color: "#60A5FA", borderRadius: "999px" }}>Req: {item.required}</span>
                        <span style={{ padding: "0.25rem 0.75rem", backgroundColor: "rgba(16, 185, 129, 0.2)", color: "#34D399", borderRadius: "999px" }}>Rec: {item.received}</span>
                        <span style={{ padding: "0.25rem 0.75rem", backgroundColor: "rgba(239, 68, 68, 0.2)", color: "#F87171", borderRadius: "999px", fontWeight: "bold" }}>Missing: {item.missing}</span>
                      </div>
                    </div>
                    
                    <div style={{ padding: "1rem" }}>
                      <h4 style={{ fontWeight: "600", color: "#D1D5DB", marginBottom: "1rem", fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                        AI-Matched Compatible Alternatives
                      </h4>
                      
                      {!item.compatible_components || item.compatible_components.length === 0 ? (
                        <p style={{ color: "#9CA3AF", fontStyle: "italic", fontSize: "0.9rem", marginBottom: "1rem" }}>No vector-compatible alternative components found in the database.</p>
                      ) : (
                        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
                          {item.compatible_components.map((alt, altIdx) => (
                            <div key={altIdx} style={{ padding: "0.75rem 1rem", border: "1px solid rgba(255,255,255,0.05)", borderRadius: "6px", backgroundColor: "rgba(255,255,255,0.02)" }}>
                              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.5rem" }}>
                                <div style={{ fontWeight: "500", color: "#F3F4F6", fontSize: "1.05rem" }}>{alt.component_name}</div>
                                <div style={{ fontWeight: "bold", color: "#34D399", fontSize: "0.95rem" }}>
                                  {alt.compatibility_score ? parseFloat(alt.compatibility_score).toFixed(1) : 0}% Match
                                </div>
                              </div>
                              {alt.suppliers && Array.isArray(alt.suppliers) && alt.suppliers.length > 0 && (
                                <div style={{ fontSize: "0.85rem", color: "#9CA3AF", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                                  <div style={{color: "#D1D5DB", marginBottom: "0.2rem"}}>Suppliers:</div>
                                  {alt.suppliers.map((s, sIdx) => {
                                    const supplierEmail = s.contact_email || `sales@${s.supplier_name.toLowerCase().replace(/\s+/g,'')}.com`;
                                    return (
                                      <div key={sIdx} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", backgroundColor: "rgba(0,0,0,0.1)", padding: "0.5rem", borderRadius: "4px" }}>
                                        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                                          <span style={{ fontWeight: "500", color: "#E5E7EB" }}>{s.supplier_name}</span>
                                          <span style={{ color: "#9CA3AF" }}>${s.price.toFixed(2)} | {s.lead_time_days}d lead</span>
                                        </div>
                                        <button 
                                          onClick={() => handleMail(item.component_id, item.component, item.missing, s.supplier_name, supplierEmail)}
                                          disabled={mailStatus[s.supplier_name] === "sending" || mailStatus[s.supplier_name] === "sent"}
                                          style={{ 
                                            display: "flex", alignItems: "center", gap: "0.35rem", padding: "0.35rem 0.6rem", fontSize: "0.75rem", fontWeight: "600",
                                            backgroundColor: mailStatus[s.supplier_name] === "sent" ? "rgba(16, 185, 129, 0.15)" : "rgba(59, 130, 246, 0.15)", 
                                            color: mailStatus[s.supplier_name] === "sent" ? "#34D399" : "#60A5FA", 
                                            border: `1px solid ${mailStatus[s.supplier_name] === "sent" ? "rgba(16,185,129,0.3)" : "rgba(59,130,246,0.3)"}`, 
                                            borderRadius: "4px", cursor: "pointer", transition: "all 0.2s" 
                                          }}
                                        >
                                          <Mail size={14} /> 
                                          {mailStatus[s.supplier_name] === "sending" ? "Sending RFQ..." : mailStatus[s.supplier_name] === "sent" ? "RFQ Sent" : "Request Quote"}
                                        </button>
                                      </div>
                                    );
                                  })}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}

                    </div>
                  </div>
                ))}
              </div>
            )}
            
          </div>
        )}
      </div>
    </div>
  );
}
