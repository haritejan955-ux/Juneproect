import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

export function ConfidenceMeter({
  score,
  lowConfidence,
}: {
  score: number;
  lowConfidence: boolean;
}) {
  const pct = Math.round(score * 100);

  return (
    <div className="max-w-xs space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">Confidence</span>
        <span className={cn("font-medium tabular-nums", lowConfidence && "text-warning")}>
          {pct}%{lowConfidence && " · low confidence"}
        </span>
      </div>
      <Progress
        value={pct}
        indicatorClassName={lowConfidence ? "bg-warning" : undefined}
        className="h-1.5"
      />
    </div>
  );
}
