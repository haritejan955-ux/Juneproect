import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SeverityBadge } from "./SeverityBadge";

describe("SeverityBadge", () => {
  it("renders the human-readable label for each severity", () => {
    render(<SeverityBadge severity="contraindicated" />);
    expect(screen.getByText("Contraindicated")).toBeInTheDocument();
  });

  it("renders 'No concerns' for none severity", () => {
    render(<SeverityBadge severity="none" />);
    expect(screen.getByText("No concerns")).toBeInTheDocument();
  });
});
