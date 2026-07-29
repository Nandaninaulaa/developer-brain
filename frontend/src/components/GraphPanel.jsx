import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";

const WIDTH = 900;
const HEIGHT = 500;

function layoutGraph(nodes, edges) {
  const positioned = nodes.map((n) => ({
    ...n,
    x: WIDTH / 2 + (Math.random() - 0.5) * 200,
    y: HEIGHT / 2 + (Math.random() - 0.5) * 200,
    vx: 0,
    vy: 0,
  }));
  const byId = Object.fromEntries(positioned.map((n) => [n.id, n]));

  const REPULSION = 2500;
  const SPRING = 0.03;
  const SPRING_LEN = 100;
  const DAMPING = 0.8;
  const STEPS = 250;

  for (let step = 0; step < STEPS; step++) {
    for (let i = 0; i < positioned.length; i++) {
      for (let j = i + 1; j < positioned.length; j++) {
        const a = positioned[i];
        const b = positioned[j];
        let dx = a.x - b.x;
        let dy = a.y - b.y;
        let dist2 = dx * dx + dy * dy || 0.01;
        const force = REPULSION / dist2;
        const dist = Math.sqrt(dist2);
        dx /= dist;
        dy /= dist;
        a.vx += dx * force;
        a.vy += dy * force;
        b.vx -= dx * force;
        b.vy -= dy * force;
      }
    }
    for (const e of edges) {
      const a = byId[e.source];
      const b = byId[e.target];
      if (!a || !b) continue;
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 0.01;
      const force = (dist - SPRING_LEN) * SPRING;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      a.vx += fx;
      a.vy += fy;
      b.vx -= fx;
      b.vy -= fy;
    }
    for (const n of positioned) {
      n.vx *= DAMPING;
      n.vy *= DAMPING;
      n.x += n.vx;
      n.y += n.vy;
      n.x = Math.min(WIDTH - 40, Math.max(40, n.x));
      n.y = Math.min(HEIGHT - 40, Math.max(40, n.y));
    }
  }
  return positioned;
}

export default function GraphPanel() {
  const [graph, setGraph] = useState(null);
  const [positioned, setPositioned] = useState([]);
  const [loading, setLoading] = useState(false);
  const [building, setBuilding] = useState(false);
  const [error, setError] = useState(null);
  const loadedOnce = useRef(false);

  async function loadGraph() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getGraph(300);
      setGraph(data);
      setPositioned(layoutGraph(data.nodes, data.edges));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleBuild() {
    setBuilding(true);
    setError(null);
    try {
      await api.buildGraph(200);
      await loadGraph();
    } catch (err) {
      setError(err.message);
    } finally {
      setBuilding(false);
    }
  }

  async function handleClear() {
    if (!window.confirm("Are you sure you want to clear the entire graph?")) return;
    setError(null);
    try {
      await api.clearGraph();
      setGraph(null);
      setPositioned([]);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    if (!loadedOnce.current) {
      loadedOnce.current = true;
      loadGraph();
    }
  }, []);

  const byId = Object.fromEntries(positioned.map((n) => [n.id, n]));

  return (
    <div className="graph-panel">
      <div className="panel-actions">
        <p className="panel-note">
          Visualize the connections between concepts and files in your project.
        </p>
        <div className="button-group">
          <button className="primary" onClick={handleBuild} disabled={building}>
            {building ? <div className="spinner-small" /> : "Build Graph"}
          </button>
          <button className="secondary" onClick={loadGraph} disabled={loading}>
            {loading ? "Loading..." : "Refresh"}
          </button>
          <button className="secondary danger" onClick={handleClear}>Clear</button>
        </div>
      </div>

      {error && <div className="error fade-in">{error}</div>}

      {loading && (
        <div className="loading-overlay fade-in">
          <div className="spinner"></div>
          <p>Rendering your knowledge map...</p>
        </div>
      )}

      {graph && graph.nodes.length === 0 && !loading && (
        <div className="empty fade-in">
          <div className="empty-icon">🕸️</div>
          <p>No graph data yet. Build the graph to see connections.</p>
        </div>
      )}

      {positioned.length > 0 && !loading && (
        <div className="graph-container fade-in">
          <div className="graph-frame">
            <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} preserveAspectRatio="xMidYMid meet">
              <defs>
                <filter id="glow">
                  <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
                  <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                  </feMerge>
                </filter>
              </defs>
              {graph.edges.map((e, i) => {
                const a = byId[e.source];
                const b = byId[e.target];
                if (!a || !b) return null;
                return (
                  <line
                    key={i}
                    x1={a.x}
                    y1={a.y}
                    x2={b.x}
                    y2={b.y}
                    stroke="rgba(88, 166, 255, 0.15)"
                    strokeWidth={1.5}
                  />
                );
              })}
              {positioned.map((n) => (
                <g key={n.id} transform={`translate(${n.x}, ${n.y})`} className="node">
                  <circle
                    r={n.type === "file" ? 10 : 7}
                    fill={n.type === "file" ? "#1f6feb" : "#f0883e"}
                    stroke="rgba(255,255,255,0.1)"
                    strokeWidth={2}
                    filter="url(#glow)"
                  />
                  <text
                    y={-18}
                    textAnchor="middle"
                    fontSize="11"
                    fontFamily="var(--font-mono)"
                    fill={n.type === "file" ? "#58a6ff" : "#ffa657"}
                    fontWeight="600"
                  >
                    {n.label.length > 25 ? n.label.slice(0, 22) + "..." : n.label}
                  </text>
                </g>
              ))}
            </svg>
          </div>
          
          <div className="graph-legend">
            <div className="legend-item">
              <span className="dot" style={{ background: "#f0883e" }} />
              <span>{graph.nodes.filter((n) => n.type === "concept").length} Concepts</span>
            </div>
            <div className="legend-item">
              <span className="dot" style={{ background: "#1f6feb" }} />
              <span>{graph.nodes.filter((n) => n.type === "file").length} Files</span>
            </div>
            <div className="legend-item">
              <span className="link-icon">─</span>
              <span>{graph.edges.length} Connections</span>
            </div>
          </div>
        </div>
      )}

      <style>{`
        .graph-container {
          background: var(--bg-secondary);
          border-radius: 12px;
          border: 1px solid var(--border-color);
          overflow: hidden;
        }
        .graph-frame {
          background: radial-gradient(circle at center, #161b22 0%, #0d1117 100%);
          cursor: grab;
        }
        .graph-frame svg {
          width: 100%;
          height: auto;
          display: block;
        }
        .button-group {
          display: flex;
          gap: 0.5rem;
        }
        .danger:hover {
          color: var(--error) !important;
          border-color: var(--error) !important;
        }
        .node:hover circle {
          r: 12;
          stroke: white;
          transition: all 0.2s;
        }
        .graph-legend {
          display: flex;
          gap: 2rem;
          padding: 1rem 1.5rem;
          background: rgba(0,0,0,0.3);
          border-top: 1px solid var(--border-color);
          font-family: var(--font-mono);
          font-size: 0.8rem;
        }
        .legend-item {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          color: var(--text-secondary);
        }
        .dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
        }
        .link-icon {
          color: rgba(88, 166, 255, 0.4);
          font-weight: bold;
        }
      `}</style>
    </div>
  );
}
