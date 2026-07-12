"use client";

import Link from "next/link";
import { Activity, FileText, MessagesSquare, ScrollText } from "lucide-react";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

const SEGMENTS = [
  { value: "processing", label: "Processing", icon: Activity },
  { value: "decision", label: "Decision", icon: FileText },
  { value: "dispute", label: "Dispute", icon: MessagesSquare },
  { value: "audit", label: "Audit Trail", icon: ScrollText },
] as const;

export function ClaimNav({
  claimId,
  active,
}: {
  claimId: string;
  active: (typeof SEGMENTS)[number]["value"];
}) {
  return (
    <Tabs value={active} className="w-full">
      <TabsList className="w-full justify-start overflow-x-auto sm:w-auto">
        {SEGMENTS.map(({ value, label, icon: Icon }) => (
          <TabsTrigger key={value} value={value} asChild>
            <Link href={`/${value}/${claimId}`} className="flex items-center gap-1.5">
              <Icon className="size-3.5" />
              {label}
            </Link>
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  );
}
