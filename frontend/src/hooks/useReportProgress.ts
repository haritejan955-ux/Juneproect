import { useEffect, useState } from "react";

import { reportProgressSocketUrl } from "../lib/api";
import type { ProgressEvent } from "../lib/types";

export const AGENT_SEQUENCE = [
  "prescription_parser",
  "drug_normalizer",
  "patient_profile_loader",
  "interaction_retriever",
  "allergy_checker",
  "dosage_validator",
  "risk_synthesizer",
  "self_critic",
  "prepare_retry",
  "final_output",
] as const;

interface ProgressState {
  events: ProgressEvent[];
  latestAgent: string | null;
  done: boolean;
  finalStatus: string | null;
}

export function useReportProgress(reportId: string): ProgressState {
  const [events, setEvents] = useState<ProgressEvent[]>([]);
  const [done, setDone] = useState(false);
  const [finalStatus, setFinalStatus] = useState<string | null>(null);

  useEffect(() => {
    const socket = new WebSocket(reportProgressSocketUrl(reportId));

    socket.onmessage = (event) => {
      const parsed = JSON.parse(event.data) as ProgressEvent;
      setEvents((prev) => [...prev, parsed]);
      if (parsed.type === "complete") {
        setDone(true);
        setFinalStatus(parsed.status ?? null);
      }
    };
    socket.onerror = () => {
      setDone(true);
    };

    return () => socket.close();
  }, [reportId]);

  const latestAgent = [...events].reverse().find((e) => e.type === "progress")?.agent ?? null;

  return { events, latestAgent, done, finalStatus };
}
