import { useState, useRef, useEffect } from "react";
import "./App.css";

const API_BASE = "http://localhost:8000/api/v1";
const RUNNING_STATUSES = ["submitting", "pending", "started", "processing", "retry"];
const STATUS_TITLES = { success: "Analysis complete", failure: "Analysis failed" };
const SEVERITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3 };

const parseRepo = (input) => {
  const trimmed = input.trim();
  if (!trimmed.includes("github.com")) return trimmed;
  const parts = trimmed.split("github.com/")[1]?.split("/") ?? [];
  return parts.length >= 2 ? `${parts[0]}/${parts[1]}` : trimmed;
};

const scoreTone = (score) => (score >= 80 ? "good" : score >= 60 ? "warn" : "bad");

const bySeverity = (a, b) =>
  (SEVERITY_ORDER[a.severity] ?? 9) - (SEVERITY_ORDER[b.severity] ?? 9);

function App() {
  const [repoUrl, setRepoUrl] = useState("");
  const [prNumber, setPrNumber] = useState("");
  const [githubToken, setGithubToken] = useState("");
  const [taskId, setTaskId] = useState(null);
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const pollRef = useRef(null);
  const isRunning = RUNNING_STATUSES.includes(status);

  useEffect(() => () => clearInterval(pollRef.current), []);

  const fetchResults = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/results/${id}`);
      if (!res.ok) {
        setError(`Could not load results (${res.status})`);
        return;
      }
      setResults(await res.json());
    } catch (e) {
      setError(`Could not load results: ${e.message}`);
    }
  };

  const startPolling = (id) => {
    clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/status/${id}`);
        if (!res.ok) return;
        const data = await res.json();
        setStatus(data.status);
        setProgress(data.progress || 0);
        setStatusMessage(data.message || "");
        setError(data.error || null);
        if (data.status === "success") {
          clearInterval(pollRef.current);
          fetchResults(id);
        }
        if (data.status === "failure") clearInterval(pollRef.current);
      } catch (e) {
        console.error("Poll error:", e);
      }
    }, 2000);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const repo = parseRepo(repoUrl);
    if (!repo || !prNumber) {
      setError("Enter a repository (owner/repo or GitHub URL) and a PR number.");
      return;
    }
    setStatus("submitting");
    setProgress(0);
    setStatusMessage("Submitting analysis request…");
    setError(null);
    setResults(null);
    setTaskId(null);

    try {
      const response = await fetch(`${API_BASE}/analyze-pr`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repo,
          pr_number: Number(prNumber),
          github_token: githubToken || null,
        }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        const detail = body?.detail;
        throw new Error(
          Array.isArray(detail) ? detail.map((d) => d.msg).join("; ") : detail || `HTTP ${response.status}`
        );
      }
      const data = await response.json();
      setTaskId(data.task_id);
      setStatus(data.status);
      setStatusMessage(data.message);
      startPolling(data.task_id);
    } catch (e) {
      setError(e.message);
      setStatus(null);
    }
  };

  const issues = results ? [...results.issues].sort(bySeverity) : [];

  return (
    <div className="app">
      <header className="hero">
        <div className="brand-mark">{"</>"}</div>
        <div>
          <h1>AI Code Review</h1>
          <p>Local pull request analysis · Ollama llama3</p>
        </div>
      </header>

      <form className="card form-card" onSubmit={handleSubmit}>
        <div className="form-grid">
          <label className="field field-wide">
            <span>Repository</span>
            <input
              placeholder="owner/repo or https://github.com/owner/repo"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              disabled={isRunning}
            />
          </label>
          <label className="field">
            <span>PR number</span>
            <input
              type="number"
              min="1"
              placeholder="42"
              value={prNumber}
              onChange={(e) => setPrNumber(e.target.value)}
              disabled={isRunning}
            />
          </label>
          <label className="field">
            <span>GitHub token <em>optional</em></span>
            <input
              type="password"
              placeholder="ghp_…"
              autoComplete="off"
              value={githubToken}
              onChange={(e) => setGithubToken(e.target.value)}
              disabled={isRunning}
            />
          </label>
        </div>
        <button type="submit" className="primary" disabled={isRunning}>
          {isRunning ? <><span className="spinner" /> Analyzing…</> : "Analyze PR"}
        </button>
      </form>

      {error && (
        <div className="alert" role="alert">
          <strong>Error</strong>
          <span>{error}</span>
        </div>
      )}

      {taskId && (
        <section className={`card status-card status-${status}`}>
          <div className="status-row">
            <h2>{STATUS_TITLES[status] ?? "Analysis in progress"}</h2>
            <span className={`pill pill-${status}`}>{status}</span>
          </div>
          <div className="progress" aria-valuenow={progress} role="progressbar">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
          <p className="muted">{progress}% · {statusMessage}</p>
        </section>
      )}

      {results && (
        <section className="card results">
          <div className="pr-head">
            <h2>{results.pr_summary?.title || "Analysis results"}</h2>
            <p className="muted">
              by <strong>{results.pr_summary?.author}</strong>
              <span className="dot" />
              {results.pr_summary?.files_changed} file{results.pr_summary?.files_changed === 1 ? "" : "s"} changed
              <span className="dot" />
              <span className="add">+{results.pr_summary?.additions}</span>{" "}
              <span className="del">−{results.pr_summary?.deletions}</span>
            </p>
          </div>

          <div className="overview">
            <div className={`score score-${scoreTone(results.overall_score)}`}>
              <span className="score-value">{Math.round(results.overall_score)}</span>
              <span className="score-label">Quality score</span>
            </div>
            <div className="overview-text">
              <h3>Summary</h3>
              <p>{results.summary}</p>
            </div>
          </div>

          {results.recommendations?.length > 0 && (
            <div className="block">
              <h3>Recommendations</h3>
              <ol className="recommendations">
                {results.recommendations.map((rec, idx) => (
                  <li key={idx}>{rec}</li>
                ))}
              </ol>
            </div>
          )}

          <div className="block">
            <h3>
              Issues <span className="count">{issues.length}</span>
            </h3>
            {issues.length === 0 ? (
              <p className="empty">No issues found in this pull request.</p>
            ) : (
              <ul className="issues">
                {issues.map((issue, idx) => (
                  <li key={idx} className={`issue severity-${issue.severity}`}>
                    <div className="issue-tags">
                      <span className="pill pill-severity">{issue.severity}</span>
                      <span className="pill pill-category">{issue.category}</span>
                      {issue.file_path && (
                        <code className="path">
                          {issue.file_path}
                          {issue.line_number ? `:${issue.line_number}` : ""}
                        </code>
                      )}
                    </div>
                    <h4>{issue.title}</h4>
                    <p>{issue.description}</p>
                    {issue.suggestion && (
                      <p className="suggestion">
                        <strong>Suggestion</strong> {issue.suggestion}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <footer className="meta">
            <span>Analyzed {new Date(results.analyzed_at).toLocaleString()}</span>
            <span>{results.processing_time?.toFixed(1)}s processing</span>
            <code>{taskId}</code>
          </footer>
        </section>
      )}
    </div>
  );
}

export default App;
