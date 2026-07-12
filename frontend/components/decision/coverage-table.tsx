import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { CoverageLineItem } from "@/lib/types";

function formatCurrency(amount: number | null): string {
  if (amount == null) return "—";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(amount);
}

export function CoverageTable({ items }: { items: CoverageLineItem[] }) {
  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground">No line-items were evaluated for this claim.</p>;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>CPT</TableHead>
          <TableHead>Diagnosis</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Cited clause</TableHead>
          <TableHead className="text-right">Billed</TableHead>
          <TableHead className="text-right">Covered</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.map((item, index) => (
          <TableRow key={index}>
            <TableCell className="font-mono text-xs">{item.cpt_code}</TableCell>
            <TableCell className="font-mono text-xs">{item.diagnosis_code}</TableCell>
            <TableCell>
              <Badge variant={item.status === "approved" ? "success" : "destructive"}>
                {item.status}
              </Badge>
            </TableCell>
            <TableCell className="max-w-[16rem] truncate text-muted-foreground" title={item.cited_clause}>
              {item.cited_clause}
            </TableCell>
            <TableCell className="text-right tabular-nums">
              {formatCurrency(item.amount_billed)}
            </TableCell>
            <TableCell className="text-right tabular-nums font-medium">
              {formatCurrency(item.amount_covered)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
