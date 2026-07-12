"use client";

import { useEffect, useRef, useState } from "react";
import { SendHorizontal } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { ChatMessage } from "@/components/dispute/chat-message";
import { useDisputeThread, useStreamDisputeMessage } from "@/hooks/useDispute";

export function ChatThread({ claimId }: { claimId: string }) {
  const { data: thread, isLoading } = useDisputeThread(claimId);
  const { send, isStreaming, error } = useStreamDisputeMessage(claimId);
  const [draft, setDraft] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const messages = thread?.messages ?? [];
  const lastMessageContent = messages.at(-1)?.content;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length, lastMessageContent]);

  function handleSend(event: React.FormEvent) {
    event.preventDefault();
    const trimmed = draft.trim();
    if (!trimmed || isStreaming) return;
    setDraft("");
    void send(trimmed);
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="scrollbar-thin h-[28rem] space-y-4 overflow-y-auto rounded-lg border border-border bg-muted/20 p-4">
        {isLoading && (
          <div className="space-y-4">
            <Skeleton className="ml-auto h-10 w-2/3 rounded-2xl" />
            <Skeleton className="h-14 w-3/4 rounded-2xl" />
          </div>
        )}

        {!isLoading && messages.length === 0 && (
          <p className="flex h-full items-center justify-center text-center text-sm text-muted-foreground">
            No messages yet — ask about this decision below.
          </p>
        )}

        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSend} className="flex items-end gap-2">
        <Textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              handleSend(event);
            }
          }}
          placeholder="Explain why you're disputing this decision…"
          rows={1}
          disabled={isStreaming}
          className="min-h-9 resize-none"
        />
        <Button type="submit" size="icon" disabled={isStreaming || draft.trim().length === 0}>
          <SendHorizontal className="size-4" />
          <span className="sr-only">Send</span>
        </Button>
      </form>

      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  );
}
