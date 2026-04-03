import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";
import { useState, useEffect, createContext } from "react";
import { getSession, onAuthStateChange } from "./services/auth";

import AuthPage from "./pages/AuthPage";
import SetupPage from "./pages/SetupPage";
import InventoryDash from "./pages/InventoryDash";
import BomAnalysis from "./pages/BomAnalysis";
import SupplierIntelligence from "./pages/SupplierIntelligence";
import SupplierRisk from "./pages/SupplierRisk";
import InventoryRisk from "./pages/InventoryRisk";
import ShippingDashboard from "./pages/ShippingDashboard";
import Sidebar from "./components/Sidebar";

export const AuthContext = createContext(null);

/* ── Auth guard ───────────────────────────────────────────────── */

function ProtectedRoute({ session, ready }) {
  if (!ready) {
    return (
      <div className="auth-loading">
        <span className="spinner spinner--lg" />
      </div>
    );
  }
  return session ? <Outlet /> : <Navigate to="/" replace />;
}

/* ── Layout with sidebar ──────────────────────────────────────── */

function DashboardLayout() {
  return (
    <div className="dashboard-layout">
      <Sidebar />
      <main className="dashboard-layout__main">
        <Outlet />
      </main>
    </div>
  );
}

/* ── App ──────────────────────────────────────────────────────── */

export default function App() {
  const [session, setSession] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    getSession().then((s) => {
      setSession(s);
      setReady(true);
    });

    const sub = onAuthStateChange((s) => setSession(s));
    return () => sub.unsubscribe();
  }, []);

  return (
    <AuthContext.Provider value={{ session }}>
      <BrowserRouter>
        <Routes>
          {/* Public */}
          <Route
            path="/"
            element={
              session ? (
                localStorage.getItem("needsSetup") === "true"
                  ? <Navigate to="/setup" replace />
                  : <Navigate to="/dashboard" replace />
              ) : (
                <AuthPage />
              )
            }
          />

          {/* Protected — no sidebar (setup flow) */}
          <Route element={<ProtectedRoute session={session} ready={ready} />}>
            <Route path="/setup" element={<SetupPage />} />
          </Route>

          {/* Protected — with sidebar */}
          <Route element={<ProtectedRoute session={session} ready={ready} />}>
            <Route element={<DashboardLayout />}>
              <Route path="/dashboard" element={<InventoryDash />} />
              <Route path="/bom-analysis" element={<BomAnalysis />} />
              <Route path="/supplier-intelligence" element={<SupplierIntelligence />} />
              <Route path="/supplier-risk" element={<SupplierRisk />} />
              <Route path="/inventory-risk" element={<InventoryRisk />} />
              <Route path="/shipping" element={<ShippingDashboard />} />
            </Route>
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthContext.Provider>
  );
}
