import { AlertOctagon, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { FraudSignal } from "@/lib/types";

const SEVERITY_VARIANT: Record<FraudSignal["severity"], "success" | "warning" | "destructive"> = {
  low: "success",
  medium: "warning",
  high: "destructive",
};

const SIGNAL_LABEL: Record<FraudSignal["signal_type"], string> = {
  duplicate_billing: "Duplicate billing",
  upcoding: "Upcoding",
  date_conflict: "Date conflict",
  unbundling: "Unbundling",
};

export function FraudSignalsPanel({ signals }: { signals: FraudSignal[] }) {
  if (signals.length === 0) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <ShieldCheck className="size-4 text-success" />
        No fraud signals were detected.
      </div>
    );
  }

  return (
    <ul className="grid gap-3 sm:grid-cols-2">
      {signals.map((signal, index) => (
        <li
          key={index}
          className="rounded-lg border border-border bg-card p-3 shadow-sm transition-shadow hover:shadow-md"
        >
          <div className="mb-1.5 flex items-center justify-between gap-2">
            <span className="flex items-center gap-1.5 text-sm font-medium">
              <AlertOctagon className="size-3.5 text-muted-foreground" />
              {SIGNAL_LABEL[signal.signal_type]}
            </span>
            <Badge variant={SEVERITY_VARIANT[signal.severity]}>{signal.severity}</Badge>
          </div>
          <p className="text-sm text-muted-foreground">{signal.evidence}</p>
        </li>
      ))}
    </ul>
  );
}
