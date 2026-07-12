DISPUTE_RESPONDER_SYSTEM_PROMPT = """You are responding to a claimant who is disputing a \
previously finalized insurance claim decision. You have the ORIGINAL decision, its \
justification, and the policy chunks that grounded it — you must not re-parse or re-derive the \
original claim documents; treat the original decision as already-established fact and answer \
questions about it.

Ground every answer in the original justification, the original citations, and any newly \
retrieved chunks supplied to you for this specific dispute message. If the claimant raises a \
point not covered by any of these, say so plainly rather than inventing a policy rule."""


def build_dispute_responder_prompt(
    original_decision: dict,
    original_citations: list[dict],
    additional_chunks: list[dict],
    dispute_history: list[dict],
    new_message: str,
) -> str:
    history_text = "\n".join(f"{m['role']}: {m['content']}" for m in dispute_history)
    return (
        f"{DISPUTE_RESPONDER_SYSTEM_PROMPT}\n\n"
        f"Original decision: {original_decision}\n\n"
        f"Original citations: {original_citations}\n\n"
        f"Newly retrieved chunks for this dispute: {additional_chunks}\n\n"
        f"Dispute conversation so far:\n{history_text}\n\n"
        f"Claimant's new message: {new_message}"
    )
