import { NavLink, useNavigate } from "react-router-dom";
import { signOut } from "../services/auth";
import { useState } from "react";
import {
  LayoutDashboard,
  Microscope,
  ShieldAlert,
  PackageOpen,
  Hexagon,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Mail,
  Ship,
  Globe
} from "lucide-react";

const NAV_ITEMS = [
  { to: "/dashboard", icon: <LayoutDashboard size={20} />, label: "Dashboard" },
  { to: "/bom-analysis", icon: <Microscope size={20} />, label: "BOM Analysis" },
  { to: "/supplier-risk", icon: <ShieldAlert size={20} />, label: "Supplier Risk" },
  { to: "/supplier-intelligence", icon: <Mail size={20} />, label: "Supplier Intel" },
  { to: "/inventory-risk", icon: <PackageOpen size={20} />, label: "Inventory Risk" },
  { to: "/shipping", icon: <Ship size={20} />, label: "Shipping Intelligence" },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);

  async function handleSignOut() {
    await signOut();
    navigate("/");
  }

  return (
    <aside className={`sidebar ${collapsed ? "sidebar--collapsed" : ""}`}>
      <div className="sidebar__header">
        <div className="sidebar__logo">
          {!collapsed && <span className="sidebar__brand">SupplyShield</span>}
          {collapsed && <span className="sidebar__brand-icon" style={{ display: 'flex' }}><Hexagon size={24} color="var(--accent-light)" /></span>}
        </div>
        <button
          className="sidebar__toggle"
          onClick={() => setCollapsed((c) => !c)}
          title={collapsed ? "Expand" : "Collapse"}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      <nav className="sidebar__nav">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `sidebar__link ${isActive ? "sidebar__link--active" : ""}`
            }
          >
            <span className="sidebar__icon" style={{ display: 'flex' }}>{item.icon}</span>
            {!collapsed && <span className="sidebar__label">{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar__footer">
        <button className="sidebar__signout" onClick={handleSignOut}>
          <span className="sidebar__icon" style={{ display: 'flex' }}><LogOut size={20} /></span>
          {!collapsed && <span className="sidebar__label">Sign Out</span>}
        </button>
      </div>
    </aside>
  );
}
