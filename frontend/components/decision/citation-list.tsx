import { Quote } from "lucide-react";

import type { Citation } from "@/lib/types";

export function CitationList({ citations }: { citations: Citation[] }) {
  if (citations.length === 0) {
    return <p className="text-sm text-muted-foreground">No citations were recorded.</p>;
  }

  return (
    <ul className="space-y-3">
      {citations.map((citation, index) => (
        <li
          key={index}
          className="relative rounded-lg border border-border bg-muted/30 py-2.5 pl-9 pr-3"
        >
          <Quote className="absolute left-3 top-2.5 size-3.5 text-muted-foreground/60" />
          <p className="text-sm font-medium">
            {citation.source_doc}
            {citation.section ? (
              <span className="font-normal text-muted-foreground"> — {citation.section}</span>
            ) : null}
          </p>
          <p className="mt-0.5 text-sm italic text-muted-foreground">&ldquo;{citation.excerpt}&rdquo;</p>
        </li>
      ))}
    </ul>
  );
}
