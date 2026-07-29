// Deterministic, purely cosmetic "call number" derived from a file path —
// gives every card a stable catalog-style stamp (e.g. "JS·047") without
// needing anything from the backend.
export function callNumber(path) {
  if (!path) return "—";
  const ext = (path.split(".").pop() || "").slice(0, 3).toUpperCase();
  let hash = 0;
  for (let i = 0; i < path.length; i++) {
    hash = (hash * 31 + path.charCodeAt(i)) >>> 0;
  }
  const num = (hash % 900) + 100; // 3-digit stamp
  return `${ext || "DOC"}·${num}`;
}

export function fileName(path) {
  if (!path) return "unknown";
  return path.split("\\").pop().split("/").pop();
}
