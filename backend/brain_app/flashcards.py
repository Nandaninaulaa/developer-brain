"""
Auto-generates flashcards (Q&A pairs) from ingested content.

With an LLM configured: asks it to produce concept-level flashcards from a
sample of chunks. Without one: falls back to simple heuristic cards built
from function/class names and doc headings, so the feature still works with
zero API cost.
"""
import json
import random

from . import config
from .vectorstore import get_collection

FLASHCARD_PROMPT = (
    "You generate flashcards for a developer studying their own codebase and "
    "notes. Given the following content chunks, produce {n} flashcards as a "
    "JSON array of objects with 'question' and 'answer' fields. Focus on "
    "concepts, design decisions, and non-obvious logic — not trivial syntax. "
    "Return ONLY the JSON array, no other text.\n\nContent:\n\n{content}"
)


def _sample_chunks(n: int) -> list[dict]:
    collection = get_collection()
    total = collection.count()
    if total == 0:
        return []
    fetch_n = min(total, max(n * 4, 20))
    result = collection.get(limit=fetch_n, include=["documents", "metadatas"])
    docs = result["documents"]
    metas = result["metadatas"]
    combined = list(zip(docs, metas))
    random.shuffle(combined)
    return [{"text": d, "metadata": m} for d, m in combined[:fetch_n]]


def _heuristic_flashcards(chunks: list[dict], n: int) -> list[dict]:
    cards = []
    for c in chunks:
        symbol = c["metadata"].get("symbol")
        source = c["metadata"].get("source_path", "unknown")
        if symbol and symbol != "<module_header>":
            cards.append({
                "question": f"What does `{symbol}` do, and where is it defined?",
                "answer": f"Defined in {source}. Snippet:\n{c['text'][:200]}",
            })
        if len(cards) >= n:
            break
    return cards[:n]


def _llm_flashcards(chunks: list[dict], n: int) -> list[dict] | None:
    if config.LLM_PROVIDER != "openai" or not config.OPENAI_API_KEY:
        return None

    from openai import OpenAI
    client = OpenAI(api_key=config.OPENAI_API_KEY)

    content = "\n\n---\n\n".join(c["text"][:800] for c in chunks[: n * 2])
    prompt = FLASHCARD_PROMPT.format(n=n, content=content)

    resp = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )
    raw = resp.choices[0].message.content.strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        cards = json.loads(raw)
        return cards[:n]
    except json.JSONDecodeError:
        return None


def generate_flashcards(n: int = 5) -> list[dict]:
    chunks = _sample_chunks(n)
    if not chunks:
        return []

    cards = _llm_flashcards(chunks, n)
    if cards:
        return cards

    return _heuristic_flashcards(chunks, n)
