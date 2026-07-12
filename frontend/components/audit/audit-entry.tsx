"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";

import { cn } from "@/lib/utils";
import { agentLabel, AuditIcon } from "@/components/audit/audit-icon";
import type { AuditLogEntry } from "@/lib/types";

export function AuditEntry({ entry, isLast }: { entry: AuditLogEntry; isLast: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const hasDetails = Object.keys(entry.details).length > 0;

  return (
    <li className="relative pl-9">
      {!isLast && <span className="absolute left-[15px] top-8 h-full w-px bg-border" />}
      <span className="absolute left-0 top-0.5 flex size-8 items-center justify-center rounded-full border border-border bg-card text-muted-foreground">
        <AuditIcon agent={entry.agent} className="size-4" />
      </span>

      <div className="pb-6">
        <button
          type="button"
          disabled={!hasDetails}
          onClick={() => setExpanded((prev) => !prev)}
          className={cn(
            "flex w-full items-start justify-between gap-2 rounded-md text-left",
            hasDetails && "cursor-pointer",
          )}
        >
          <div>
            <p className="text-sm font-medium">
              {agentLabel(entry.agent)}
              <span className="font-normal text-muted-foreground"> — {entry.action.replace(/_/g, " ")}</span>
            </p>
            <p className="text-xs text-muted-foreground">
              {new Date(entry.timestamp).toLocaleString()}
            </p>
          </div>
          {hasDetails && (
            <ChevronDown
              className={cn(
                "mt-1 size-3.5 shrink-0 text-muted-foreground transition-transform",
                expanded && "rotate-180",
              )}
            />
          )}
        </button>

        {hasDetails && expanded && (
          <pre className="animate-in fade-in slide-in-from-top-1 mt-2 overflow-x-auto rounded-md bg-muted px-3 py-2 text-xs text-muted-foreground duration-150">
            {JSON.stringify(entry.details, null, 2)}
          </pre>
        )}
      </div>
    </li>
  );
}
