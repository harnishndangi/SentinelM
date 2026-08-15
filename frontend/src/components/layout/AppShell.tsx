'use client';

import { usePathname } from 'next/navigation';
import SideNavBar from '@/components/layout/SideNavBar';
import TopAppBar from '@/components/layout/TopAppBar';

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isLandingPage = pathname === '/';

  if (isLandingPage) {
    return (
      <div className="w-full min-h-screen bg-[#0B0E14] text-slate-100 overflow-y-auto">
        {children}
      </div>
    );
  }

  return (
    <>
      {/* Fixed Navigation Sidebar (240px wide) */}
      <SideNavBar />

      {/* Fixed Top App Header (64px high) */}
      <TopAppBar />

      {/* Content Viewport Container */}
      <div className="pl-[240px] pt-[64px] w-full h-screen overflow-hidden flex flex-col">
        {children}
      </div>
    </>
  );
}
