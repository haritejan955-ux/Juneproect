"use client";

import { useMemo } from "react";
import {
  BadgeCheck,
  Ban,
  CheckCircle2,
  FileSearch,
  Gavel,
  Library,
  ListChecks,
  MessageSquareQuote,
  RotateCcw,
  ScanSearch,
  ShieldAlert,
  Sparkles,
} from "lucide-react";

import { cn } from "@/lib/utils";
import type { AgentStreamEvent } from "@/lib/types";

const PIPELINE_STEPS = [
  { agent: "document_preprocessor", label: "Document Preprocessor", icon: FileSearch },
  { agent: "intent_analyzer", label: "Intent Analyzer", icon: ScanSearch },
  { agent: "rag_retriever", label: "RAG Retriever", icon: Library },
  { agent: "security_checker", label: "Security Checker", icon: ShieldAlert },
  { agent: "coverage_validator", label: "Coverage Validator", icon: ListChecks },
  { agent: "fraud_detector", label: "Fraud Detector", icon: BadgeCheck },
  { agent: "answer_synthesizer", label: "Answer Synthesizer", icon: MessageSquareQuote },
  { agent: "self_critic", label: "Self-Critic", icon: Sparkles },
  { agent: "final_output", label: "Final Output", icon: Gavel },
] as const;

export function computeProgress(events: AgentStreamEvent[]): number {
  if (events.some((event) => event.agent === "blocked")) return 100;
  const completed = new Set(events.map((event) => event.agent));
  const reached = PIPELINE_STEPS.filter((step) => completed.has(step.agent)).length;
  return Math.round((reached / PIPELINE_STEPS.length) * 100);
}

export function AgentTimeline({ events }: { events: AgentStreamEvent[] }) {
  const completedAgents = useMemo(() => new Set(events.map((event) => event.agent)), [events]);
  const isBlocked = completedAgents.has("blocked");
  const retryCount = events.filter((event) => event.agent === "prepare_retry").length;

  const firstPendingIndex = PIPELINE_STEPS.findIndex((step) => !completedAgents.has(step.agent));

  return (
    <ol className="space-y-1">
      {PIPELINE_STEPS.map((step, index) => {
        const isDone = completedAgents.has(step.agent);
        const isBlockedHere = isBlocked && step.agent === "security_checker";
        const isActive = !isDone && !isBlocked && index === firstPendingIndex;
        const isSkipped = isBlocked && !isDone && index > 3;

        const timestamp = events.find((event) => event.agent === step.agent)?.timestamp;

        return (
          <li
            key={step.agent}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2.5 transition-colors",
              isActive && "bg-accent",
            )}
          >
            <span
              className={cn(
                "relative flex size-8 shrink-0 items-center justify-center rounded-full border transition-colors",
                isDone && !isBlockedHere && "border-success bg-success/15 text-success",
                isBlockedHere && "border-destructive bg-destructive/15 text-destructive",
                isActive && "border-primary bg-primary/10 text-primary",
                isSkipped && "border-border bg-muted text-muted-foreground opacity-50",
                !isDone && !isActive && !isSkipped && "border-border text-muted-foreground",
              )}
            >
              {isActive && (
                <span className="absolute inset-0 rounded-full border border-primary animate-pulse-ring" />
              )}
              {isBlockedHere ? (
                <Ban className="size-4" />
              ) : isDone ? (
                <CheckCircle2 className="size-4" />
              ) : (
                <step.icon className="size-4" />
              )}
            </span>

            <div className="min-w-0 flex-1">
              <p
                className={cn(
                  "truncate text-sm font-medium",
                  isSkipped && "text-muted-foreground",
                )}
              >
                {step.label}
              </p>
              {isBlockedHere && (
                <p className="text-xs text-destructive">Blocked — prompt injection detected</p>
              )}
            </div>

            {timestamp && (
              <span className="shrink-0 text-xs tabular-nums text-muted-foreground">
                {new Date(timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
              </span>
            )}
          </li>
        );
      })}

      {retryCount > 0 && !isBlocked && (
        <li className="ml-11 flex items-center gap-1.5 text-xs text-muted-foreground">
          <RotateCcw className="size-3.5" />
          Self-Critic requested {retryCount} {retryCount === 1 ? "retry" : "retries"} of Answer
          Synthesizer
        </li>
      )}
    </ol>
  );
}
