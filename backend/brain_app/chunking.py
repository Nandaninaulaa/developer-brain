"""
Chunking strategy:
- Code files (.py/.js/.ts/...) are split on top-level function/class boundaries
  using a lightweight regex heuristic (no full AST parsing needed for MVP).
- Doc files (.md/.txt) are split on blank-line paragraph boundaries.
- PDFs are split the same way as docs, after text extraction.

Every chunk that's still too long gets hard-wrapped with overlap so nothing
blows past the embedding model's context window.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import config


@dataclass
class Chunk:
    text: str
    source_path: str
    chunk_type: str          # "code" | "doc"
    symbol: str | None = None  # function/class name if known
    start_line: int | None = None
    metadata: dict = field(default_factory=dict)


# Matches top-level "def foo(...)" / "class Foo" (Python) and
# "function foo(...)" / "const foo = (...) =>" / "class Foo" (JS/TS).
_CODE_SPLIT_RE = re.compile(
    r"""^(
        (async\s+)?def\s+\w+\(.*\):|          # python def
        class\s+\w+.*:|                       # python class
        (export\s+)?(default\s+)?function\s+\w*\(.*\)\s*{|  # js function
        (export\s+)?(const|let|var)\s+\w+\s*=\s*(async\s*)?\(.*\)\s*=>|  # js arrow fn
        (export\s+)?class\s+\w+.*{                          # js/ts class
    )""",
    re.MULTILINE | re.VERBOSE,
)


def _hard_wrap(text: str, max_chars: int, overlap: int) -> list[str]:
    """Fallback splitter for chunks that are still too big."""
    if len(text) <= max_chars:
        return [text]
    pieces = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        pieces.append(text[start:end])
        start = end - overlap if end < len(text) else end
    return pieces


def chunk_code(text: str, source_path: str) -> list[Chunk]:
    matches = list(_CODE_SPLIT_RE.finditer(text))
    chunks: list[Chunk] = []

    if not matches:
        # No recognizable function/class boundaries — hard-wrap the whole file.
        for piece in _hard_wrap(text, config.CODE_CHUNK_MAX_CHARS, config.CHUNK_OVERLAP_CHARS):
            chunks.append(Chunk(text=piece, source_path=source_path, chunk_type="code"))
        return chunks

    # Anything before the first match (imports, module docstring) becomes its own chunk.
    if matches[0].start() > 0:
        preamble = text[: matches[0].start()].strip()
        if preamble:
            chunks.append(Chunk(text=preamble, source_path=source_path, chunk_type="code", symbol="<module_header>"))

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if not body:
            continue
        symbol_line = match.group(0).splitlines()[0].strip()
        for piece in _hard_wrap(body, config.CODE_CHUNK_MAX_CHARS, config.CHUNK_OVERLAP_CHARS):
            start_line = text[:start].count("\n") + 1
            chunks.append(
                Chunk(text=piece, source_path=source_path, chunk_type="code",
                      symbol=symbol_line, start_line=start_line)
            )
    return chunks


def chunk_doc(text: str, source_path: str) -> list[Chunk]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[Chunk] = []
    buffer = ""

    for para in paragraphs:
        candidate = f"{buffer}\n\n{para}".strip() if buffer else para
        if len(candidate) > config.DOC_CHUNK_MAX_CHARS and buffer:
            chunks.append(Chunk(text=buffer, source_path=source_path, chunk_type="doc"))
            buffer = para
        else:
            buffer = candidate

    if buffer:
        chunks.append(Chunk(text=buffer, source_path=source_path, chunk_type="doc"))

    # Safety net for any single paragraph that's still huge.
    final: list[Chunk] = []
    for c in chunks:
        for piece in _hard_wrap(c.text, config.DOC_CHUNK_MAX_CHARS, config.CHUNK_OVERLAP_CHARS):
            final.append(Chunk(text=piece, source_path=c.source_path, chunk_type=c.chunk_type))
    return final


def chunk_file(path: Path, text: str) -> list[Chunk]:
    if path.suffix in {".py", ".js", ".jsx", ".ts", ".tsx"}:
        return chunk_code(text, str(path))
    return chunk_doc(text, str(path))
