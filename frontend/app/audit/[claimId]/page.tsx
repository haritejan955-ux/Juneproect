import { AuditTimeline } from "@/components/audit/AuditTimeline";
import { Card } from "@/components/ui/Card";
import { getAuditTrail } from "@/lib/api";

interface AuditPageProps {
  params: { claimId: string };
}

export default async function AuditPage({ params }: AuditPageProps) {
  const trail = await getAuditTrail(params.claimId);

  return (
    <Card title="Audit trail">
      <AuditTimeline entries={trail.entries} />
    </Card>
  );
}
