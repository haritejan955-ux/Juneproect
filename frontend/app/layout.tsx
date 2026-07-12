import type { Metadata } from "next";
import { Inter } from "next/font/google";

import { SiteHeader } from "@/components/layout/site-header";
import { Providers } from "./providers";

import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "US Insurance Claim Processing Agent",
  description: "Multi-agent LangGraph pipeline for US insurance claim processing",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} min-h-screen bg-background font-sans antialiased`}>
        <Providers>
          <div className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(circle_at_20%_-10%,hsl(var(--primary)/0.12),transparent_45%),radial-gradient(circle_at_85%_10%,hsl(var(--primary)/0.08),transparent_40%)]" />
          <SiteHeader />
          <main className="container py-8 sm:py-10">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
