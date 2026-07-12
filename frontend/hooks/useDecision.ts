"use client";

import { useQuery } from "@tanstack/react-query";

import { ApiError, getDecision } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

export function useDecision(claimId: string) {
  return useQuery({
    queryKey: queryKeys.decision(claimId),
    queryFn: () => getDecision(claimId),
    retry: (failureCount, error) => {
      // A 404 here means the claim hasn't finished processing yet, not a real failure —
      // don't burn retries on it, the Processing page is what gates navigation here anyway.
      if (error instanceof ApiError && error.status === 404) {
        return false;
      }
      return failureCount < 2;
    },
  });
}
