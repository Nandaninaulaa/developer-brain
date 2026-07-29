import { useState } from "react";
import { api } from "../api.js";

export default function FlashcardsPanel() {
  const [cards, setCards] = useState([]);
  const [revealed, setRevealed] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function loadCards() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.flashcards(6); // Load 6 for a better grid
      setCards(res.flashcards || []);
      setRevealed({});
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function toggle(i) {
    setRevealed((prev) => ({ ...prev, [i]: !prev[i] }));
  }

  return (
    <div className="flashcards-panel">
      <div className="panel-actions">
        <p className="panel-note">
          Test your knowledge! We've generated these cards based on your indexed code and documentation.
        </p>
        <button className="primary" onClick={loadCards} disabled={loading}>
          {loading ? <div className="spinner-small" /> : "Generate New Batch"}
        </button>
      </div>

      {error && <div className="error fade-in">{error}</div>}

      {loading && (
        <div className="loading-overlay fade-in">
          <div className="spinner"></div>
          <p>Drafting cards from your brain...</p>
        </div>
      )}

      <div className="flashcard-grid">
        {cards.length === 0 && !loading && (
          <div className="empty fade-in">
            <div className="empty-icon">🗂️</div>
            <p>No cards yet. Index some content and click "Generate" to start studying.</p>
          </div>
        )}
        {cards.map((c, i) => (
          <div
            key={i}
            className={`flashcard ${revealed[i] ? "revealed" : ""} fade-in`}
            style={{ animationDelay: `${i * 100}ms` }}
            onClick={() => toggle(i)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && toggle(i)}
          >
            <div className="flashcard-inner">
              <div className="flashcard-face front">
                <div className="eyebrow">QUESTION {i + 1}</div>
                <div className="content">{c.question}</div>
                <div className="flashcard-hint">Click to reveal answer</div>
              </div>
              <div className="flashcard-face back">
                <div className="eyebrow">ANSWER</div>
                <div className="content">{c.answer}</div>
                <div className="flashcard-hint">Click to flip back</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <style>{`
        .panel-actions {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 2rem;
          background: var(--bg-secondary);
          padding: 1.5rem;
          border-radius: 12px;
          border: 1px solid var(--border-color);
        }
        .panel-actions .panel-note {
          margin: 0;
          max-width: 60%;
        }
        .flashcard-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 1.5rem;
        }
        .flashcard {
          height: 220px;
          perspective: 1000px;
        }
        .flashcard-inner {
          position: relative;
          width: 100%;
          height: 100%;
          transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
          transform-style: preserve-3d;
          cursor: pointer;
        }
        .flashcard.revealed .flashcard-inner {
          transform: rotateY(180deg);
        }
        .flashcard-face {
          position: absolute;
          width: 100%;
          height: 100%;
          backface-visibility: hidden;
          display: flex;
          flex-direction: column;
          padding: 1.5rem;
          border-radius: 12px;
          background-color: var(--bg-secondary);
          border: 1px solid var(--border-color);
          box-shadow: var(--card-shadow);
        }
        .flashcard-face.back {
          transform: rotateY(180deg);
          background-color: var(--bg-tertiary);
          border-color: var(--accent-primary);
        }
        .flashcard-face .eyebrow {
          font-family: var(--font-mono);
          font-size: 0.7rem;
          text-transform: uppercase;
          color: var(--accent-primary);
          margin-bottom: 1rem;
          letter-spacing: 0.1em;
        }
        .flashcard-face .content {
          font-size: 1rem;
          font-weight: 500;
          line-height: 1.5;
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          text-align: center;
        }
        .flashcard-hint {
          font-family: var(--font-mono);
          font-size: 0.65rem;
          color: var(--text-secondary);
          text-transform: uppercase;
          margin-top: 1rem;
          text-align: center;
          opacity: 0.6;
        }
        .spinner-small {
          width: 16px;
          height: 16px;
          border: 2px solid rgba(255,255,255,0.3);
          border-top-color: white;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }
        @media (max-width: 600px) {
          .panel-actions {
            flex-direction: column;
            gap: 1rem;
            text-align: center;
          }
          .panel-actions .panel-note {
            max-width: 100%;
          }
        }
      `}</style>
    </div>
  );
}
