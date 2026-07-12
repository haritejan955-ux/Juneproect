const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_BASE_URL ?? "ws://localhost:8000";

export function openClaimStream(claimId: string): WebSocket {
  return new WebSocket(`${WS_BASE_URL}/ws/v1/claims/${claimId}/stream`);
}
