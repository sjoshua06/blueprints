'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';

const menuItems = [
  { href: '/dashboard', label: 'Dashboard', icon: '📊' },
  { href: '/internal-risk', label: 'Internal Risk', icon: '⚠️' },
  { href: '/compatibility', label: 'Compatibility', icon: '🔗' },
  { href: '/supplier-risk', label: 'Supplier Risk', icon: '📦' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside className={`bg-sidebar border-r border-sidebar-border transition-all ${
      collapsed ? 'w-20' : 'w-64'
    }`}>
      <div className="h-full flex flex-col">
        {/* Logo */}
        <div className="p-4 border-b border-sidebar-border flex items-center justify-between">
          {!collapsed && (
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <span className="text-primary-foreground font-bold">⚡</span>
              </div>
              <span className="font-bold text-sidebar-foreground">ChainAI</span>
            </Link>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-2 hover:bg-sidebar-accent rounded-lg text-sidebar-foreground"
          >
            {collapsed ? '→' : '←'}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-6 space-y-2">
          {menuItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                  isActive
                    ? 'bg-sidebar-primary text-sidebar-primary-foreground'
                    : 'text-sidebar-foreground hover:bg-sidebar-accent'
                }`}
                title={collapsed ? item.label : undefined}
              >
                <span className="text-lg flex-shrink-0">{item.icon}</span>
                {!collapsed && <span className="text-sm font-medium">{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-sidebar-border">
          <button className={`w-full flex items-center gap-3 px-4 py-2 rounded-lg text-sidebar-foreground hover:bg-sidebar-accent ${
            collapsed ? 'justify-center' : ''
          }`}>
            <span className="text-lg">👤</span>
            {!collapsed && <span className="text-sm font-medium">Profile</span>}
          </button>
        </div>
      </div>
    </aside>
  );
}
