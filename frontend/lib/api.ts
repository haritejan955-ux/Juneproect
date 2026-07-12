import type {
  AuditTrail,
  ClaimStatusResponse,
  ClaimSubmitResponse,
  Decision,
  DisputeMessage,
  DisputeThread,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("X-API-Key", API_KEY);

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}) as Record<string, unknown>);
    const message = typeof body.message === "string" ? body.message : undefined;
    throw new Error(message ?? `Request to ${path} failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function submitClaim(
  claimantId: string,
  query: string,
  files: File[],
): Promise<ClaimSubmitResponse> {
  const formData = new FormData();
  formData.append("claimant_id", claimantId);
  formData.append("query", query);
  files.forEach((file) => formData.append("files", file));

  return apiFetch<ClaimSubmitResponse>("/api/v1/claims", {
    method: "POST",
    body: formData,
  });
}

export function getClaimStatus(claimId: string): Promise<ClaimStatusResponse> {
  return apiFetch<ClaimStatusResponse>(`/api/v1/claims/${claimId}`);
}

export function getDecision(claimId: string): Promise<Decision> {
  return apiFetch<Decision>(`/api/v1/claims/${claimId}/decision`);
}

export function postDisputeMessage(claimId: string, message: string): Promise<DisputeMessage> {
  return apiFetch<DisputeMessage>(`/api/v1/claims/${claimId}/dispute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
}

export function getDisputeThread(claimId: string): Promise<DisputeThread> {
  return apiFetch<DisputeThread>(`/api/v1/claims/${claimId}/dispute`);
}

export function getAuditTrail(claimId: string): Promise<AuditTrail> {
  return apiFetch<AuditTrail>(`/api/v1/claims/${claimId}/audit`);
}
