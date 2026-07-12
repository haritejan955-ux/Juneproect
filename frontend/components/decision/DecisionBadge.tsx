import { Badge } from "@/components/ui/Badge";
import type { DecisionStatus } from "@/lib/types";

const STATUS_VARIANT: Record<DecisionStatus, "green" | "amber" | "red" | "gray"> = {
  approved: "green",
  partial_approved: "amber",
  denied: "red",
  blocked: "gray",
};

const STATUS_LABEL: Record<DecisionStatus, string> = {
  approved: "Approved",
  partial_approved: "Partially Approved",
  denied: "Denied",
  blocked: "Blocked",
};

export function DecisionBadge({ status }: { status: DecisionStatus }) {
  return <Badge variant={STATUS_VARIANT[status]}>{STATUS_LABEL[status]}</Badge>;
}
