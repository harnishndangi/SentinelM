import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SentinelML - Autonomous ML Reliability & Self-Healing Platform",
  description: "Enterprise portfolio-grade ML Reliability, Drift Detection, & Self-Healing System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased bg-[#090d16] text-gray-100 min-h-screen">
        {children}
      </body>
    </html>
  );
}
