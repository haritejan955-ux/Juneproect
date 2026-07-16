import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useReportProgress } from "./useReportProgress";

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: (() => void) | null = null;
  constructor(public url: string) {
    FakeWebSocket.instances.push(this);
  }
  close() {}
  emit(data: unknown) {
    this.onmessage?.({ data: JSON.stringify(data) });
  }
}

describe("useReportProgress", () => {
  beforeEach(() => {
    FakeWebSocket.instances = [];
    vi.stubGlobal("WebSocket", FakeWebSocket);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("tracks the latest agent to report progress and flips done on completion", () => {
    const { result } = renderHook(() => useReportProgress("report-1"));
    const socket = FakeWebSocket.instances[0];

    act(() => socket.emit({ type: "progress", agent: "prescription_parser", action: "parsed_medications" }));
    expect(result.current.latestAgent).toBe("prescription_parser");
    expect(result.current.done).toBe(false);

    act(() => socket.emit({ type: "progress", agent: "drug_normalizer", action: "normalized_medications" }));
    expect(result.current.latestAgent).toBe("drug_normalizer");

    act(() => socket.emit({ type: "complete", status: "complete" }));
    expect(result.current.done).toBe(true);
    expect(result.current.finalStatus).toBe("complete");
  });
});
