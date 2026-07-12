export const queryKeys = {
  claimStatus: (claimId: string) => ["claim", claimId, "status"] as const,
  decision: (claimId: string) => ["claim", claimId, "decision"] as const,
  disputeThread: (claimId: string) => ["claim", claimId, "dispute"] as const,
  auditTrail: (claimId: string) => ["claim", claimId, "audit"] as const,
};
