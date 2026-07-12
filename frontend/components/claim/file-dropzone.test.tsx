import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { FileDropzone } from "./file-dropzone";

function pdfFile(name: string, sizeBytes = 1024): File {
  const file = new File([new Uint8Array(sizeBytes)], name, { type: "application/pdf" });
  return file;
}

function textFile(name: string): File {
  return new File(["not a pdf"], name, { type: "text/plain" });
}

describe("FileDropzone", () => {
  it("adds a selected PDF file via onChange", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<FileDropzone files={[]} onChange={onChange} />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    await user.upload(input, pdfFile("claim.pdf"));

    expect(onChange).toHaveBeenCalledTimes(1);
    const [newFiles] = onChange.mock.calls[0];
    expect(newFiles).toHaveLength(1);
    expect(newFiles[0].name).toBe("claim.pdf");
  });

  it("filters out non-PDF files and never calls onChange for them", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<FileDropzone files={[]} onChange={onChange} />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    await user.upload(input, textFile("not-a-claim.txt"));

    expect(onChange).not.toHaveBeenCalled();
  });

  it("appends to existing files rather than replacing them", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    const existing = [pdfFile("already-attached.pdf")];
    render(<FileDropzone files={existing} onChange={onChange} />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    await user.upload(input, pdfFile("second.pdf"));

    const [newFiles] = onChange.mock.calls[0];
    expect(newFiles.map((f: File) => f.name)).toEqual(["already-attached.pdf", "second.pdf"]);
  });

  it("renders an attached file's name and lets it be removed", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    const existing = [pdfFile("claim.pdf")];
    render(<FileDropzone files={existing} onChange={onChange} />);

    expect(screen.getByText("claim.pdf")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /remove claim\.pdf/i }));

    expect(onChange).toHaveBeenCalledWith([]);
  });

  it("disables the remove button when disabled", () => {
    const existing = [pdfFile("claim.pdf")];
    render(<FileDropzone files={existing} onChange={vi.fn()} disabled />);

    expect(screen.getByRole("button", { name: /remove claim\.pdf/i })).toBeDisabled();
  });
});
