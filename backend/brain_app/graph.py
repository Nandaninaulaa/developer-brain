"""
Phase 3: Knowledge graph layer.

Extracts concepts from stored chunks and writes a graph into Neo4j:
    (:Concept {name}) -[:USED_IN]-> (:File {path})
    (:Concept {name}) -[:PREREQUISITE_OF]-> (:Concept {name})

Two extraction modes:
- LLM mode (if OPENAI_API_KEY is set): asks the model to pull out named
  concepts/technologies per chunk and, optionally, prerequisite relationships.
- Heuristic mode (no key): falls back to function/class symbol names already
  captured during chunking, so the graph still populates with zero API cost
  (concept = symbol, relationship = used_in only, no prerequisite edges).
"""
import json
import re
from functools import lru_cache

from neo4j import GraphDatabase

from . import config
from .vectorstore import get_collection

CONCEPT_EXTRACTION_PROMPT = (
    "Extract the key technical concepts, technologies, or named components "
    "discussed in this code/doc chunk (e.g. 'JWT authentication', 'BMR "
    "calculation', 'REST endpoint', 'React hook'). Return ONLY a JSON array "
    "of 1-5 short concept name strings, nothing else.\n\nChunk:\n{content}"
)

_WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")


@lru_cache(maxsize=1)
def get_driver():
    return GraphDatabase.driver(
        config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )


def close_driver():
    get_driver().close()


def _ensure_constraints(tx):
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE")


def _write_edges(tx, concepts: list[str], source_path: str):
    for concept in concepts:
        tx.run(
            """
            MERGE (c:Concept {name: $concept})
            MERGE (f:File {path: $path})
            MERGE (c)-[:USED_IN]->(f)
            """,
            concept=concept,
            path=source_path,
        )


def _heuristic_concepts(text: str, symbol: str | None) -> list[str]:
    if symbol and symbol != "<module_header>":
        # Pull the identifier out of a signature like "def foo(...)" or
        # "const foo = (...) =>" and title-case it into a readable concept.
        match = re.search(r"(?:def|class|function)\s+(\w+)|const\s+(\w+)", symbol)
        if match:
            name = match.group(1) or match.group(2)
            return [name]
    return []


def _llm_concepts(text: str) -> list[str] | None:
    if config.LLM_PROVIDER != "openai" or not config.OPENAI_API_KEY:
        return None

    from openai import OpenAI
    client = OpenAI(api_key=config.OPENAI_API_KEY)

    prompt = CONCEPT_EXTRACTION_PROMPT.format(content=text[:1200])
    resp = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    raw = resp.choices[0].message.content.strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        concepts = json.loads(raw)
        return [c for c in concepts if isinstance(c, str)][:5]
    except json.JSONDecodeError:
        return None


def build_graph(limit: int = 200) -> dict:
    """Read up to `limit` stored chunks, extract concepts, write graph edges."""
    collection = get_collection()
    total = collection.count()
    if total == 0:
        return {"chunks_processed": 0, "concepts_written": 0, "note": "No chunks ingested yet."}

    fetch_n = min(total, limit)
    result = collection.get(limit=fetch_n, include=["documents", "metadatas"])

    driver = get_driver()
    with driver.session() as session:
        session.execute_write(_ensure_constraints)

        chunks_processed = 0
        all_concepts_written = set()

        for text, meta in zip(result["documents"], result["metadatas"]):
            source_path = meta.get("source_path", "unknown")
            symbol = meta.get("symbol")

            concepts = _llm_concepts(text)
            if concepts is None:
                concepts = _heuristic_concepts(text, symbol)

            if concepts:
                session.execute_write(_write_edges, concepts, source_path)
                all_concepts_written.update(concepts)

            chunks_processed += 1

    return {
        "chunks_processed": chunks_processed,
        "concepts_written": len(all_concepts_written),
    }


def get_graph_data(limit: int = 300) -> dict:
    """Return nodes + edges in a shape the frontend can render directly."""
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (c:Concept)-[r:USED_IN]->(f:File)
            RETURN c.name AS concept, f.path AS file
            LIMIT $limit
            """,
            limit=limit,
        )
        records = list(result)

    nodes = {}
    edges = []
    for rec in records:
        concept_id = f"concept:{rec['concept']}"
        file_id = f"file:{rec['file']}"
        if concept_id not in nodes:
            nodes[concept_id] = {"id": concept_id, "label": rec["concept"], "type": "concept"}
        if file_id not in nodes:
            # Show just the filename, not the full path, for readability.
            short_name = rec["file"].split("\\")[-1].split("/")[-1]
            nodes[file_id] = {"id": file_id, "label": short_name, "type": "file"}
        edges.append({"source": concept_id, "target": file_id})

    return {"nodes": list(nodes.values()), "edges": edges}


def clear_graph():
    driver = get_driver()
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
