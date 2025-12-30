import { useState } from "react";

function App() {
  const [repoUrl, setRepoUrl] = useState("");
  const [prNumber, setPrNumber] = useState("");
  const [githubToken, setGithubToken] = useState("");
  const [taskId, setTaskId] = useState(null);
  const [status, setStatus] = useState(null);
  const [results, setResults] = useState(null);

  const handleSubmit = async () => {
    setStatus("submitting");

    const response = await fetch("http://localhost:8000/analyze-pr", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        repo_url: repoUrl,
        pr_number: Number(prNumber),
        github_token: githubToken || null,
      }),
    });

    const data = await response.json();
    setTaskId(data.task_id);
    setStatus(data.status);

    pollStatus(data.task_id);
  };


  return (
    <div style={{ padding: "20px", maxWidth: "600px" }}>
      <h2>AI Code Review Agent</h2>

      <input
        placeholder="GitHub Repo URL"
        value={repoUrl}
        onChange={(e) => setRepoUrl(e.target.value)}
        style={{ width: "100%", marginBottom: "10px" }}
      />

      <input
        placeholder="PR Number"
        value={prNumber}
        onChange={(e) => setPrNumber(e.target.value)}
        style={{ width: "100%", marginBottom: "10px" }}
      />

      <input
        placeholder="GitHub Token (optional)"
        value={githubToken}
        onChange={(e) => setGithubToken(e.target.value)}
        style={{ width: "100%", marginBottom: "10px" }}
      />

      <button onClick={handleSubmit}>Analyze PR</button>

      {taskId && (
        <div style={{ marginTop: "20px" }}>
          <p><b>Task ID:</b> {taskId}</p>
          <p><b>Status:</b> {status}</p>
        </div>
      )}

      {results && (
        <pre style={{ marginTop: "20px" }}>
          {JSON.stringify(results, null, 2)}
        </pre>
      )}
    </div>
  );
}

const pollStatus = async (taskId) => {
  const interval = setInterval(async () => {
    const res = await fetch(`http://localhost:8000/status/${taskId}`);
    const data = await res.json();

    setStatus(data.status);

    if (data.status === "completed") {
      clearInterval(interval);

      const resultRes = await fetch(
        `http://localhost:8000/results/${taskId}`
      );
      const resultData = await resultRes.json();
      setResults(resultData.results);
    }

    if (data.status === "failed") {
      clearInterval(interval);
    }
  }, 3000);
};

export default App;
