"""
Phase 2: Retrieval + Q&A (RAG core).

qa(question) -> {
    "answer": str,
    "sources": [{"source_path": ..., "symbol": ..., "text": snippet}, ...]
}

If LLM_PROVIDER is "none" or no API key is configured, falls back to a
retrieval-only mode: returns the best-matching chunks without a generated
answer, so the pipeline is still demoable with zero API cost.
"""
from . import config
from .vectorstore import query as vector_query

SYSTEM_PROMPT = (
    "You are Developer Brain, an assistant that answers questions about the "
    "user's own codebase and notes. Answer ONLY using the provided context. "
    "If the context doesn't contain the answer, say so plainly instead of "
    "guessing. Cite which file each part of your answer comes from."
)


def _build_context_block(hits: list[dict]) -> str:
    parts = []
    for i, hit in enumerate(hits, start=1):
        meta = hit["metadata"]
        label = meta.get("source_path", "unknown")
        if meta.get("symbol"):
            label += f"  ({meta['symbol']})"
        parts.append(f"[{i}] {label}\n{hit['text']}")
    return "\n\n---\n\n".join(parts)


def _call_llm(question: str, context_block: str) -> str:
    if config.LLM_PROVIDER != "openai" or not config.OPENAI_API_KEY:
        return None  # signal fallback

    from openai import OpenAI
    client = OpenAI(api_key=config.OPENAI_API_KEY)

    resp = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n\n{context_block}\n\nQuestion: {question}"},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content


def qa(question: str, top_k: int | None = None) -> dict:
    hits = vector_query(question, top_k=top_k)

    if not hits:
        return {
            "answer": "No relevant content found. Have you run ingestion yet?",
            "sources": [],
        }

    context_block = _build_context_block(hits)
    answer = _call_llm(question, context_block)

    if answer is None:
        # Retrieval-only fallback — no LLM configured.
        answer = (
            "[Retrieval-only mode — no LLM configured] "
            "Here are the most relevant chunks for your question:"
        )

    sources = [
        {
            "source_path": h["metadata"].get("source_path"),
            "symbol": h["metadata"].get("symbol") or None,
            "text": h["text"][:300],
        }
        for h in hits
    ]

    return {"answer": answer, "sources": sources}
