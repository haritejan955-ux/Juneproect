import { AuditEntry } from "@/components/audit/audit-entry";
import type { AuditLogEntry } from "@/lib/types";

export function AuditTimeline({ entries }: { entries: AuditLogEntry[] }) {
  if (entries.length === 0) {
    return <p className="text-sm text-muted-foreground">No audit entries recorded yet.</p>;
  }

  return (
    <ol>
      {entries.map((entry, index) => (
        <AuditEntry key={index} entry={entry} isLast={index === entries.length - 1} />
      ))}
    </ol>
  );
}
