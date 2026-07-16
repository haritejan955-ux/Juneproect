import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, getReport, submitReport } from "./api";

describe("api client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends the API key header and JSON body on submitReport", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ report_id: "abc123", status: "processing" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await submitReport({
      raw_prescription_text: "Tylenol 500mg",
      patient_profile: {
        allergies: [],
        conditions: [],
        renal_function: "normal",
        hepatic_function: "normal",
      },
    });

    expect(result.report_id).toBe("abc123");
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/api/v1/reports");
    expect(init.method).toBe("POST");
    expect(init.headers["X-API-Key"]).toBeDefined();
    expect(JSON.parse(init.body).raw_prescription_text).toBe("Tylenol 500mg");
  });

  it("throws an ApiError with the response status and detail on failure", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: "Not Found",
      json: async () => ({ detail: "Report not found" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(getReport("missing-id")).rejects.toMatchObject(
      new ApiError(404, "Report not found"),
    );
  });
});
