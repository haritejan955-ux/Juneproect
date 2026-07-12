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

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function authHeaders(extra?: HeadersInit): Headers {
  const headers = new Headers(extra);
  headers.set("X-API-Key", API_KEY);
  return headers;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: authHeaders(init?.headers),
    cache: "no-store",
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}) as Record<string, unknown>);
    const message = typeof body.message === "string" ? body.message : undefined;
    throw new ApiError(
      message ?? `Request to ${path} failed with status ${response.status}`,
      response.status,
    );
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

export type DisputeStreamEvent =
  | { event: "token"; data: { content: string } }
  | { event: "done"; data: { id: string; timestamp: string } };

/**
 * Consumes `POST /dispute/stream`'s Server-Sent Events by hand rather than the browser's
 * `EventSource` API — `EventSource` only supports unauthenticated `GET` requests, and this
 * endpoint is a `POST` that needs the `X-API-Key` header. `fetch` + a manual `ReadableStream`
 * reader is the standard workaround; frames are separated by a blank line per the SSE spec.
 */
export async function* streamDisputeMessage(
  claimId: string,
  message: string,
  signal?: AbortSignal,
): AsyncGenerator<DisputeStreamEvent> {
  const response = await fetch(`${API_BASE_URL}/api/v1/claims/${claimId}/dispute/stream`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ message }),
    signal,
  });

  if (!response.ok || !response.body) {
    const body = await response.json().catch(() => ({}) as Record<string, unknown>);
    const errorMessage = typeof body.message === "string" ? body.message : undefined;
    throw new ApiError(errorMessage ?? "Streaming request failed.", response.status);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let frameEnd = buffer.indexOf("\n\n");
    while (frameEnd !== -1) {
      const frame = buffer.slice(0, frameEnd);
      buffer = buffer.slice(frameEnd + 2);

      const eventLine = frame.split("\n").find((line) => line.startsWith("event: "));
      const dataLine = frame.split("\n").find((line) => line.startsWith("data: "));
      if (eventLine && dataLine) {
        const event = eventLine.slice("event: ".length).trim();
        const data = JSON.parse(dataLine.slice("data: ".length));
        yield { event, data } as DisputeStreamEvent;
      }

      frameEnd = buffer.indexOf("\n\n");
    }
  }
}
