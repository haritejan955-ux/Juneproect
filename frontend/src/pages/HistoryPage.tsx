import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listReports } from "../lib/api";
import { SeverityBadge } from "../components/SeverityBadge";
import type { ReportSummary } from "../lib/types";

export function HistoryPage() {
  const [reports, setReports] = useState<ReportSummary[]>([]);

  useEffect(() => {
    listReports().then(setReports);
  }, []);

  return (
    <div className="mx-auto max-w-2xl p-6">
      <h1 className="mb-6 text-2xl font-semibold">Report History</h1>
      {reports.length === 0 ? (
        <p className="text-sm text-gray-500">No reports yet.</p>
      ) : (
        <ul className="space-y-3">
          {reports.map((report) => (
            <li key={report.id}>
              <Link
                to={`/report/${report.id}`}
                className="flex items-center justify-between rounded-md border border-gray-200 p-4 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-900"
              >
                <div>
                  <p className="text-sm font-medium">{report.id}</p>
                  <p className="text-xs text-gray-500">{new Date(report.created_at).toLocaleString()}</p>
                </div>
                <div className="flex items-center gap-2">
                  {report.pharmacist_review_flag && (
                    <span className="text-xs font-medium text-amber-700">Needs review</span>
                  )}
                  {report.overall_severity && <SeverityBadge severity={report.overall_severity} />}
                  {!report.overall_severity && (
                    <span className="text-xs text-gray-400">{report.status}</span>
                  )}
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
