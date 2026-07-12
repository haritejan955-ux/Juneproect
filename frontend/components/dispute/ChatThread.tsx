"use client";

import { useEffect, useState } from "react";

import { getDisputeThread, postDisputeMessage } from "@/lib/api";
import type { DisputeMessage } from "@/lib/types";

export function ChatThread({ claimId }: { claimId: string }) {
  const [messages, setMessages] = useState<DisputeMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDisputeThread(claimId)
      .then((thread) => setMessages(thread.messages))
      .catch(() => setMessages([]));
  }, [claimId]);

  async function handleSend(event: React.FormEvent) {
    event.preventDefault();
    if (!draft.trim()) return;

    const claimantMessage: DisputeMessage = {
      id: `local-${Date.now()}`,
      role: "claimant",
      content: draft,
      timestamp: new Date().toISOString(),
    };
    setMessages((previous) => [...previous, claimantMessage]);
    setDraft("");
    setSending(true);
    setError(null);

    try {
      const reply = await postDisputeMessage(claimId, claimantMessage.content);
      setMessages((previous) => [...previous, reply]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message.");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="max-h-96 space-y-3 overflow-y-auto rounded-md border border-slate-200 p-4">
        {messages.length === 0 && (
          <p className="text-sm text-slate-400">
            No messages yet — ask about this decision below.
          </p>
        )}
        {messages.map((message) => (
          <div key={message.id} className={message.role === "claimant" ? "text-right" : "text-left"}>
            <span
              className={`inline-block max-w-[80%] rounded-lg px-3 py-2 text-sm ${
                message.role === "claimant"
                  ? "bg-slate-900 text-white"
                  : "bg-slate-100 text-slate-800"
              }`}
            >
              {message.content}
            </span>
          </div>
        ))}
      </div>

      <form onSubmit={handleSend} className="flex gap-2">
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Explain why you're disputing this decision…"
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
        <button
          type="submit"
          disabled={sending}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          Send
        </button>
      </form>

      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
