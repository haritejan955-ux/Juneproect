import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { FindingsList } from "./FindingsList";
import type { Finding } from "../lib/types";

describe("FindingsList", () => {
  it("shows a fallback message when there are no findings", () => {
    render(<FindingsList findings={[]} />);
    expect(screen.getByText(/no safety findings/i)).toBeInTheDocument();
  });

  it("renders each finding with its severity, drugs, and citation", () => {
    const findings: Finding[] = [
      {
        category: "interaction",
        severity: "major",
        description: "Concurrent use raises bleeding risk.",
        drugs: ["warfarin", "aspirin"],
        citation_doc_id: "warfarin_aspirin",
        citation_title: "Warfarin + Aspirin",
      },
    ];
    render(<FindingsList findings={findings} />);

    expect(screen.getByText(/drug interaction/i)).toBeInTheDocument();
    expect(screen.getByText("Concurrent use raises bleeding risk.")).toBeInTheDocument();
    expect(screen.getByText(/Source: Warfarin \+ Aspirin/)).toBeInTheDocument();
    expect(screen.getByText("Major")).toBeInTheDocument();
  });
});
