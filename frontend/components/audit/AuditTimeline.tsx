import type { AuditLogEntry } from "@/lib/types";

export function AuditTimeline({ entries }: { entries: AuditLogEntry[] }) {
  if (entries.length === 0) {
    return <p className="text-sm text-slate-500">No audit entries recorded yet.</p>;
  }

  return (
    <ol className="space-y-4 border-l border-slate-200 pl-4">
      {entries.map((entry, index) => (
        <li key={index} className="relative">
          <span className="absolute -left-[21px] top-1 h-2 w-2 rounded-full bg-slate-400" />
          <p className="text-sm font-medium text-slate-800">
            {entry.agent} — {entry.action}
          </p>
          <p className="text-xs text-slate-400">{new Date(entry.timestamp).toLocaleString()}</p>
          {Object.keys(entry.details).length > 0 && (
            <pre className="mt-1 overflow-x-auto rounded bg-slate-50 p-2 text-xs text-slate-600">
              {JSON.stringify(entry.details, null, 2)}
            </pre>
          )}
        </li>
      ))}
    </ol>
  );
}
