import { useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { AGENT_SEQUENCE, useReportProgress } from "../hooks/useReportProgress";

const AGENT_LABELS: Record<string, string> = {
  prescription_parser: "Parsing prescription",
  drug_normalizer: "Normalizing drug names",
  patient_profile_loader: "Loading patient profile",
  interaction_retriever: "Checking drug interactions",
  allergy_checker: "Checking allergies & contraindications",
  dosage_validator: "Validating dosages",
  risk_synthesizer: "Synthesizing safety report",
  self_critic: "Reviewing report for completeness",
  prepare_retry: "Revising synthesis",
  final_output: "Finalizing report",
};

export function ProcessingPage() {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();
  const { events, latestAgent, done } = useReportProgress(reportId ?? "");

  const completedAgents = new Set(events.filter((e) => e.type === "progress").map((e) => e.agent));

  useEffect(() => {
    if (done && reportId) {
      const timeout = setTimeout(() => navigate(`/report/${reportId}`), 500);
      return () => clearTimeout(timeout);
    }
  }, [done, reportId, navigate]);

  return (
    <div className="mx-auto max-w-xl p-6">
      <h1 className="mb-6 text-2xl font-semibold">Running safety check…</h1>
      <ol className="space-y-3">
        {AGENT_SEQUENCE.filter((agent) => agent !== "prepare_retry").map((agent) => {
          const isDone = completedAgents.has(agent);
          const isActive = latestAgent === agent && !done;
          return (
            <li key={agent} className="flex items-center gap-3">
              <span
                data-testid={`agent-status-${agent}`}
                data-status={isDone ? "done" : isActive ? "active" : "pending"}
                className={`h-3 w-3 rounded-full ${
                  isDone ? "bg-green-500" : isActive ? "animate-pulse bg-blue-500" : "bg-gray-300"
                }`}
              />
              <span className={isDone || isActive ? "text-gray-900 dark:text-gray-100" : "text-gray-400"}>
                {AGENT_LABELS[agent]}
              </span>
            </li>
          );
        })}
      </ol>
      {done && <p className="mt-6 text-sm text-gray-500">Redirecting to the report…</p>}
    </div>
  );
}
