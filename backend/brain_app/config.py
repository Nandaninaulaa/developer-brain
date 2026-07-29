"""
Central configuration for Developer Brain (personal mode MVP).
All values are overridable via environment variables / .env file.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Paths -------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", BASE_DIR / "data" / "chroma"))
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# --- Ingestion -----------------------------------------------------------
# File types the ingestion pipeline will walk and read.
INGEST_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".md", ".txt", ".pdf"}

# Chunking targets (in characters, not tokens — good enough for MVP)
CODE_CHUNK_MAX_CHARS = 1500
DOC_CHUNK_MAX_CHARS = 1000
CHUNK_OVERLAP_CHARS = 150

# --- Embeddings ----------------------------------------------------------
# "local" uses fastembed — a lightweight, torch-free ONNX runtime (free,
# no API key, and small enough to run on memory-constrained free-tier
# hosting, unlike sentence-transformers/torch which needs much more RAM).
# "openai" uses OpenAI's embedding API (better quality, needs OPENAI_API_KEY).
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local")
LOCAL_EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# --- LLM (for Q&A answer generation, Phase 2) -----------------------------
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # "openai" or "none" (retrieval-only)
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# --- Retrieval -------------------------------------------------------------
TOP_K = int(os.getenv("TOP_K", 5))

# --- Collection name in Chroma --------------------------------------------
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "developer_brain")

# --- Knowledge graph (Phase 3) ---------------------------------------------
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "devbrain123")
