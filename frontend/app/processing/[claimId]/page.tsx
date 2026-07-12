"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { AgentStatusLog } from "@/components/processing/AgentStatusLog";
import { Card } from "@/components/ui/Card";
import { useClaimStream } from "@/hooks/useClaimStream";
import { getClaimStatus } from "@/lib/api";

interface ProcessingPageProps {
  params: { claimId: string };
}

export default function ProcessingPage({ params }: ProcessingPageProps) {
  const { claimId } = params;
  const router = useRouter();
  const { events, connected } = useClaimStream(claimId);

  useEffect(() => {
    const finished = events.some(
      (event) => event.agent === "final_output" || event.agent === "blocked",
    );
    if (!finished) return;

    let cancelled = false;
    const timeout = setTimeout(async () => {
      const status = await getClaimStatus(claimId).catch(() => null);
      if (!cancelled && status && (status.status === "completed" || status.status === "blocked")) {
        router.push(`/decision/${claimId}`);
      }
    }, 500);

    return () => {
      cancelled = true;
      clearTimeout(timeout);
    };
  }, [events, claimId, router]);

  return (
    <Card title={`Processing claim ${claimId}`}>
      <AgentStatusLog events={events} connected={connected} />
    </Card>
  );
}
