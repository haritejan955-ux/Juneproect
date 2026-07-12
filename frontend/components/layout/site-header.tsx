import Link from "next/link";
import { ShieldCheck } from "lucide-react";

import { ThemeToggle } from "@/components/layout/theme-toggle";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur-md">
      <div className="container flex h-16 items-center justify-between">
        <Link href="/submit" className="flex items-center gap-2.5">
          <span className="flex size-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-indigo-400 text-primary-foreground shadow-sm">
            <ShieldCheck className="size-4" />
          </span>
          <span className="flex flex-col leading-none">
            <span className="text-sm font-semibold tracking-tight">Claim Processing Agent</span>
            <span className="text-[11px] text-muted-foreground">
              Multi-agent LangGraph pipeline
            </span>
          </span>
        </Link>
        <ThemeToggle />
      </div>
    </header>
  );
}
