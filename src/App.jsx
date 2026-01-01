import { useState, useRef } from "react";
import "./App.css";

const API_BASE = "http://localhost:8000/api/v1";

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

  const parseRepo = (input) => {
    try {
      const trimmed = input.trim();
      if (!trimmed) return "";
      if (trimmed.includes("github.com")) {
        const parts = trimmed.split("github.com/")[1].split("/");
        if (parts.length >= 2) return `${parts[0]}/${parts[1]}`;
      }
      return trimmed;
    } catch (e) {
      return input;
    }
  };

  const startPolling = (id) => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/status/${id}`);
        if (!res.ok) {
          console.error("Status fetch failed");
          return;
        }
        const data = await res.json();
        setStatus(data.status);
        setProgress(data.progress || 0);
        setStatusMessage(data.message || "");
        setError(data.error || null);

        if (data.status === "success") {
          clearInterval(pollRef.current);
          setTimeout(() => fetchResults(id), 500);
        }

        if (data.status === "failure") {
          clearInterval(pollRef.current);
        }
      } catch (e) {
        console.error("Poll error:", e);
      }
    }, 2000);
  };

  const fetchResults = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/results/${id}`);
      if (!res.ok) {
        const text = await res.text();
        console.error("Results fetch failed:", text);
        return;
      }
      const data = await res.json();
      setResults(data);
    } catch (e) {
      console.error("Results error:", e);
    }
  };

  const handleSubmit = async () => {
    setStatus("submitting");
    setProgress(0);
    setStatusMessage("Submitting analysis request...");
    setError(null);
    setResults(null);
    
    const repo = parseRepo(repoUrl);
    if (!repo || !prNumber) {
      setError("Please provide repository (owner/repo or GitHub URL) and PR number.");
      setStatus(null);
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/analyze-pr`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          repo: repo,
          pr_number: Number(prNumber),
          github_token: githubToken || null,
        }),
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Request failed");
      }

      const data = await response.json();
      setTaskId(data.task_id);
      setStatus(data.status);
      setStatusMessage(data.message);
      startPolling(data.task_id);
    } catch (e) {
      console.error(e);
      setError("Failed to submit analysis request: " + e.message);
      setStatus(null);
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      critical: "#dc3545",
      high: "#fd7e14",
      medium: "#ffc107",
      low: "#28a745"
    };
    return colors[severity] || "#6c757d";
  };

  return (
    <div className="container">
      <header>
        <h1>🤖 AI Code Review Agent</h1>
        <p>Powered by Ollama llama3</p>
      </header>

      <div className="input-section">
        <div className="form-group">
          <label>GitHub Repository</label>
          <input
            placeholder="owner/repo or https://github.com/owner/repo"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            disabled={!!taskId}
          />
        </div>

        <div className="form-group">
          <label>PR Number</label>
          <input
            type="number"
            placeholder="1"
            value={prNumber}
            onChange={(e) => setPrNumber(e.target.value)}
            disabled={!!taskId}
          />
        </div>

        <div className="form-group">
          <label>GitHub Token (optional)</label>
          <input
            type="password"
            placeholder="ghp_..."
            value={githubToken}
            onChange={(e) => setGithubToken(e.target.value)}
            disabled={!!taskId}
          />
        </div>

        <button onClick={handleSubmit} disabled={!!taskId} className="submit-btn">
          Analyze PR
        </button>
      </div>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {taskId && (
        <div className="status-section">
          <div className="status-header">
            <h3>Analysis in Progress</h3>
            <code>{taskId}</code>
          </div>

          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }}></div>
          </div>
          <p className="progress-text">{progress}% - {statusMessage}</p>
        </div>
      )}

      {results && (
        <div className="results-section">
          <div className="pr-summary">
            <h2>{results.pr_summary?.title || "Analysis Results"}</h2>
            <div className="pr-stats">
              <div className="stat">
                <span className="label">Author:</span>
                <span>{results.pr_summary?.author}</span>
              </div>
              <div className="stat">
                <span className="label">Files Changed:</span>
                <span>{results.pr_summary?.files_changed}</span>
              </div>
              <div className="stat">
                <span className="label">Additions:</span>
                <span style={{ color: "#28a745" }}>+{results.pr_summary?.additions}</span>
              </div>
              <div className="stat">
                <span className="label">Deletions:</span>
                <span style={{ color: "#dc3545" }}>-{results.pr_summary?.deletions}</span>
              </div>
            </div>
          </div>

          <div className="score-card">
            <div className="score-circle">
              <span className="score-value">{results.overall_score}</span>
              <span className="score-label">Code Quality</span>
            </div>
          </div>

          <div className="summary-section">
            <h3>Summary</h3>
            <p>{results.summary}</p>
          </div>

          {results.recommendations && results.recommendations.length > 0 && (
            <div className="recommendations-section">
              <h3>Recommendations</h3>
              <ul>
                {results.recommendations.map((rec, idx) => (
                  <li key={idx}>{rec}</li>
                ))}
              </ul>
            </div>
          )}

          {results.issues && results.issues.length > 0 && (
            <div className="issues-section">
              <h3>Issues Found ({results.issues.length})</h3>
              <div className="issues-list">
                {results.issues.map((issue, idx) => (
                  <div key={idx} className="issue-card" style={{ borderLeftColor: getSeverityColor(issue.severity) }}>
                    <div className="issue-header">
                      <span className="severity" style={{ backgroundColor: getSeverityColor(issue.severity) }}>
                        {issue.severity.toUpperCase()}
                      </span>
                      <span className="category">{issue.category}</span>
                    </div>
                    <h4>{issue.title}</h4>
                    <p className="description">{issue.description}</p>
                    {issue.file_path && (
                      <p className="file-path">
                        <strong>File:</strong> {issue.file_path}
                        {issue.line_number && ` (Line ${issue.line_number})`}
                      </p>
                    )}
                    {issue.suggestion && (
                      <p className="suggestion">
                        <strong>Suggestion:</strong> {issue.suggestion}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {(!results.issues || results.issues.length === 0) && (
            <div className="no-issues">
              <p>✅ No issues found!</p>
            </div>
          )}

          <div className="metadata">
            <p>Analyzed at: {new Date(results.analyzed_at).toLocaleString()}</p>
            <p>Processing time: {results.processing_time?.toFixed(2)}s</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
