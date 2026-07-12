import { AttorneyFlagBanner } from "@/components/decision/AttorneyFlagBanner";
import { CitationList } from "@/components/decision/CitationList";
import { CoverageTable } from "@/components/decision/CoverageTable";
import { DecisionBadge } from "@/components/decision/DecisionBadge";
import { FraudSignalsPanel } from "@/components/decision/FraudSignalsPanel";
import { Card } from "@/components/ui/Card";
import { getDecision } from "@/lib/api";

interface DecisionPageProps {
  params: { claimId: string };
}

export default async function DecisionPage({ params }: DecisionPageProps) {
  const decision = await getDecision(params.claimId);

  return (
    <div className="space-y-6">
      <AttorneyFlagBanner show={decision.attorney_flag} />

      <Card title="Decision">
        <div className="mb-4 flex items-center gap-4">
          <DecisionBadge status={decision.status} />
          <span className="text-sm text-slate-500">
            Confidence: {(decision.confidence_score * 100).toFixed(0)}%
            {decision.low_confidence && " (low confidence)"}
          </span>
        </div>
        <p className="text-sm text-slate-700">{decision.justification}</p>
      </Card>

      <Card title="Coverage">
        <CoverageTable items={decision.coverage_map} />
      </Card>

      <Card title="Fraud signals">
        <FraudSignalsPanel signals={decision.fraud_signals} />
      </Card>

      <Card title="Citations">
        <CitationList citations={decision.citations} />
      </Card>

      <Card title="Disclaimer">
        <p className="text-sm text-slate-500">{decision.disclaimer}</p>
      </Card>
    </div>
  );
}
