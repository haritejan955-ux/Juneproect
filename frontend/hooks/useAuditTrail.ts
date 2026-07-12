"use client";

import { useQuery } from "@tanstack/react-query";

import { getAuditTrail } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

export function useAuditTrail(claimId: string) {
  return useQuery({
    queryKey: queryKeys.auditTrail(claimId),
    queryFn: () => getAuditTrail(claimId),
  });
}
