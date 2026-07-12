import { CheckCircle2, ShieldOff, SplitSquareHorizontal, XCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { DecisionStatus } from "@/lib/types";

const STATUS_CONFIG: Record<
  DecisionStatus,
  { label: string; variant: "success" | "warning" | "destructive" | "muted"; icon: typeof CheckCircle2 }
> = {
  approved: { label: "Approved", variant: "success", icon: CheckCircle2 },
  partial_approved: { label: "Partially Approved", variant: "warning", icon: SplitSquareHorizontal },
  denied: { label: "Denied", variant: "destructive", icon: XCircle },
  blocked: { label: "Blocked", variant: "muted", icon: ShieldOff },
};

export function DecisionBadge({ status, className }: { status: DecisionStatus; className?: string }) {
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;

  return (
    <Badge variant={config.variant} className={cn("px-3 py-1 text-sm", className)}>
      <Icon className="size-4" />
      {config.label}
    </Badge>
  );
}
