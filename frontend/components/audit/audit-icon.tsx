import {
  BadgeCheck,
  Ban,
  FileSearch,
  Gavel,
  Library,
  ListChecks,
  type LucideIcon,
  MessageSquareQuote,
  MessagesSquare,
  RotateCcw,
  ScanSearch,
  ShieldAlert,
  Sparkles,
} from "lucide-react";

const AGENT_ICON: Record<string, LucideIcon> = {
  document_preprocessor: FileSearch,
  intent_analyzer: ScanSearch,
  rag_retriever: Library,
  security_checker: ShieldAlert,
  coverage_validator: ListChecks,
  fraud_detector: BadgeCheck,
  answer_synthesizer: MessageSquareQuote,
  self_critic: Sparkles,
  final_output: Gavel,
  blocked: Ban,
  prepare_retry: RotateCcw,
  dispute_responder: MessagesSquare,
};

export function AuditIcon({ agent, className }: { agent: string; className?: string }) {
  const Icon = AGENT_ICON[agent] ?? Sparkles;
  return <Icon className={className} />;
}

export function agentLabel(agent: string): string {
  return agent
    .split("_")
    .map((word) => word[0]?.toUpperCase() + word.slice(1))
    .join(" ");
}
