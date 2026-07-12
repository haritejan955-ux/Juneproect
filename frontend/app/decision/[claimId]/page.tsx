"use client";

import Link from "next/link";
import { AlertCircle, MessagesSquare, RotateCcw, ScrollText } from "lucide-react";

import { ClaimNav } from "@/components/layout/claim-nav";
import { AttorneyFlagBanner } from "@/components/decision/attorney-flag-banner";
import { CitationList } from "@/components/decision/citation-list";
import { ConfidenceMeter } from "@/components/decision/confidence-meter";
import { CoverageTable } from "@/components/decision/coverage-table";
import { DecisionBadge } from "@/components/decision/decision-badge";
import { DecisionSkeleton } from "@/components/decision/decision-skeleton";
import { FraudSignalsPanel } from "@/components/decision/fraud-signals-panel";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useDecision } from "@/hooks/useDecision";

interface DecisionPageProps {
  params: { claimId: string };
}

export default function DecisionPage({ params }: DecisionPageProps) {
  const { claimId } = params;
  const { data: decision, isLoading, isError, error, refetch } = useDecision(claimId);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <ClaimNav claimId={claimId} active="decision" />

      {isLoading && <DecisionSkeleton />}

      {isError && (
        <Alert variant="destructive">
          <AlertCircle className="size-4" />
          <AlertTitle>Couldn&apos;t load this decision</AlertTitle>
          <AlertDescription className="flex flex-col gap-3">
            <span>
              {error instanceof Error ? error.message : "The decision may not be ready yet."}
            </span>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={() => refetch()}>
                <RotateCcw className="size-3.5" /> Retry
              </Button>
              <Button size="sm" variant="ghost" asChild>
                <Link href={`/processing/${claimId}`}>Back to processing</Link>
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {decision && (
        <div className="animate-in fade-in slide-in-from-bottom-2 space-y-6 duration-500">
          <AttorneyFlagBanner show={decision.attorney_flag} />

          <Card>
            <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-4 space-y-0">
              <div className="flex items-center gap-3">
                <DecisionBadge status={decision.status} />
                <span className="font-mono text-xs text-muted-foreground">{claimId}</span>
              </div>
              <ConfidenceMeter
                score={decision.confidence_score}
                lowConfidence={decision.low_confidence}
              />
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed text-foreground/90">
                {decision.justification}
              </p>
              {decision.retry_count > 0 && (
                <p className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
                  <RotateCcw className="size-3" />
                  Self-Critic requested {decision.retry_count}{" "}
                  {decision.retry_count === 1 ? "retry" : "retries"} before finalizing.
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Coverage</CardTitle>
            </CardHeader>
            <CardContent>
              <CoverageTable items={decision.coverage_map} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Fraud signals</CardTitle>
            </CardHeader>
            <CardContent>
              <FraudSignalsPanel signals={decision.fraud_signals} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Citations</CardTitle>
            </CardHeader>
            <CardContent>
              <CitationList citations={decision.citations} />
            </CardContent>
          </Card>

          <p className="text-center text-xs text-muted-foreground">{decision.disclaimer}</p>

          <Separator />

          <div className="flex flex-wrap justify-center gap-3">
            <Button asChild>
              <Link href={`/dispute/${claimId}`}>
                <MessagesSquare className="size-4" /> Dispute this decision
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href={`/audit/${claimId}`}>
                <ScrollText className="size-4" /> View audit trail
              </Link>
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
