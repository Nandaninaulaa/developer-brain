const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  stats: () => request("/stats"),
  ingest: (folder) =>
    request("/ingest", { method: "POST", body: JSON.stringify({ folder }) }),
  ingestUpload: (formData) =>
    fetch("/api/ingest-upload", { method: "POST", body: formData }).then(res => {
      if (!res.ok) return res.json().then(b => { throw new Error(b.detail || "Upload failed") });
      return res.json();
    }),
  ask: (question, top_k) =>
    request("/ask", { method: "POST", body: JSON.stringify({ question, top_k }) }),
  flashcards: (n = 5) => request(`/flashcards?n=${n}`),
  buildGraph: (limit = 200) =>
    request("/graph/build", { method: "POST", body: JSON.stringify({ limit }) }),
  getGraph: (limit = 300) => request(`/graph?limit=${limit}`),
  clearGraph: () => request("/graph/clear", { method: "DELETE" }),
};
