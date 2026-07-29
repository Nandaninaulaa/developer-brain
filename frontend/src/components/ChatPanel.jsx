import { useState } from "react";
import { api } from "../api.js";
import { callNumber, fileName } from "../callNumber.js";

export default function ChatPanel() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  async function handleAsk(e) {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.ask(question.trim());
      setResult(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="chat-panel">
      <form className="ask-form" onSubmit={handleAsk}>
        <input
          placeholder="Ask about your code, e.g. 'How does authentication work?'"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          autoFocus
        />
        <button className="primary" type="submit" disabled={loading}>
          {loading ? <div className="spinner-small" /> : "Search"}
        </button>
      </form>

      {error && <div className="error fade-in">{error}</div>}

      {loading && (
        <div className="loading-overlay fade-in">
          <div className="spinner"></div>
          <p>Consulting your brain...</p>
        </div>
      )}

      {result && !loading && (
        <div className="results-container">
          <div className="card answer-card fade-in">
            <div className="card-tag">
              <span className="call-number">RESPONSE</span>
              <span className="call-label">{result.sources?.length || 0} sources cited</span>
            </div>
            <div className="card-body main-answer">{result.answer}</div>
          </div>

          <h3 className="section-title">Supporting Evidence</h3>
          <div className="sources-grid">
            {result.sources?.map((s, i) => (
              <div className="card source-card fade-in" key={i} style={{ animationDelay: `${i * 100}ms` }}>
                <div className="card-tag">
                  <span className="call-number">{callNumber(s.source_path)}</span>
                  <span className="call-label">
                    {fileName(s.source_path)}
                    {s.symbol ? ` · ${s.symbol}` : ""}
                  </span>
                </div>
                <div className="card-body code-snippet">{s.text}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!result && !loading && (
        <div className="empty fade-in">
          <div className="empty-icon">🧠</div>
          <p>Your brain is ready. Ask anything about your indexed projects.</p>
        </div>
      )}

      <style>{`
        .section-title {
          font-family: var(--font-mono);
          font-size: 0.8rem;
          text-transform: uppercase;
          color: var(--text-secondary);
          margin: 2rem 0 1rem;
          letter-spacing: 0.1em;
        }
        .main-answer {
          font-size: 1.1rem;
          color: var(--text-primary);
        }
        .code-snippet {
          font-family: var(--font-mono);
          font-size: 0.8rem;
          color: var(--text-secondary);
          background: rgba(0,0,0,0.2);
          padding: 0.75rem;
          border-radius: 4px;
          overflow-x: auto;
        }
        .empty {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 4rem 2rem;
          border: 1px dashed var(--border-color);
          border-radius: 12px;
          color: var(--text-secondary);
        }
        .empty-icon {
          font-size: 3rem;
          margin-bottom: 1rem;
          opacity: 0.5;
        }
        .spinner-small {
          width: 16px;
          height: 16px;
          border: 2px solid rgba(255,255,255,0.3);
          border-top-color: white;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }
      `}</style>
    </div>
  );
}
