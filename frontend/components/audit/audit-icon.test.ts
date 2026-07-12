import { describe, expect, it } from "vitest";

import { agentLabel } from "./audit-icon";

describe("agentLabel", () => {
  it("title-cases each underscore-separated word", () => {
    expect(agentLabel("document_preprocessor")).toBe("Document Preprocessor");
    expect(agentLabel("self_critic")).toBe("Self Critic");
    expect(agentLabel("final_output")).toBe("Final Output");
  });

  it("leaves a single-word agent name capitalized", () => {
    expect(agentLabel("blocked")).toBe("Blocked");
  });
});
