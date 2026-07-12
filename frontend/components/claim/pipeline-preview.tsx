import {
  BadgeCheck,
  FileSearch,
  Gavel,
  Library,
  ListChecks,
  MessageSquareQuote,
  ScanSearch,
  ShieldAlert,
  Sparkles,
} from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

const STEPS = [
  { icon: FileSearch, label: "Document Preprocessor", detail: "Parses & flags PII" },
  { icon: ScanSearch, label: "Intent Analyzer", detail: "Classifies the query" },
  { icon: Library, label: "RAG Retriever", detail: "Hybrid dense + sparse search" },
  { icon: ShieldAlert, label: "Security Checker", detail: "Hybrid injection gate" },
  { icon: ListChecks, label: "Coverage Validator", detail: "Cites policy clauses" },
  { icon: BadgeCheck, label: "Fraud Detector", detail: "Scores 4 fraud signal types" },
  { icon: MessageSquareQuote, label: "Answer Synthesizer", detail: "Drafts the decision" },
  { icon: Sparkles, label: "Self-Critic", detail: "Scores & retries if needed" },
  { icon: Gavel, label: "Final Output", detail: "Persists the decision" },
] as const;

export function PipelinePreview() {
  return (
    <Card className="bg-gradient-to-b from-card to-muted/30">
      <CardHeader>
        <CardTitle className="text-base">What happens next</CardTitle>
        <CardDescription>
          Your claim runs through 9 agents in a LangGraph pipeline — you&apos;ll see each one
          complete live on the next screen.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ol className="relative space-y-4 border-l border-border pl-5">
          {STEPS.map(({ icon: Icon, label, detail }, index) => (
            <li key={label} className="relative">
              <span className="absolute -left-[27px] flex size-4 items-center justify-center rounded-full border border-border bg-background text-[9px] font-semibold text-muted-foreground">
                {index + 1}
              </span>
              <div className="flex items-start gap-2.5">
                <Icon className="mt-0.5 size-4 shrink-0 text-primary" />
                <div>
                  <p className="text-sm font-medium leading-tight">{label}</p>
                  <p className="text-xs text-muted-foreground">{detail}</p>
                </div>
              </div>
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  );
}
