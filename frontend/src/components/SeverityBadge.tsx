import type { Severity } from "../lib/types";

const LABELS: Record<Severity, string> = {
  none: "No concerns",
  minor: "Minor",
  moderate: "Moderate",
  major: "Major",
  contraindicated: "Contraindicated",
};

const CLASSES: Record<Severity, string> = {
  none: "bg-severity-none/10 text-severity-none border-severity-none",
  minor: "bg-severity-minor/10 text-severity-minor border-severity-minor",
  moderate: "bg-severity-moderate/10 text-severity-moderate border-severity-moderate",
  major: "bg-severity-major/10 text-severity-major border-severity-major",
  contraindicated: "bg-severity-contraindicated/10 text-severity-contraindicated border-severity-contraindicated",
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1 text-sm font-medium ${CLASSES[severity]}`}
    >
      {LABELS[severity]}
    </span>
  );
}
