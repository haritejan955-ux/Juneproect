import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, getDecision, streamDisputeMessage, submitClaim } from "./api";

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function sseResponse(frames: string[]): Response {
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      const encoder = new TextEncoder();
      for (const frame of frames) {
        controller.enqueue(encoder.encode(frame));
      }
      controller.close();
    },
  });
  return new Response(stream, { status: 200 });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("apiFetch error handling (via submitClaim/getDecision)", () => {
  it("resolves with the parsed JSON body on success", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(202, { claim_id: "abc", status: "processing" })),
    );

    const result = await submitClaim("claimant-1", "is this covered?", []);

    expect(result).toEqual({ claim_id: "abc", status: "processing" });
  });

  it("throws an ApiError carrying the backend's message and status on failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(404, { error_code: "claim_not_found", message: "No decision yet." }),
      ),
    );

    await expect(getDecision("missing-claim")).rejects.toMatchObject({
      message: "No decision yet.",
      status: 404,
    });
  });

  it("falls back to a generic message when the error body has no message field", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(500, {})));

    let caught: unknown;
    try {
      await getDecision("some-claim");
    } catch (err) {
      caught = err;
    }

    expect(caught).toBeInstanceOf(ApiError);
    expect((caught as ApiError).message).toContain("failed with status 500");
  });

  it("sends an X-API-Key header on every request", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, {}));
    vi.stubGlobal("fetch", fetchMock);

    await getDecision("claim-1");

    const [, init] = fetchMock.mock.calls[0];
    const headers = init.headers as Headers;
    expect(headers.has("X-API-Key")).toBe(true);
  });
});

describe("streamDisputeMessage", () => {
  it("parses token and done SSE frames into structured events, in order", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        sseResponse([
          'event: token\ndata: {"content": "Hello"}\n\n',
          'event: token\ndata: {"content": ", world"}\n\n',
          'event: done\ndata: {"id": "msg-1", "timestamp": "2026-01-01T00:00:00+00:00"}\n\n',
        ]),
      ),
    );

    const events = [];
    for await (const event of streamDisputeMessage("claim-1", "why?")) {
      events.push(event);
    }

    expect(events).toEqual([
      { event: "token", data: { content: "Hello" } },
      { event: "token", data: { content: ", world" } },
      { event: "done", data: { id: "msg-1", timestamp: "2026-01-01T00:00:00+00:00" } },
    ]);
  });

  it("correctly reassembles a frame split across multiple stream chunks", async () => {
    // Simulates a frame arriving in two separate network reads — the parser buffers until it
    // sees the blank-line frame terminator, rather than assuming one chunk == one frame.
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        sseResponse(['event: token\ndata: {"content"', ': "partial"}\n\n']),
      ),
    );

    const events = [];
    for await (const event of streamDisputeMessage("claim-1", "why?")) {
      events.push(event);
    }

    expect(events).toEqual([{ event: "token", data: { content: "partial" } }]);
  });

  it("throws an ApiError instead of yielding when the response is not ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(404, { message: "No finalized decision exists for claim x" }),
      ),
    );

    async function drain() {
      const events = [];
      for await (const event of streamDisputeMessage("claim-x", "why?")) {
        events.push(event);
      }
      return events;
    }

    await expect(drain()).rejects.toMatchObject({
      message: "No finalized decision exists for claim x",
      status: 404,
    });
  });
});
