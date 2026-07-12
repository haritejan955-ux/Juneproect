"use client";

import { useQuery } from "@tanstack/react-query";

import { getClaimStatus } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

/** Polls claim status; used as the authoritative "is it actually safe to navigate to the
 * decision page yet" check once the WS stream reports a terminal event — the WS event and
 * the DB write it depends on aren't guaranteed to be simultaneous. */
export function useClaimStatus(claimId: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: queryKeys.claimStatus(claimId),
    queryFn: () => getClaimStatus(claimId),
    enabled: options?.enabled ?? true,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "processing" ? 1500 : false;
    },
  });
}
