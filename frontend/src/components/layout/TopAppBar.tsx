'use client';

import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { useSentinelStore } from '@/store/useSentinelStore';

export default function TopAppBar() {
  const pathname = usePathname();
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const incidents = useSentinelStore((state) => state.incidents);

  // Derive breadcrumbs based on pathname
  const getBreadcrumbs = () => {
    switch (pathname) {
      case '/models':
        return { parent: 'Models', current: 'Overview' };
      case '/drift':
        return { parent: 'Monitoring', current: 'Drift Monitoring' };
      case '/incidents':
        return { parent: 'Operations', current: 'Active Incidents' };
      case '/retraining':
        return { parent: 'Pipelines', current: 'Automated Retraining' };
      case '/deployments':
        return { parent: 'Release', current: 'Canary Deployments' };
      case '/alerts':
        return { parent: 'Notifications', current: 'Alert Rules' };
      case '/settings':
        return { parent: 'System', current: 'Platform Settings' };
      default:
        return { parent: 'Dashboard', current: 'Control Center' };
    }
  };

  const breadcrumbs = getBreadcrumbs();

  return (
    <header className="fixed top-0 right-0 h-[64px] left-[240px] z-40 border-b border-outline-variant bg-surface flex items-center justify-between px-lg transition-all">
      {/* Breadcrumb Section */}
      <div className="flex items-center gap-4">
        <div className="text-on-surface-variant font-mono-label text-mono-label flex items-center gap-2">
          <span>{breadcrumbs.parent}</span>
          <span className="material-symbols-outlined text-[16px]">chevron_right</span>
          <span className="text-primary font-bold">{breadcrumbs.current}</span>
        </div>
      </div>

      {/* Action Controls */}
      <div className="flex items-center gap-4">
        {/* Global Search Bar */}
        <div className="hidden md:flex items-center gap-sm bg-surface-container-high px-md py-1.5 rounded-full border border-outline-variant focus-within:border-primary transition-colors">
          <span className="material-symbols-outlined text-on-surface-variant text-sm">search</span>
          <input
            type="text"
            placeholder="Search resources, models, features..."
            className="bg-transparent border-none outline-none text-body-md font-body-md text-on-surface placeholder-on-surface-variant w-48 focus:ring-0"
          />
        </div>

        {/* Notifications Icon & Popover */}
        <div className="relative">
          <button
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            className="text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer relative p-1 rounded hover:bg-surface-container"
            title="Notifications"
          >
            <span className="material-symbols-outlined text-[24px]">notifications</span>
            {incidents.length > 0 && (
              <span className="absolute top-0 right-0 w-2 h-2 rounded-full bg-status-error-text animate-pulse"></span>
            )}
          </button>

          {notificationsOpen && (
            <div className="absolute right-0 top-10 w-80 bg-surface-container-high border border-outline-variant rounded-lg shadow-xl z-50 p-md">
              <div className="flex justify-between items-center mb-3 pb-2 border-b border-outline-variant">
                <span className="font-mono-label text-mono-label font-bold text-on-surface">Notifications</span>
                <span className="text-body-sm text-status-error-text font-mono-label">{incidents.length} Alert(s)</span>
              </div>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {incidents.map((inc) => (
                  <div key={inc.id} className="p-2 rounded bg-surface-container-low border border-outline-variant/40 text-body-sm">
                    <p className="text-on-surface font-medium">{inc.title}</p>
                    <div className="flex justify-between items-center mt-1 text-on-surface-variant text-[11px]">
                      <span>{inc.affectedModel}</span>
                      <span>{inc.createdAt}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Live Status Pill */}
        <div className="text-on-surface-variant hover:text-on-surface transition-colors flex items-center gap-2 bg-surface-container-high px-3 py-1.5 rounded-full card-border">
          <span className="w-2 h-2 rounded-full bg-[#4ade80] animate-pulse"></span>
          <span className="text-mono-label font-mono-label">Live</span>
        </div>

        {/* User Account */}
        <button
          className="text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
          title="Account Profile"
          onClick={() => alert('SentinelML Admin User')}
        >
          <span className="material-symbols-outlined text-[28px]">account_circle</span>
        </button>
      </div>
    </header>
  );
}
