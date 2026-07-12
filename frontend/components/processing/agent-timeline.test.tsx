import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AgentTimeline, computeProgress } from "./agent-timeline";
import type { AgentStreamEvent } from "@/lib/types";

function event(agent: string, timestamp = "2026-01-01T00:00:00Z"): AgentStreamEvent {
  return { agent, status: "completed", timestamp };
}

describe("computeProgress", () => {
  it("is 0 for no events", () => {
    expect(computeProgress([])).toBe(0);
  });

  it("counts each of the 9 canonical pipeline steps once towards the total", () => {
    const events = [
      event("document_preprocessor"),
      event("intent_analyzer"),
      event("rag_retriever"),
    ];
    expect(computeProgress(events)).toBe(Math.round((3 / 9) * 100));
  });

  it("is 100 once every canonical step has completed", () => {
    const allNine = [
      "document_preprocessor",
      "intent_analyzer",
      "rag_retriever",
      "security_checker",
      "coverage_validator",
      "fraud_detector",
      "answer_synthesizer",
      "self_critic",
      "final_output",
    ].map((agent) => event(agent));

    expect(computeProgress(allNine)).toBe(100);
  });

  it("is 100 immediately on a blocked event, regardless of how few steps ran", () => {
    const events = [event("document_preprocessor"), event("intent_analyzer"), event("blocked")];
    expect(computeProgress(events)).toBe(100);
  });

  it("does not double count a step that reports completion more than once", () => {
    const events = [event("document_preprocessor"), event("document_preprocessor")];
    expect(computeProgress(events)).toBe(Math.round((1 / 9) * 100));
  });

  it("ignores an unrecognized agent name rather than inflating the total", () => {
    const events = [event("document_preprocessor"), event("some_future_agent")];
    expect(computeProgress(events)).toBe(Math.round((1 / 9) * 100));
  });
});

describe("AgentTimeline", () => {
  it("shows a distinct blocked message on the Security Checker step when blocked", () => {
    const events = [
      event("document_preprocessor"),
      event("intent_analyzer"),
      event("rag_retriever"),
      event("blocked"),
    ];

    render(<AgentTimeline events={events} />);

    expect(screen.getByText(/Blocked — prompt injection detected/i)).toBeInTheDocument();
  });

  it("renders every canonical step label even before any events arrive", () => {
    render(<AgentTimeline events={[]} />);

    expect(screen.getByText("Document Preprocessor")).toBeInTheDocument();
    expect(screen.getByText("Final Output")).toBeInTheDocument();
  });

  it("shows the retry count when Self-Critic requested a retry", () => {
    const events = [event("prepare_retry"), event("answer_synthesizer"), event("self_critic")];

    render(<AgentTimeline events={events} />);

    expect(screen.getByText(/requested 1 retry/i)).toBeInTheDocument();
  });
});
