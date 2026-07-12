// Mirrors backend/app/schemas/*.py — kept in sync by hand since this is a
// two-language monorepo; if this drifts, the symptom is a runtime shape
// mismatch, not a compile error, so treat backend schema changes as
// requiring a matching edit here.

export type ClaimStatus = "processing" | "completed" | "blocked" | "failed";

export interface ClaimSubmitResponse {
  claim_id: string;
  status: ClaimStatus;
}

export interface ClaimStatusResponse {
  claim_id: string;
  claimant_id: string;
  status: ClaimStatus;
  query: string;
  intent: string | null;
  intent_confidence: number | null;
  submitted_at: string;
}

export type DecisionStatus = "approved" | "partial_approved" | "denied" | "blocked";
export type Severity = "low" | "medium" | "high";

export interface CoverageLineItem {
  cpt_code: string;
  diagnosis_code: string;
  status: "approved" | "denied";
  cited_clause: string;
  amount_billed: number | null;
  amount_covered: number | null;
}

export interface FraudSignal {
  signal_type: "duplicate_billing" | "upcoding" | "date_conflict" | "unbundling";
  severity: Severity;
  evidence: string;
}

export interface Citation {
  source_doc: string;
  section: string | null;
  excerpt: string;
}

export interface Decision {
  claim_id: string;
  status: DecisionStatus;
  confidence_score: number;
  low_confidence: boolean;
  attorney_flag: boolean;
  justification: string;
  coverage_map: CoverageLineItem[];
  fraud_signals: FraudSignal[];
  citations: Citation[];
  disclaimer: string;
  retry_count: number;
  created_at: string;
}

export interface DisputeMessage {
  id: string;
  role: "claimant" | "assistant";
  content: string;
  timestamp: string;
}

export interface DisputeThread {
  dispute_id: string;
  claim_id: string;
  status: "open" | "resolved";
  messages: DisputeMessage[];
}

export interface AuditLogEntry {
  agent: string;
  action: string;
  details: Record<string, unknown>;
  timestamp: string;
}

export interface AuditTrail {
  claim_id: string;
  entries: AuditLogEntry[];
}

export interface AgentStreamEvent {
  agent: string;
  status: "completed";
  timestamp: string;
}
