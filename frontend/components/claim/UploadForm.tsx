"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { submitClaim } from "@/lib/api";

export function UploadForm() {
  const router = useRouter();
  const [claimantId, setClaimantId] = useState("");
  const [query, setQuery] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (files.length === 0) {
      setError("Attach at least one claim document.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const response = await submitClaim(claimantId, query, files);
      router.push(`/processing/${response.claim_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission failed.");
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="claimantId" className="block text-sm font-medium text-slate-700">
          Claimant ID
        </label>
        <input
          id="claimantId"
          required
          value={claimantId}
          onChange={(event) => setClaimantId(event.target.value)}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
      </div>

      <div>
        <label htmlFor="query" className="block text-sm font-medium text-slate-700">
          What would you like us to check?
        </label>
        <textarea
          id="query"
          required
          rows={3}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          placeholder="e.g. Is my recent MRI covered under my policy?"
        />
      </div>

      <div>
        <label htmlFor="files" className="block text-sm font-medium text-slate-700">
          Claim documents (PDF)
        </label>
        <input
          id="files"
          type="file"
          accept="application/pdf"
          multiple
          onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
          className="mt-1 w-full text-sm"
        />
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {submitting ? "Submitting…" : "Submit claim"}
      </button>
    </form>
  );
}
