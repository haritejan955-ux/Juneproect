import { Scale } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export function AttorneyFlagBanner({ show }: { show: boolean }) {
  if (!show) return null;

  return (
    <Alert variant="destructive" role="alert" className="animate-in fade-in slide-in-from-top-1">
      <Scale className="size-4" />
      <AlertTitle>Flagged for attorney review</AlertTitle>
      <AlertDescription>
        This claim has been flagged due to a high-severity fraud signal or a high-risk legal
        interpretation. This flag cannot be dismissed.
      </AlertDescription>
    </Alert>
  );
}
