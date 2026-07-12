import type { Citation } from "@/lib/types";

export function CitationList({ citations }: { citations: Citation[] }) {
  if (citations.length === 0) {
    return <p className="text-sm text-slate-500">No citations were recorded.</p>;
  }

  return (
    <ul className="space-y-2 text-sm">
      {citations.map((citation, index) => (
        <li key={index} className="border-l-2 border-slate-300 pl-3">
          <p className="font-medium text-slate-800">
            {citation.source_doc}
            {citation.section ? ` — ${citation.section}` : ""}
          </p>
          <p className="text-slate-600">{citation.excerpt}</p>
        </li>
      ))}
    </ul>
  );
}
