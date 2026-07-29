"""
Phase 1: Ingestion pipeline.

Usage (from backend/):
    python -m app.ingest /path/to/your/project

Walks the given folder, reads every file with a supported extension,
chunks it, embeds the chunks, and stores them (+ metadata) in ChromaDB.
"""
import sys
import time
from pathlib import Path

from . import config
from .chunking import chunk_file
from .file_readers import read_file_text
from .vectorstore import add_chunks, collection_stats

IGNORE_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", "data", ".chroma",
}


def iter_ingestible_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        if path.suffix not in config.INGEST_EXTENSIONS:
            continue
        yield path


def ingest_folder(folder: str) -> dict:
    root = Path(folder).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Folder not found: {root}")

    files = list(iter_ingestible_files(root))
    total_chunks = 0
    total_files = 0
    skipped = []
    start = time.time()

    for path in files:
        text = read_file_text(path)
        if not text.strip():
            skipped.append(str(path))
            continue
        chunks = chunk_file(path, text)
        stored = add_chunks(chunks)
        total_chunks += stored
        total_files += 1
        print(f"  ingested {path.relative_to(root)}  ({len(chunks)} chunks)")

    elapsed = round(time.time() - start, 2)
    summary = {
        "root": str(root),
        "files_ingested": total_files,
        "files_skipped_empty": len(skipped),
        "chunks_stored": total_chunks,
        "seconds": elapsed,
        "collection": collection_stats(),
    }
    return summary


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m app.ingest /path/to/folder")
        sys.exit(1)

    folder_arg = sys.argv[1]
    print(f"Ingesting {folder_arg} ...")
    result = ingest_folder(folder_arg)
    print("\nDone.")
    for k, v in result.items():
        print(f"  {k}: {v}")
