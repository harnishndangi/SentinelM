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
  { label: 'Overview', href: '/', icon: LayoutDashboard },
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
    <nav className="fixed left-0 top-0 h-screen w-[240px] border-r border-outline-variant bg-surface flex flex-col overflow-y-auto px-md py-lg z-50 transition-all">
      {/* Brand Header */}
      <div className="mb-6 flex items-center gap-3">
        <span className="material-symbols-outlined text-primary text-[32px]">shield</span>
        <div>
          <h1 className="text-display-md font-display-md font-bold text-primary tracking-tight">SentinelML</h1>
          <p className="text-body-sm font-body-sm text-on-surface-variant">Reliability Control</p>
        </div>
      </div>

      {/* Environment Button */}
      <button
        onClick={toggleEnv}
        title="Click to toggle Staging / Production"
        className={`w-full font-mono-label text-mono-label py-2 rounded mb-6 flex items-center justify-center gap-2 transition-all ${
          environment === 'PRODUCTION'
            ? 'bg-primary text-on-primary hover:bg-primary-fixed-dim'
            : 'bg-tertiary-container text-on-tertiary-container hover:bg-tertiary'
        }`}
      >
        <span>{environment}</span>
        {environment === 'PRODUCTION' ? (
          <PlayCircle className="w-4 h-4" />
        ) : (
          <GitBranch className="w-4 h-4" />
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
                className={`flex items-center gap-3 px-3 py-2 rounded transition-colors duration-200 ease-in-out ${
                  isActive
                    ? 'text-primary font-bold bg-surface-container-high'
                    : 'text-on-surface-variant hover:bg-surface-container hover:text-on-surface'
                }`}
              >
                <ItemIcon className="w-5 h-5" />
                <span className="text-body-md font-body-md">{item.label}</span>
              </Link>
            </li>
          );
        })}
      </ul>


      {/* Footer / Logout */}
      <div className="mt-auto border-t border-outline-variant pt-4">
        <button
          onClick={() => alert('Logged out successfully.')}
          className="w-full flex items-center gap-3 px-3 py-2 rounded text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors duration-200 ease-in-out"
        >
          <LogOut className="w-5 h-5" />
          <span className="text-body-md font-body-md">Logout</span>
        </button>

      </div>
    </nav>
  );
}
