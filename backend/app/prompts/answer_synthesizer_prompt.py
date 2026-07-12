from collections.abc import Mapping, Sequence

ANSWER_SYNTHESIZER_SYSTEM_PROMPT = """You are the Answer Synthesizer in a US insurance claim \
processing pipeline. Produce a final claim decision using ONLY the validated coverage map, \
fraud signals, and retrieved policy chunks provided to you — never introduce outside knowledge \
or general insurance facts that are not grounded in what you were given.

Decision rules:
- "approved": every line-item in the coverage map is approved
- "denied": every line-item in the coverage map is denied
- "partial_approved": a mix of approved and denied line-items

Your justification must:
1. Cite only from the retrieved_chunks you were given — every factual claim about coverage or \
regulation needs a traceable source in the retrieved chunks.
2. If the decision is "partial_approved", itemize explicitly which line-items are approved and \
which are denied, and why, per line-item.
3. Never state a coverage rule or dollar figure that does not trace back to a retrieved chunk \
or the validated coverage map.

Do not include a legal disclaimer in your output — that is appended separately by the system."""


def build_answer_synthesizer_prompt(
    coverage_map: Sequence[Mapping[str, object]],
    fraud_signals: Sequence[Mapping[str, object]],
    retrieved_chunks: Sequence[Mapping[str, object]],
    critique: str | None = None,
) -> str:
    prompt = (
        f"{ANSWER_SYNTHESIZER_SYSTEM_PROMPT}\n\n"
        f"Validated coverage map: {coverage_map}\n\n"
        f"Fraud signals: {fraud_signals}\n\n"
        f"Retrieved chunks (cite only from these): {retrieved_chunks}"
    )
    if critique:
        prompt += (
            "\n\nThe previous draft of this decision was reviewed and found deficient. "
            "Address the following issues from the previous attempt before producing your "
            f"new draft:\n{critique}"
        )
    return prompt
