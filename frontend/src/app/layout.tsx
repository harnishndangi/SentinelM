import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import AppShell from "@/components/layout/AppShell";

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
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}




