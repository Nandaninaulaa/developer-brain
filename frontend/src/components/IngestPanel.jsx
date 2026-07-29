import { useState } from "react";
import { api } from "../api.js";

export default function IngestPanel({ onIngested, stats }) {
  const [folder, setFolder] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  async function handleIngest(e) {
    e.preventDefault();
    if (!folder.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.ingest(folder.trim());
      setResult(res);
      onIngested?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await api.ingestUpload(formData);
      setResult(res);
      onIngested?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      e.target.value = null; // reset input
    }
  }

  return (
    <div>
      <p className="panel-note">
        Ingest your project to build your developer brain. You can either point to a local folder (if running locally) or upload a <strong>.zip</strong> file of your project.
      </p>

      <div className="ingest-methods">
        <div className="ingest-method">
          <h3>Local Folder</h3>
          <form className="ingest-row" onSubmit={handleIngest}>
            <input
              placeholder="/path/to/your/project"
              value={folder}
              onChange={(e) => setFolder(e.target.value)}
            />
            <button className="primary" type="submit" disabled={loading}>
              {loading ? "Indexing…" : "Ingest"}
            </button>
          </form>
        </div>

        <div className="ingest-divider">OR</div>

        <div className="ingest-method">
          <h3>Upload ZIP</h3>
          <div className="upload-container">
            <input
              type="file"
              accept=".zip"
              onChange={handleFileUpload}
              disabled={loading}
              id="zip-upload"
              style={{ display: "none" }}
            />
            <label htmlFor="zip-upload" className={`button primary ${loading ? "disabled" : ""}`}>
              {loading ? "Uploading & Indexing…" : "Select .zip file"}
            </label>
          </div>
        </div>
      </div>

      {error && <div className="error" style={{ marginTop: "1rem" }}>{error}</div>}

      {result && (
        <div className="card" style={{ marginTop: "1rem" }}>
          <div className="card-tag">
            <span className="call-number">INDEXED</span>
            <span className="call-label">{result.seconds}s</span>
          </div>
          <div className="card-body">
            {result.files_ingested} files → {result.chunks_stored} chunks stored.
            {result.files_skipped_empty > 0 &&
              ` (${result.files_skipped_empty} empty files skipped.)`}
          </div>
        </div>
      )}

      {stats && (
        <div className="stats-line" style={{ marginTop: "1rem" }}>
          Collection "{stats.collection}" currently holds {stats.count} chunks.
        </div>
      )}
      
      <style>{`
        .ingest-methods {
          display: flex;
          align-items: center;
          gap: 2rem;
          background: #f9f9f9;
          padding: 1.5rem;
          border-radius: 8px;
          border: 1px solid #eee;
        }
        .ingest-method {
          flex: 1;
        }
        .ingest-method h3 {
          margin-top: 0;
          margin-bottom: 0.5rem;
          font-size: 0.9rem;
          color: #666;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
        .ingest-divider {
          font-weight: bold;
          color: #999;
        }
        .upload-container label.button {
          display: inline-block;
          cursor: pointer;
          padding: 0.6rem 1.2rem;
          border-radius: 4px;
          text-align: center;
        }
        .upload-container label.button.disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        @media (max-width: 600px) {
          .ingest-methods {
            flex-direction: column;
            gap: 1rem;
          }
          .ingest-divider {
            display: none;
          }
        }
      `}</style>
    </div>
  );
}
