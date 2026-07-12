"use client";

import { useMutation } from "@tanstack/react-query";

import { submitClaim } from "@/lib/api";

export function useSubmitClaim() {
  return useMutation({
    mutationFn: ({
      claimantId,
      query,
      files,
    }: {
      claimantId: string;
      query: string;
      files: File[];
    }) => submitClaim(claimantId, query, files),
  });
}
