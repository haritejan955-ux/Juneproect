"use client";

import { useCallback, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { getDisputeThread, streamDisputeMessage } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";
import type { DisputeMessage, DisputeThread } from "@/lib/types";

export function useDisputeThread(claimId: string) {
  return useQuery({
    queryKey: queryKeys.disputeThread(claimId),
    queryFn: () => getDisputeThread(claimId),
  });
}

/**
 * Sends a dispute message and streams the assistant's reply token-by-token, writing directly
 * into the React Query cache for `disputeThread` as tokens arrive — the chat UI just renders
 * whatever's in the cache, so it doesn't need separate "streaming buffer" state of its own.
 */
export function useStreamDisputeMessage(claimId: string) {
  const queryClient = useQueryClient();
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const send = useCallback(
    async (message: string) => {
      setError(null);
      setIsStreaming(true);

      const claimantMessage: DisputeMessage = {
        id: `local-claimant-${Date.now()}`,
        role: "claimant",
        content: message,
        timestamp: new Date().toISOString(),
      };
      const streamingId = `local-assistant-${Date.now()}`;
      const assistantMessage: DisputeMessage = {
        id: streamingId,
        role: "assistant",
        content: "",
        timestamp: new Date().toISOString(),
      };

      queryClient.setQueryData<DisputeThread | undefined>(
        queryKeys.disputeThread(claimId),
        (previous) =>
          previous
            ? { ...previous, messages: [...previous.messages, claimantMessage, assistantMessage] }
            : {
                dispute_id: "pending",
                claim_id: claimId,
                status: "open",
                messages: [claimantMessage, assistantMessage],
              },
      );

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        for await (const event of streamDisputeMessage(claimId, message, controller.signal)) {
          if (event.event === "token") {
            queryClient.setQueryData<DisputeThread | undefined>(
              queryKeys.disputeThread(claimId),
              (previous) => {
                if (!previous) return previous;
                return {
                  ...previous,
                  messages: previous.messages.map((existing) =>
                    existing.id === streamingId
                      ? { ...existing, content: existing.content + event.data.content }
                      : existing,
                  ),
                };
              },
            );
          } else if (event.event === "done") {
            queryClient.setQueryData<DisputeThread | undefined>(
              queryKeys.disputeThread(claimId),
              (previous) => {
                if (!previous) return previous;
                return {
                  ...previous,
                  messages: previous.messages.map((existing) =>
                    existing.id === streamingId
                      ? { ...existing, id: event.data.id, timestamp: event.data.timestamp }
                      : existing,
                  ),
                };
              },
            );
          }
        }
      } catch (err) {
        if (!(err instanceof DOMException && err.name === "AbortError")) {
          setError(err instanceof Error ? err.message : "Failed to send message.");
          // Neither optimistic message was actually persisted server-side if the stream
          // failed before its first event (e.g. no finalized decision yet) — leaving them
          // in the cache would strand the assistant bubble on its typing indicator forever,
          // since the invalidation below will itself fail to fetch a thread that was never
          // created. Roll both back so the thread reflects reality.
          queryClient.setQueryData<DisputeThread | undefined>(
            queryKeys.disputeThread(claimId),
            (previous) =>
              previous
                ? {
                    ...previous,
                    messages: previous.messages.filter(
                      (existing) =>
                        existing.id !== claimantMessage.id && existing.id !== streamingId,
                    ),
                  }
                : previous,
          );
        }
      } finally {
        setIsStreaming(false);
        abortRef.current = null;
        void queryClient.invalidateQueries({ queryKey: queryKeys.disputeThread(claimId) });
      }
    },
    [claimId, queryClient],
  );

  const cancel = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return { send, cancel, isStreaming, error };
}
