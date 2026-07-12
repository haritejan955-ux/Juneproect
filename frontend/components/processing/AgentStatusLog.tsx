import type { AgentStreamEvent } from "@/lib/types";

const AGENT_LABELS: Record<string, string> = {
  document_preprocessor: "Document Preprocessor",
  intent_analyzer: "Intent Analyzer",
  rag_retriever: "RAG Retriever",
  security_checker: "Security Checker",
  coverage_validator: "Coverage Validator",
  fraud_detector: "Fraud Detector",
  answer_synthesizer: "Answer Synthesizer",
  self_critic: "Self-Critic",
  final_output: "Final Output",
  blocked: "Blocked (Security Checker)",
  prepare_retry: "Preparing retry",
};

interface AgentStatusLogProps {
  events: AgentStreamEvent[];
  connected: boolean;
}

export function AgentStatusLog({ events, connected }: AgentStatusLogProps) {
  return (
    <div>
      <p className="mb-3 text-sm text-slate-500">
        {connected ? "Connected — live agent status" : "Connecting…"}
      </p>
      <ol className="space-y-2">
        {events.map((event, index) => (
          <li key={`${event.agent}-${index}`} className="flex items-center gap-3 text-sm">
            <span className="h-2 w-2 rounded-full bg-green-500" />
            <span className="font-medium text-slate-800">
              {AGENT_LABELS[event.agent] ?? event.agent}
            </span>
            <span className="text-slate-400">
              {new Date(event.timestamp).toLocaleTimeString()}
            </span>
          </li>
        ))}
        {events.length === 0 && (
          <li className="text-sm text-slate-400">Waiting for pipeline to start…</li>
        )}
      </ol>
    </div>
  );
}
