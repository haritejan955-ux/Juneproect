"use client";

import { AlertCircle, RotateCcw } from "lucide-react";

import { ClaimNav } from "@/components/layout/claim-nav";
import { AuditTimeline } from "@/components/audit/audit-timeline";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuditTrail } from "@/hooks/useAuditTrail";

interface AuditPageProps {
  params: { claimId: string };
}

export default function AuditPage({ params }: AuditPageProps) {
  const { claimId } = params;
  const { data: trail, isLoading, isError, error, refetch, isFetching } = useAuditTrail(claimId);

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <ClaimNav claimId={claimId} active="audit" />

      <Card className="animate-in fade-in slide-in-from-bottom-2 duration-500">
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <CardTitle>Audit trail</CardTitle>
          <Button variant="ghost" size="sm" onClick={() => refetch()} disabled={isFetching}>
            <RotateCcw className={isFetching ? "size-3.5 animate-spin" : "size-3.5"} />
            Refresh
          </Button>
        </CardHeader>
        <CardContent>
          {isLoading && (
            <div className="space-y-4">
              {[0, 1, 2].map((i) => (
                <div key={i} className="flex gap-3">
                  <Skeleton className="size-8 shrink-0 rounded-full" />
                  <div className="flex-1 space-y-1.5 pt-1">
                    <Skeleton className="h-3.5 w-1/2" />
                    <Skeleton className="h-3 w-1/3" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {isError && (
            <Alert variant="destructive">
              <AlertCircle className="size-4" />
              <AlertTitle>Couldn&apos;t load the audit trail</AlertTitle>
              <AlertDescription>
                {error instanceof Error ? error.message : "Please try again."}
              </AlertDescription>
            </Alert>
          )}

          {trail && <AuditTimeline entries={trail.entries} />}
        </CardContent>
      </Card>
    </div>
  );
}
