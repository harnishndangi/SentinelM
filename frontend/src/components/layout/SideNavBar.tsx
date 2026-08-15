'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';

import {
  LayoutDashboard,
  Cpu,
  Activity,
  GitCommit,
  AlertTriangle,
  RotateCcw,
  Rocket,
  FlaskConical,
  Database,
  Bell,
  FileText,
  Settings,
  Shield,
  PlayCircle,
  GitBranch,
  LogOut,
} from 'lucide-react';

const NAV_ITEMS = [
  { label: 'Overview', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Models', href: '/models', icon: Cpu },
  { label: 'Monitoring', href: '/monitoring', icon: Activity },
  { label: 'Drift', href: '/drift', icon: GitCommit },
  { label: 'Incidents', href: '/incidents', icon: AlertTriangle },
  { label: 'Retraining', href: '/retraining', icon: RotateCcw },
  { label: 'Deployments', href: '/deployments', icon: Rocket },
  { label: 'Experiments', href: '/experiments', icon: FlaskConical },
  { label: 'Data', href: '/data', icon: Database },
  { label: 'Alerts', href: '/alerts', icon: Bell },
  { label: 'Audit Logs', href: '/audit-logs', icon: FileText },
  { label: 'Settings', href: '/settings', icon: Settings },
];

export default function SideNavBar() {
  const pathname = usePathname();
  const [environment, setEnvironment] = useState<'PRODUCTION' | 'STAGING'>('PRODUCTION');

  const toggleEnv = () => {
    setEnvironment((prev) => (prev === 'PRODUCTION' ? 'STAGING' : 'PRODUCTION'));
  };

  return (
    <nav className="fixed left-0 top-0 h-screen w-[240px] border-r border-[#252E3B] bg-[#101417] flex flex-col overflow-y-auto px-4 py-5 z-50 transition-all font-sans">
      {/* Brand Header */}
      <div className="mb-5 flex items-center gap-3 px-1">
        <Shield className="w-7 h-7 text-[#d0bcff]" />
        <div>
          <h1 className="text-lg font-bold text-white tracking-tight font-sans">SentinelML</h1>
          <p className="text-[11px] font-mono text-[#94a3b8]">Reliability Control</p>
        </div>
      </div>

      {/* Environment Button */}
      <button
        onClick={toggleEnv}
        title="Click to toggle Staging / Production"
        className={`w-full font-mono text-xs font-bold py-2.5 px-3 rounded mb-5 flex items-center justify-center gap-2 tracking-wider transition-all uppercase shadow-sm ${
          environment === 'PRODUCTION'
            ? 'bg-[#d0bcff] text-[#340080] hover:bg-[#c4b5fd]'
            : 'bg-[#ffb869] text-[#482900] hover:bg-[#ffa742]'
        }`}
      >
        <span>{environment}</span>
        {environment === 'PRODUCTION' ? (
          <PlayCircle className="w-4 h-4 text-[#340080] fill-[#340080]/20" />
        ) : (
          <GitBranch className="w-4 h-4 text-[#482900]" />
        )}
      </button>

      {/* Links List */}
      <ul className="flex-1 space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || (item.href === '/' && pathname === '/dashboard');
          const ItemIcon = item.icon;
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors duration-150 ${
                  isActive
                    ? 'text-[#d0bcff] font-semibold bg-[#101417] border border-[#252E3B]'
                    : 'text-[#e0e3e7] font-medium hover:bg-[#181c20] hover:text-white'
                }`}
              >
                <ItemIcon className={`w-4 h-4 ${isActive ? 'text-[#d0bcff]' : 'text-[#94a3b8]'}`} />
                <span className="text-sm font-sans tracking-tight">{item.label}</span>
              </Link>
            </li>
          );
        })}
      </ul>

      {/* Footer / Logout */}
      <div className="mt-auto border-t border-[#252E3B] pt-4">
        <button
          onClick={() => alert('Logged out successfully.')}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-md text-[#e0e3e7] font-medium hover:bg-[#181c20] hover:text-white transition-colors"
        >
          <LogOut className="w-4 h-4 text-[#94a3b8]" />
          <span className="text-sm font-sans">Logout</span>
        </button>
      </div>
    </nav>
  );
}
