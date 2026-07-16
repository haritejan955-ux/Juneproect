import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { SubmitPage } from "./SubmitPage";

vi.mock("../lib/api", () => ({
  submitReport: vi.fn().mockResolvedValue({ report_id: "report-123", status: "processing" }),
}));

describe("SubmitPage", () => {
  it("submits the prescription form and navigates to the processing screen", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/submit"]}>
        <Routes>
          <Route path="/submit" element={<SubmitPage />} />
          <Route path="/processing/:reportId" element={<div>Processing report-123</div>} />
        </Routes>
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText(/prescription list/i), "Warfarin 5mg daily");
    await user.click(screen.getByRole("button", { name: /run safety check/i }));

    expect(await screen.findByText("Processing report-123")).toBeInTheDocument();
  });
});
