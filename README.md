# Developer Brain — Personal Mode MVP

An AI-powered knowledge system for your own code and notes: ingest a project
folder, ask natural-language questions grounded in your content, and
auto-generate flashcards for interview prep.

This implements **Phase 0–4 of the build plan** end-to-end:
ingestion → chunking → embeddings → vector storage (Chroma) → RAG Q&A →
flashcards → a React frontend. It runs with **zero API cost by default**
(local embeddings + retrieval-only Q&A) and upgrades automatically once you
add an OpenAI key.

## Structure

```
developer-brain/
  backend/
    app/
      config.py        # all settings, env-var driven
      chunking.py       # code/doc chunking (Phase 1)
      file_readers.py   # text + PDF extraction
      embeddings.py      # local (sentence-transformers) or OpenAI
      vectorstore.py     # ChromaDB wrapper
      ingest.py          # Phase 1: walks a folder, chunks, embeds, stores
      qa.py               # Phase 2: RAG retrieval + answer generation
      flashcards.py       # flashcard auto-generation (LLM or heuristic)
      main.py             # FastAPI app (Phase 2/4 API layer)
    requirements.txt
    .env.example
  frontend/
    src/
      App.jsx, components/  # Ask / Flashcards / Ingest tabs (Phase 4)
    package.json
    vite.config.js
```

## Backend setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # defaults work with zero config

uvicorn app.main:app --reload --port 8000
```

The first request that generates embeddings will download the local model
(`all-MiniLM-L6-v2`, ~80MB) from Hugging Face — needs internet once, then it's
cached locally.

### Ingest a folder (CLI)

```bash
python -m app.ingest /path/to/your/project
```

Or use the `/ingest` API endpoint / the frontend's "Ingest" tab.

### Ask a question (CLI-free, via API)

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How does the retry logic work in the payment service?"}'
```

Without an OpenAI key, this returns the top-k most relevant chunks
(retrieval-only mode) instead of a generated answer — still useful, zero cost.

### Turn on real LLM answers + flashcards

In `.env`:

```
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

Optionally also switch `EMBEDDING_PROVIDER=openai` for higher-quality
retrieval (uses `text-embedding-3-small`).

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Opens on `http://localhost:5173`, proxying `/api/*` to the backend on
`:8000` (see `vite.config.js`). Three tabs: **Ask** (chat + sources),
**Flashcards** (click to reveal), **Ingest** (point at a folder, see stats).

## What's implemented vs. the original plan

| Phase | Status |
|---|---|
| 0 — Scope MVP | Done — this is the MVP |
| 1 — Ingestion & storage | Done — folder walk, code/doc-aware chunking, Chroma + metadata |
| 2 — RAG Q&A | Done — retrieval + grounded answers with sources, graceful no-LLM fallback |
| Flashcards | Done — LLM-generated when a key is present, heuristic fallback otherwise |
| 3 — Knowledge graph (Neo4j) | Done — concept extraction + `/graph` endpoints + force-directed view |
| 4 — Frontend | Done — Ask / Flashcards / Graph / Ingest tabs |
| 5 — Deployment (Docker) | Done — one-command `docker compose up` for backend + frontend + Neo4j |
| 6 — Team mode (stretch) | Not yet built |

## Knowledge graph (Phase 3)

`app/graph.py` extracts concepts from your ingested chunks and writes them
into Neo4j as `(Concept)-[:USED_IN]->(File)` relationships.

- **With an LLM configured**: asks the model to name 1-5 concepts per chunk
  (e.g. "JWT authentication", "BMR calculation") — richer, more meaningful
  nodes.
- **Without one**: falls back to the function/class symbol names already
  captured during chunking (e.g. `loginUser`, `calculate_bmr`) — works with
  zero API cost, just less semantically grouped.

Usage: ingest a folder first, then in the **Graph** tab click "Build graph
from ingested content", then "Refresh" to see the force-directed view
(orange = concepts, blue = files). "Clear graph" wipes it via `DETACH DELETE`
so you can rebuild cleanly after ingesting something new.

API: `POST /graph/build` (extracts + writes edges), `GET /graph` (nodes +
edges as JSON), `DELETE /graph` (wipes it).

Needs a running Neo4j instance — either via `docker-compose` (below) or a
local install, with connection details in `backend/.env` (`NEO4J_URI`,
`NEO4J_USER`, `NEO4J_PASSWORD`).

## Docker (Phase 5)

One-command startup for the whole stack — backend, frontend, and Neo4j —
using `docker-compose.yml` at the project root.

```bash
cp .env.docker.example .env   # set HOST_PROJECTS_DIR and optionally an OpenAI key
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Neo4j browser (optional, for poking at the graph directly): http://localhost:7474

**Ingesting from inside Docker**: the backend container mounts
`HOST_PROJECTS_DIR` (from your root `.env`) read-only at `/host-projects`.
So if `HOST_PROJECTS_DIR=C:/Users/nanda/Downloads` and your project is at
`C:/Users/nanda/Downloads/front end/nutritacker`, use
`/host-projects/front end/nutritacker` as the folder path in the Ingest tab
— not the Windows path.

Data persists across restarts via named volumes (`chroma_data`, `neo4j_data`)
— `docker compose down` keeps them, `docker compose down -v` wipes them.

To turn on real LLM answers/flashcards/concepts in Docker, set
`OPENAI_API_KEY` in the root `.env` before `docker compose up` (no need to
touch `backend/.env` — compose injects it into the backend container).

## Suggested next steps

1. **Team mode (Phase 6)**: multi-user auth, ingest a GitHub repo's commit
   history/PRs instead of just local files, auto-draft ADRs, basic static
   impact analysis (which files reference a changed file).
2. **Prerequisite edges in the graph**: currently the graph only models
   `concept -> used_in -> file`. Add `concept -> prerequisite_of -> concept`
   edges (the LLM path in `graph.py` is set up to be extended for this) so
   the concept map shows a learning order, not just a usage map.
3. **Keep ingesting real projects**: run ingestion against more of your
   repos (Cloudburst, the store-rating platform, etc.) so the tool's actual
   knowledge base — and your flashcard deck — grows over time.

## Notes on what was tested

The ingestion → chunking → embedding → Chroma storage → retrieval →
flashcard-generation pipeline was smoke-tested end-to-end in this
environment (chunking correctly split code files by function/class,
Q&A retrieval returned relevant sources, flashcard generation produced
valid cards). Live download of the sentence-transformers model and live
calls to the OpenAI API were **not** exercised here since this sandbox has
no internet access to Hugging Face or OpenAI — both are standard calls
that will work on your machine once you run `pip install` and start the
server locally.
