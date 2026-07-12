const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_BASE_URL ?? "ws://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "";

export function openClaimStream(claimId: string): WebSocket {
  // Auth is a query param here, not the X-API-Key header lib/api.ts uses for REST calls —
  // the browser WebSocket API cannot set custom headers on the connect handshake. See
  // backend/app/api/websocket.py.
  return new WebSocket(
    `${WS_BASE_URL}/ws/v1/claims/${claimId}/stream?api_key=${encodeURIComponent(API_KEY)}`,
  );
}
