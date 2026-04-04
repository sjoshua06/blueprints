import { useEffect, useState } from "react";
import {
  getDashboardSummary,
  getDashboardComponents,
  getDashboardSuppliers,
  getDashboardInventory,
} from "../services/api";
import ResultsTable from "../components/ResultsTable";
import RiskBadge from "../components/RiskBadge";
import { Cpu, Factory, Package, Link } from "lucide-react";

export default function InventoryDash() {
  const [summary, setSummary] = useState(() => {
    const saved = sessionStorage.getItem("dash_summary");
    return saved ? JSON.parse(saved) : null;
  });
  const [components, setComponents] = useState(() => {
    const saved = sessionStorage.getItem("dash_components");
    return saved ? JSON.parse(saved) : [];
  });
  const [suppliers, setSuppliers] = useState(() => {
    const saved = sessionStorage.getItem("dash_suppliers");
    return saved ? JSON.parse(saved) : [];
  });
  const [inventory, setInventory] = useState(() => {
    const saved = sessionStorage.getItem("dash_inventory");
    return saved ? JSON.parse(saved) : [];
  });
  const [activeTab, setActiveTab] = useState(() => {
    return sessionStorage.getItem("dash_activeTab") || "components";
  });
  const [loading, setLoading] = useState(!sessionStorage.getItem("dash_summary"));
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const [sum, comp, sup, inv] = await Promise.all([
          getDashboardSummary(),
          getDashboardComponents(),
          getDashboardSuppliers(),
          getDashboardInventory(),
        ]);
        setSummary(sum);
        setComponents(comp);
        setSuppliers(sup);
        setInventory(inv);
        sessionStorage.setItem("dash_summary", JSON.stringify(sum));
        sessionStorage.setItem("dash_components", JSON.stringify(comp));
        sessionStorage.setItem("dash_suppliers", JSON.stringify(sup));
        sessionStorage.setItem("dash_inventory", JSON.stringify(inv));
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    
    if (!summary) {
      load();
    } else {
      setLoading(false);
    }
  }, []);

  if (loading) {
    return (
      <div className="dash-loading">
        <span className="spinner spinner--lg" />
        <p>Loading dashboard…</p>
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

  /* ── Column definitions ────────────────────────────────────── */

  const componentCols = [
    { key: "component_id", label: "#" },
    { key: "component_name", label: "Name" },
    { key: "component_type", label: "Type" },
    { key: "category", label: "Category" },
    { key: "subcategory", label: "Sub-category" },
    { key: "manufacturer", label: "Manufacturer" },
    { key: "part_number", label: "Part No." },
    { key: "lifecycle_status", label: "Status" },
  ];

  const supplierCols = [
    { key: "supplier_id", label: "#" },
    { key: "supplier_name", label: "Supplier" },
    { key: "country", label: "Country" },
    { key: "reliability_score", label: "Reliability" },
    {
      key: "risk_score",
      label: "Risk",
      render: (val) =>
        val != null ? <RiskBadge score={Number(val)} /> : "—",
    },
    { key: "on_time_delivery_rate", label: "On-Time %" },
    { key: "defect_rate", label: "Defect %" },
    { key: "avg_lead_time_days", label: "Lead Time (d)" },
  ];

  const inventoryCols = [
    { key: "inventory_id", label: "#" },
    { key: "component_id", label: "Component" },
    { key: "stock_quantity", label: "Stock Qty" },
    { key: "unit_of_measure", label: "UoM" },
    { key: "warehouse_location", label: "Warehouse" },
    { key: "reorder_level", label: "Reorder Lvl" },
    { key: "safety_stock", label: "Safety Stock" },
  ];

  const TABS = [
    { key: "components", label: "Components", count: summary?.component_count },
    { key: "suppliers", label: "Suppliers", count: summary?.supplier_count },
    { key: "inventory", label: "Inventory", count: summary?.inventory_count },
  ];

  return (
    <div className="inventory-dash">
      <div className="inventory-dash__header">
        <h1>Inventory Dashboard</h1>
        <p className="inventory-dash__subtitle">
          Overview of your uploaded supply chain data
        </p>
      </div>

      {/* Summary cards */}
      <div className="summary-cards">
        <div className="summary-card">
          <span className="summary-card__icon"><Cpu size={24} color="#818cf8" /></span>
          <div>
            <p className="summary-card__value">
              {summary?.component_count ?? 0}
            </p>
            <p className="summary-card__label">Components</p>
          </div>
        </div>
        <div className="summary-card">
          <span className="summary-card__icon"><Factory size={24} color="#f87171" /></span>
          <div>
            <p className="summary-card__value">
              {summary?.supplier_count ?? 0}
            </p>
            <p className="summary-card__label">Suppliers</p>
          </div>
        </div>
        <div className="summary-card">
          <span className="summary-card__icon"><Package size={24} color="#34d399" /></span>
          <div>
            <p className="summary-card__value">
              {summary?.inventory_count ?? 0}
            </p>
            <p className="summary-card__label">Inventory Items</p>
          </div>
        </div>
        <div className="summary-card">
          <span className="summary-card__icon"><Link size={24} color="#fbbf24" /></span>
          <div>
            <p className="summary-card__value">
              {summary?.supplier_component_count ?? 0}
            </p>
            <p className="summary-card__label">Supplier Links</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="dash-tabs">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            className={`dash-tab ${
              activeTab === tab.key ? "dash-tab--active" : ""
            }`}
            onClick={() => {
              setActiveTab(tab.key);
              sessionStorage.setItem("dash_activeTab", tab.key);
            }}
          >
            {tab.label}
            {tab.count != null && (
              <span className="dash-tab__badge">{tab.count}</span>
            )}
          </button>
        ))}
      </div>

      {/* Table for active tab */}
      <div className="dash-table-container">
        {activeTab === "components" && (
          <ResultsTable
            columns={componentCols}
            data={components}
            emptyMessage="No components uploaded yet"
          />
        )}
        {activeTab === "suppliers" && (
          <ResultsTable
            columns={supplierCols}
            data={suppliers}
            emptyMessage="No suppliers uploaded yet"
          />
        )}
        {activeTab === "inventory" && (
          <ResultsTable
            columns={inventoryCols}
            data={inventory}
            emptyMessage="No inventory uploaded yet"
          />
        )}
      </div>
    </div>
  );
}
