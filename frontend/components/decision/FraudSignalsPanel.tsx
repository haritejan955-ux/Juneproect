import { Badge } from "@/components/ui/Badge";
import type { FraudSignal } from "@/lib/types";

const SEVERITY_VARIANT: Record<FraudSignal["severity"], "green" | "amber" | "red"> = {
  low: "green",
  medium: "amber",
  high: "red",
};

export function FraudSignalsPanel({ signals }: { signals: FraudSignal[] }) {
  if (signals.length === 0) {
    return <p className="text-sm text-slate-500">No fraud signals were detected.</p>;
  }

  return (
    <ul className="space-y-3">
      {signals.map((signal, index) => (
        <li key={index} className="rounded-md border border-slate-200 p-3">
          <div className="mb-1 flex items-center justify-between">
            <span className="font-medium text-slate-800">
              {signal.signal_type.replace(/_/g, " ")}
            </span>
            <Badge variant={SEVERITY_VARIANT[signal.severity]}>{signal.severity}</Badge>
          </div>
          <p className="text-sm text-slate-600">{signal.evidence}</p>
        </li>
      ))}
    </ul>
  );
}
