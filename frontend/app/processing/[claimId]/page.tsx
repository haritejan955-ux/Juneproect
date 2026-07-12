"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Radio } from "lucide-react";

import { AgentTimeline, computeProgress } from "@/components/processing/agent-timeline";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useClaimStatus } from "@/hooks/useClaimStatus";
import { useClaimStream } from "@/hooks/useClaimStream";

interface ProcessingPageProps {
  params: { claimId: string };
}

export default function ProcessingPage({ params }: ProcessingPageProps) {
  const { claimId } = params;
  const router = useRouter();
  const { events, connected } = useClaimStream(claimId);

  const finished = events.some(
    (event) => event.agent === "final_output" || event.agent === "blocked",
  );
  const { data: status } = useClaimStatus(claimId, { enabled: finished });

  useEffect(() => {
    if (status?.status === "completed" || status?.status === "blocked") {
      router.push(`/decision/${claimId}`);
    }
  }, [status, claimId, router]);

  const progress = computeProgress(events);

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <Card className="animate-in fade-in slide-in-from-bottom-2 duration-500">
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle>Processing your claim</CardTitle>
            <CardDescription className="font-mono text-xs">{claimId}</CardDescription>
          </div>
          <Badge variant={connected ? "success" : "muted"} className="shrink-0">
            <Radio className={connected ? "size-3 animate-pulse" : "size-3"} />
            {connected ? "Live" : "Connecting…"}
          </Badge>
        </CardHeader>

        <CardContent className="space-y-6">
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>Overall progress</span>
              <span className="tabular-nums">{progress}%</span>
            </div>
            <Progress value={progress} />
          </div>

          {events.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">
              Waiting for the pipeline to start…
            </p>
          ) : (
            <AgentTimeline events={events} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
