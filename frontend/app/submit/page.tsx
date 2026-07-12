import { PipelinePreview } from "@/components/claim/pipeline-preview";
import { UploadForm } from "@/components/claim/upload-form";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function SubmitPage() {
  return (
    <div className="mx-auto grid max-w-4xl gap-6 lg:max-w-5xl lg:grid-cols-[1.4fr_1fr]">
      <Card className="animate-in fade-in slide-in-from-bottom-2 duration-500">
        <CardHeader>
          <CardTitle>Submit a claim</CardTitle>
          <CardDescription>
            Upload your claim documents and tell us what you&apos;d like checked — coverage,
            a denial, anything.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <UploadForm />
        </CardContent>
      </Card>

      <div className="animate-in fade-in slide-in-from-bottom-2 duration-500 [animation-delay:100ms] [animation-fill-mode:backwards]">
        <PipelinePreview />
      </div>
    </div>
  );
}
