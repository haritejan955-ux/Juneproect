import { UploadForm } from "@/components/claim/UploadForm";
import { Card } from "@/components/ui/Card";

export default function SubmitPage() {
  return (
    <Card title="Submit a claim">
      <UploadForm />
    </Card>
  );
}
