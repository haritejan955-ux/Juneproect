import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ChatMessage } from "./chat-message";
import type { DisputeMessage } from "@/lib/types";

function message(overrides: Partial<DisputeMessage>): DisputeMessage {
  return {
    id: "m1",
    role: "assistant",
    content: "",
    timestamp: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("ChatMessage", () => {
  it("renders the message text when content is present", () => {
    render(<ChatMessage message={message({ role: "claimant", content: "Why was this denied?" })} />);

    expect(screen.getByText("Why was this denied?")).toBeInTheDocument();
  });

  it("renders a typing indicator instead of text when content is still empty", () => {
    const { container } = render(<ChatMessage message={message({ content: "" })} />);

    expect(container.querySelectorAll(".animate-bounce")).toHaveLength(3);
  });

  it("does not render the typing indicator once content has arrived", () => {
    const { container } = render(<ChatMessage message={message({ content: "partial rep" })} />);

    expect(container.querySelectorAll(".animate-bounce")).toHaveLength(0);
  });
});
