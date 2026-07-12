"use client";

import { useEffect, useRef, useState } from "react";

import type { AgentStreamEvent } from "@/lib/types";
import { openClaimStream } from "@/lib/websocket";

export function useClaimStream(claimId: string) {
  const [events, setEvents] = useState<AgentStreamEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const socket = openClaimStream(claimId);
    socketRef.current = socket;

    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onmessage = (message: MessageEvent<string>) => {
      const event = JSON.parse(message.data) as AgentStreamEvent;
      setEvents((previous) => [...previous, event]);
    };

    return () => {
      socket.close();
    };
  }, [claimId]);

  return { events, connected };
}
