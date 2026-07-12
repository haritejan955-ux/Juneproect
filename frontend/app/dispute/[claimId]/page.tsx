import { ChatThread } from "@/components/dispute/ChatThread";
import { Card } from "@/components/ui/Card";

interface DisputePageProps {
  params: { claimId: string };
}

export default function DisputePage({ params }: DisputePageProps) {
  return (
    <Card title="Dispute this decision">
      <ChatThread claimId={params.claimId} />
    </Card>
  );
}
