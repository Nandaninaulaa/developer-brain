import { useEffect, useState } from "react";
import { api } from "./api.js";
import IngestPanel from "./components/IngestPanel.jsx";
import ChatPanel from "./components/ChatPanel.jsx";
import FlashcardsPanel from "./components/FlashcardsPanel.jsx";
import GraphPanel from "./components/GraphPanel.jsx";

const TABS = [
  { id: "ask", idx: "01", label: "Ask", icon: "💬" },
  { id: "flashcards", idx: "02", label: "Flashcards", icon: "🗂️" },
  { id: "graph", idx: "03", label: "Graph", icon: "🕸️" },
  { id: "ingest", idx: "04", label: "Ingest", icon: "📥" },
];

const TAB_META = {
  ask: {
    title: "Ask your Brain",
    sub: "Query your indexed code and notes in plain English.",
  },
  flashcards: {
    title: "Study Cards",
    sub: "Auto-generated flashcards for interview and concept review.",
  },
  graph: {
    title: "Knowledge Map",
    sub: "Visualize how concepts and files connect in your project.",
  },
  ingest: {
    title: "Ingest Content",
    sub: "Add new projects or notes to your knowledge base.",
  },
};

export default function App() {
  const [tab, setTab] = useState("ask");
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  async function refreshStats() {
    try {
      const data = await api.stats();
      setStats(data);
    } catch (err) {
      console.error("Failed to fetch stats", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refreshStats();
  }, []);

  const meta = TAB_META[tab];

  return (
    <div className="shell">
      <aside className="drawer">
        <button className="drawer-brand" onClick={() => setTab("ask")}>
          <div className="mark">
            Developer<span className="mark-accent">Brain</span>
          </div>
          <div className="sub">Personal AI Knowledge Base</div>
        </button>
        <nav className="drawer-tabs">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={`drawer-tab ${tab === t.id ? "active" : ""}`}
              onClick={() => setTab(t.id)}
            >
              <span className="idx">{t.icon}</span>
              {t.label}
              <span className="tab-arrow">→</span>
            </button>
          ))}
        </nav>
        <div className={`drawer-footer status-${loading ? "connecting" : stats ? "online" : "offline"}`}>
          <span className="status-dot" />
          {loading ? (
            <span className="pulse">Connecting...</span>
          ) : stats ? (
            <>
              <span className="count">{stats.count}</span> chunks indexed
            </>
          ) : (
            "Backend offline"
          )}
        </div>
      </aside>

      <main className="desk">
        <div className="desk-header fade-in" key={tab}>
          <h1>{meta.title}</h1>
          <p>{meta.sub}</p>
        </div>

        <div className="content-area fade-in" key={`${tab}-content`}>
          {tab === "ask" && <ChatPanel />}
          {tab === "flashcards" && <FlashcardsPanel />}
          {tab === "graph" && <GraphPanel />}
          {tab === "ingest" && (
            <IngestPanel stats={stats} onIngested={refreshStats} />
          )}
        </div>
      </main>
      
      <style>{`
        .pulse {
          animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.5; }
          100% { opacity: 1; }
        }
        .content-area {
          min-height: 400px;
        }
      `}</style>
    </div>
  );
}
