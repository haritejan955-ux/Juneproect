import { Bot, User } from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { TypingDots } from "@/components/dispute/typing-dots";
import { cn } from "@/lib/utils";
import type { DisputeMessage } from "@/lib/types";

export function ChatMessage({ message }: { message: DisputeMessage }) {
  const isClaimant = message.role === "claimant";

  return (
    <div
      className={cn(
        "flex animate-in fade-in slide-in-from-bottom-1 items-end gap-2 duration-300",
        isClaimant && "flex-row-reverse",
      )}
    >
      <Avatar className="size-7 shrink-0">
        <AvatarFallback className={isClaimant ? "bg-primary/15 text-primary" : undefined}>
          {isClaimant ? <User className="size-3.5" /> : <Bot className="size-3.5" />}
        </AvatarFallback>
      </Avatar>

      <div
        className={cn(
          "max-w-[75%] rounded-2xl px-3.5 py-2 text-sm leading-relaxed shadow-sm",
          isClaimant
            ? "rounded-br-sm bg-primary text-primary-foreground"
            : "rounded-bl-sm bg-muted text-foreground",
        )}
      >
        {message.content.length > 0 ? (
          <span className="whitespace-pre-wrap">{message.content}</span>
        ) : (
          <TypingDots />
        )}
      </div>
    </div>
  );
}
