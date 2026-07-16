import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { getReport, getReportAudit } from "../lib/api";
import { FindingsList } from "../components/FindingsList";
import { SeverityBadge } from "../components/SeverityBadge";
import type { AuditEntry, SafetyReportResponse } from "../lib/types";

export function ReportPage() {
  const { reportId } = useParams<{ reportId: string }>();
  const [report, setReport] = useState<SafetyReportResponse | null>(null);
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  const [showAudit, setShowAudit] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!reportId) return;
    getReport(reportId)
      .then(setReport)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load report"));
  }, [reportId]);

  useEffect(() => {
    if (!reportId || !showAudit) return;
    getReportAudit(reportId).then(setAudit);
  }, [reportId, showAudit]);

  if (error) return <p className="p-6 text-red-600">{error}</p>;
  if (!report) return <p className="p-6 text-gray-500">Loading report…</p>;

  if (report.status === "blocked") {
    return (
      <div className="mx-auto max-w-2xl p-6">
        <h1 className="mb-4 text-2xl font-semibold text-red-700">Submission blocked</h1>
        <p className="text-sm text-gray-700">
          This submission was blocked by the security check and was not processed:{" "}
          {report.error ?? "a potential prompt-injection attempt was detected."}
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Medication Safety Report</h1>
        {report.overall_severity && <SeverityBadge severity={report.overall_severity} />}
      </div>

      {report.pharmacist_review_flag && (
        <div className="mb-6 rounded-md border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900 dark:bg-amber-950 dark:text-amber-100">
          <strong>Pharmacist review recommended.</strong> This report contains a major or
          contraindicated finding.
        </div>
      )}

      {report.summary && <p className="mb-6 text-gray-700 dark:text-gray-300">{report.summary}</p>}

      <section className="mb-8">
        <h2 className="mb-3 text-lg font-medium">Medications</h2>
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-gray-500 dark:border-gray-700">
              <th className="py-2">Drug</th>
              <th className="py-2">Class</th>
              <th className="py-2">Dose</th>
              <th className="py-2">Frequency</th>
            </tr>
          </thead>
          <tbody>
            {report.medications.map((med, index) => (
              <tr key={index} className="border-b border-gray-100 dark:border-gray-800">
                <td className="py-2">{med.normalized_name ?? med.raw_name}</td>
                <td className="py-2 text-gray-500">{med.drug_class ?? "unrecognized"}</td>
                <td className="py-2">
                  {med.dose_value ? `${med.dose_value}${med.dose_unit ?? ""}` : "—"}
                </td>
                <td className="py-2">{med.frequency ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="mb-8">
        <h2 className="mb-3 text-lg font-medium">Findings</h2>
        <FindingsList findings={report.findings} />
      </section>

      <section>
        <button
          className="text-sm font-medium text-blue-600 hover:underline"
          onClick={() => setShowAudit((prev) => !prev)}
        >
          {showAudit ? "Hide audit trail" : "Show audit trail"}
        </button>
        {showAudit && (
          <ul className="mt-3 space-y-2 text-xs text-gray-500">
            {audit.map((entry, index) => (
              <li key={index}>
                <span className="font-mono">{entry.timestamp}</span> — {entry.agent}: {entry.action}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
