import type { Metadata } from "next";
import "./globals.css";
import SideNavBar from "@/components/layout/SideNavBar";
import TopAppBar from "@/components/layout/TopAppBar";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "SentinelML - Enterprise ML Observability & Control Center",
  description: "Enterprise portfolio-grade ML Reliability, Drift Detection, & Self-Healing Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background text-on-surface antialiased flex h-screen overflow-hidden">
        <Providers>
          {/* Fixed Navigation Sidebar (240px wide) */}
          <SideNavBar />

          {/* Fixed Top App Header (64px high) */}
          <TopAppBar />

          {/* Content Viewport Container */}
          <div className="pl-[240px] pt-[64px] w-full h-screen overflow-hidden flex flex-col">
            {children}
          </div>
        </Providers>
      </body>
    </html>
  );
}



