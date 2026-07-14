export type Severity = "none" | "minor" | "moderate" | "major" | "contraindicated";

export type RenalHepaticFunction = "normal" | "mild" | "moderate" | "severe";

export interface PatientProfileIn {
  age?: number | null;
  weight_kg?: number | null;
  sex?: string | null;
  allergies: string[];
  conditions: string[];
  renal_function: RenalHepaticFunction;
  hepatic_function: RenalHepaticFunction;
}

export interface SubmitReportRequest {
  raw_prescription_text: string;
  patient_profile: PatientProfileIn;
}

export interface SubmitReportResponse {
  report_id: string;
  status: string;
}

export interface Medication {
  raw_name: string;
  normalized_name?: string | null;
  drug_class?: string | null;
  allergy_class?: string | null;
  dose_value?: number | null;
  dose_unit?: string | null;
  frequency?: string | null;
  route?: string | null;
  recognized: boolean;
}

export interface Finding {
  category: "interaction" | "allergy" | "dosage";
  severity: Severity;
  description: string;
  drug?: string;
  drugs?: string[];
  citation_doc_id?: string;
  citation_title?: string;
  recommended_max?: string | null;
}

export interface SafetyReportResponse {
  id: string;
  patient_id: string;
  status: "pending" | "processing" | "complete" | "blocked" | "error";
  overall_severity: Severity | null;
  medications: Medication[];
  findings: Finding[];
  summary: string | null;
  pharmacist_review_flag: boolean;
  retry_count: number;
  error: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface AuditEntry {
  timestamp: string;
  agent: string;
  action: string;
  detail: Record<string, unknown>;
}

export interface ReportSummary {
  id: string;
  status: string;
  overall_severity: Severity | null;
  pharmacist_review_flag: boolean;
  created_at: string;
}

export interface ProgressEvent {
  type: "progress" | "complete" | "error";
  agent?: string | null;
  action?: string | null;
  status?: string;
  message?: string;
}
