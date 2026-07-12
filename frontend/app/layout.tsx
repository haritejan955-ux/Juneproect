import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "US Insurance Claim Processing Agent",
  description: "Multi-agent LangGraph pipeline for US insurance claim processing",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        <div className="mx-auto max-w-5xl px-4 py-8">
          <header className="mb-8">
            <h1 className="text-xl font-semibold text-slate-900">
              US Insurance Claim Processing Agent
            </h1>
          </header>
          <main>{children}</main>
        </div>
      </body>
    </html>
  );
}
