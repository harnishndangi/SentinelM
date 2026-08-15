'use client';

import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { Search, Bell, ChevronRight, User } from 'lucide-react';
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
    <header className="fixed top-0 right-0 h-[64px] left-[240px] z-40 border-b border-[#252E3B] bg-[#101417] flex items-center justify-between px-6 transition-all font-sans">
      {/* Breadcrumb Section */}
      <div className="flex items-center gap-4">
        <div className="text-[#94a3b8] font-mono text-xs flex items-center gap-2">
          <span>{breadcrumbs.parent}</span>
          <ChevronRight className="w-3.5 h-3.5 text-slate-500" />
          <span className="text-[#d0bcff] font-semibold">{breadcrumbs.current}</span>
        </div>
      </div>

      {/* Action Controls */}
      <div className="flex items-center gap-4">
        {/* Global Search Bar */}
        <div className="hidden md:flex items-center gap-2 bg-[#101417] px-3.5 py-1.5 rounded-lg border border-[#252E3B] focus-within:border-purple-500 transition-colors">
          <Search className="w-4 h-4 text-[#94a3b8]" />
          <input
            type="text"
            placeholder="Search resources, models, features..."
            className="bg-transparent border-none outline-none text-xs font-mono text-slate-200 placeholder-slate-500 w-48 focus:ring-0"
          />
        </div>

        {/* Notifications Icon & Popover */}
        <div className="relative">
          <button
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            className="text-[#94a3b8] hover:text-white transition-colors cursor-pointer relative p-1.5 rounded-lg hover:bg-[#181c20]"
            title="Notifications"
          >
            <Bell className="w-5 h-5" />
            {incidents.length > 0 && (
              <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-rose-400 animate-pulse" />
            )}
          </button>

          {notificationsOpen && (
            <div className="absolute right-0 top-11 w-80 bg-[#101417] border border-[#252E3B] rounded-lg shadow-xl z-50 p-4">
              <div className="flex justify-between items-center mb-3 pb-2 border-b border-[#252E3B]">
                <span className="font-mono text-xs font-bold text-white">Notifications</span>
                <span className="text-xs text-rose-400 font-mono">{incidents.length} Alert(s)</span>
              </div>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {incidents.map((inc) => (
                  <div key={inc.id} className="p-2.5 rounded-md bg-[#101417] border border-[#252E3B] text-xs font-mono">
                    <p className="text-slate-200 font-medium">{inc.title}</p>
                    <div className="flex justify-between items-center mt-1 text-[#94a3b8] text-[11px]">
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
        <div className="flex items-center gap-2 bg-[#101417] px-3 py-1.5 rounded-lg border border-[#252E3B]">
          <span className="w-2 h-2 rounded-full bg-[#4ade80] animate-pulse" />
          <span className="text-xs font-mono text-white font-semibold">Live System</span>
        </div>

        {/* User Account */}
        <button
          className="text-[#94a3b8] hover:text-white transition-colors cursor-pointer p-1"
          title="Account Profile"
          onClick={() => alert('SentinelML Admin User')}
        >
          <User className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
}
