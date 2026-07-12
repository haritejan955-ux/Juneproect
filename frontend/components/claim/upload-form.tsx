"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Spinner } from "@/components/ui/spinner";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { FileDropzone } from "@/components/claim/file-dropzone";
import { useSubmitClaim } from "@/hooks/useSubmitClaim";

export function UploadForm() {
  const router = useRouter();
  const [claimantId, setClaimantId] = useState("");
  const [query, setQuery] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [validationError, setValidationError] = useState<string | null>(null);

  const { mutate, isPending, error } = useSubmitClaim();

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (files.length === 0) {
      setValidationError("Attach at least one claim document.");
      return;
    }
    setValidationError(null);

    mutate(
      { claimantId, query, files },
      {
        onSuccess: (response) => {
          router.push(`/processing/${response.claim_id}`);
        },
        onError: (err) => {
          toast.error("Couldn't submit claim", {
            description: err instanceof Error ? err.message : "Please try again.",
          });
        },
      },
    );
  }

  const displayError = validationError ?? (error instanceof Error ? error.message : null);

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="space-y-1.5">
        <Label htmlFor="claimantId">Claimant ID</Label>
        <Input
          id="claimantId"
          required
          placeholder="claimant-12345"
          value={claimantId}
          disabled={isPending}
          onChange={(event) => setClaimantId(event.target.value)}
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="query">What would you like us to check?</Label>
        <Textarea
          id="query"
          required
          rows={3}
          placeholder="e.g. Is my recent MRI covered under my policy?"
          value={query}
          disabled={isPending}
          onChange={(event) => setQuery(event.target.value)}
        />
      </div>

      <div className="space-y-1.5">
        <Label>Claim documents</Label>
        <FileDropzone files={files} onChange={setFiles} disabled={isPending} />
      </div>

      {displayError && (
        <Alert variant="destructive">
          <AlertDescription>{displayError}</AlertDescription>
        </Alert>
      )}

      <Button type="submit" disabled={isPending} size="lg" className="w-full sm:w-auto">
        {isPending ? (
          <>
            <Spinner /> Submitting…
          </>
        ) : (
          <>
            Submit claim <ArrowRight className="size-4" />
          </>
        )}
      </Button>
    </form>
  );
}
