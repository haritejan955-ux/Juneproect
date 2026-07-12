import { Table } from "@/components/ui/Table";
import type { CoverageLineItem } from "@/lib/types";

export function CoverageTable({ items }: { items: CoverageLineItem[] }) {
  return (
    <Table<CoverageLineItem>
      rows={items}
      emptyMessage="No line-items were evaluated for this claim."
      columns={[
        { header: "CPT", render: (item) => item.cpt_code },
        { header: "Diagnosis", render: (item) => item.diagnosis_code },
        {
          header: "Status",
          render: (item) => (
            <span className={item.status === "approved" ? "text-green-700" : "text-red-700"}>
              {item.status}
            </span>
          ),
        },
        { header: "Cited clause", render: (item) => item.cited_clause },
        {
          header: "Amount covered",
          render: (item) =>
            item.amount_covered != null ? `$${item.amount_covered.toFixed(2)}` : "—",
        },
      ]}
    />
  );
}
