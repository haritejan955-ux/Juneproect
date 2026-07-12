import { ClaimNav } from "@/components/layout/claim-nav";
import { ChatThread } from "@/components/dispute/chat-thread";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

interface DisputePageProps {
  params: { claimId: string };
}

export default function DisputePage({ params }: DisputePageProps) {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <ClaimNav claimId={params.claimId} active="dispute" />

      <Card className="animate-in fade-in slide-in-from-bottom-2 duration-500">
        <CardHeader>
          <CardTitle>Dispute this decision</CardTitle>
          <CardDescription>
            Replies stream in live and are grounded in the original citations plus any newly
            relevant policy clauses — this doesn&apos;t re-process your original documents.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ChatThread claimId={params.claimId} />
        </CardContent>
      </Card>
    </div>
  );
}
