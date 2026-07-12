import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DecisionBadge } from "./decision-badge";
import type { DecisionStatus } from "@/lib/types";

const EXPECTED_LABEL: Record<DecisionStatus, string> = {
  approved: "Approved",
  partial_approved: "Partially Approved",
  denied: "Denied",
  blocked: "Blocked",
};

describe("DecisionBadge", () => {
  for (const status of Object.keys(EXPECTED_LABEL) as DecisionStatus[]) {
    it(`renders the "${EXPECTED_LABEL[status]}" label for status "${status}"`, () => {
      render(<DecisionBadge status={status} />);
      expect(screen.getByText(EXPECTED_LABEL[status])).toBeInTheDocument();
    });
  }
});
