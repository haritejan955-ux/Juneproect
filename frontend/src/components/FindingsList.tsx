import type { Finding } from "../lib/types";
import { SeverityBadge } from "./SeverityBadge";

const CATEGORY_LABELS: Record<Finding["category"], string> = {
  interaction: "Drug interaction",
  allergy: "Allergy / contraindication",
  dosage: "Dosage",
};

export function FindingsList({ findings }: { findings: Finding[] }) {
  if (findings.length === 0) {
    return <p className="text-sm text-gray-500">No safety findings were identified.</p>;
  }

  return (
    <ul className="space-y-3">
      {findings.map((finding, index) => (
        <li key={index} className="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <div className="mb-2 flex items-center justify-between gap-2">
            <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">
              {CATEGORY_LABELS[finding.category]}
              {finding.drugs ? ` — ${finding.drugs.join(" + ")}` : finding.drug ? ` — ${finding.drug}` : ""}
            </span>
            <SeverityBadge severity={finding.severity} />
          </div>
          <p className="text-sm text-gray-800 dark:text-gray-200">{finding.description}</p>
          {finding.citation_title && (
            <p className="mt-2 text-xs text-gray-500">Source: {finding.citation_title}</p>
          )}
          {finding.recommended_max && (
            <p className="mt-1 text-xs text-gray-500">Recommended max: {finding.recommended_max}</p>
          )}
        </li>
      ))}
    </ul>
  );
}
