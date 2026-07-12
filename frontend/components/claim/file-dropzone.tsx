"use client";

import { useCallback, useId, useState } from "react";
import { File as FileIcon, UploadCloud, X } from "lucide-react";

import { cn } from "@/lib/utils";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function FileDropzone({
  files,
  onChange,
  disabled,
}: {
  files: File[];
  onChange: (files: File[]) => void;
  disabled?: boolean;
}) {
  const inputId = useId();
  const [isDragging, setIsDragging] = useState(false);

  const addFiles = useCallback(
    (incoming: FileList | null) => {
      if (!incoming) return;
      const pdfs = Array.from(incoming).filter((file) => file.type === "application/pdf");
      if (pdfs.length > 0) onChange([...files, ...pdfs]);
    },
    [files, onChange],
  );

  return (
    <div className="space-y-3">
      <label
        htmlFor={inputId}
        onDragOver={(event) => {
          event.preventDefault();
          if (!disabled) setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setIsDragging(false);
          if (!disabled) addFiles(event.dataTransfer.files);
        }}
        className={cn(
          "group flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors",
          isDragging ? "border-primary bg-accent" : "border-input hover:bg-muted/40",
          disabled && "pointer-events-none opacity-50",
        )}
      >
        <UploadCloud className="size-8 text-muted-foreground transition-transform group-hover:-translate-y-0.5 group-hover:text-primary" />
        <p className="text-sm font-medium">
          Drag & drop claim documents, or <span className="text-primary">browse</span>
        </p>
        <p className="text-xs text-muted-foreground">PDF only, one or more files</p>
        <input
          id={inputId}
          type="file"
          accept="application/pdf"
          multiple
          disabled={disabled}
          className="sr-only"
          onChange={(event) => {
            addFiles(event.target.files);
            event.target.value = "";
          }}
        />
      </label>

      {files.length > 0 && (
        <ul className="space-y-1.5">
          {files.map((file, index) => (
            <li
              key={`${file.name}-${index}`}
              className="animate-in fade-in slide-in-from-top-1 flex items-center justify-between gap-3 rounded-md border border-border bg-card px-3 py-2 text-sm duration-200"
            >
              <span className="flex min-w-0 items-center gap-2">
                <FileIcon className="size-4 shrink-0 text-muted-foreground" />
                <span className="truncate font-medium">{file.name}</span>
                <span className="shrink-0 text-xs text-muted-foreground">
                  {formatBytes(file.size)}
                </span>
              </span>
              <button
                type="button"
                disabled={disabled}
                onClick={() => onChange(files.filter((_, i) => i !== index))}
                className="shrink-0 rounded-full p-1 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
                aria-label={`Remove ${file.name}`}
              >
                <X className="size-3.5" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
