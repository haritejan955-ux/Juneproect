import type {
  AuditEntry,
  ReportSummary,
  SafetyReportResponse,
  SubmitReportRequest,
  SubmitReportResponse,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const API_KEY = import.meta.env.VITE_API_KEY ?? "";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY,
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, body.detail ?? response.statusText);
  }

  return response.json() as Promise<T>;
}

export function submitReport(payload: SubmitReportRequest): Promise<SubmitReportResponse> {
  return request("/api/v1/reports", { method: "POST", body: JSON.stringify(payload) });
}

export function getReport(reportId: string): Promise<SafetyReportResponse> {
  return request(`/api/v1/reports/${reportId}`);
}

export function getReportAudit(reportId: string): Promise<AuditEntry[]> {
  return request(`/api/v1/reports/${reportId}/audit`);
}

export function listReports(): Promise<ReportSummary[]> {
  return request("/api/v1/reports");
}

export function reportProgressSocketUrl(reportId: string): string {
  const wsBase = API_BASE_URL.replace(/^http/, "ws");
  return `${wsBase}/ws/reports/${reportId}?api_key=${encodeURIComponent(API_KEY)}`;
}
