# 🤖 AI Code Review Agent

> Autonomous AI-powered GitHub pull request analyzer using local Ollama llama3 model for intelligent code review

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev/)
[![Celery](https://img.shields.io/badge/Celery-5.3+-37B24D.svg)](https://docs.celeryproject.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage Guide](#-usage-guide)
- [API Reference](#-api-reference)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

**AI Code Review Agent** is a full-stack application that analyzes GitHub pull requests using local AI (Ollama llama3 model). It identifies security issues, performance problems, code style violations, and provides actionable recommendations.

**Key Benefits:**
- 🔒 Privacy-first: runs entirely on your machine
- ⚡ Fast: ~30-60 seconds per PR analysis
- 🎨 Beautiful UI: dark-themed React interface with real-time progress
- 🔄 Async processing: powered by Celery and Redis
- 📊 Detailed analysis: security, performance, style, best practices

---

## ✨ Features

| Feature | Description |
|---------|----------|
| 🔍 **Smart Analysis** | Identifies bugs, security issues, performance problems, style violations |
| 🏃 **Async Processing** | Tasks run in background via Celery worker |
| 📈 **Real-time Progress** | Live progress bar showing analysis phase (0-100%) |
| 🎯 **Code Quality Score** | Overall score (0-100) with detailed breakdown |
| 💡 **Smart Recommendations** | Actionable suggestions for improvement |
| 🔐 **Local Processing** | No cloud dependencies, your code stays private |
| 💾 **Result Caching** | Instant re-analysis of same PR |
| 🐙 **GitHub Integration** | Direct GitHub API access for PR details, files, diffs |
| 🎨 **Beautiful UI** | Modern dark theme with color-coded severity badges |
| 📱 **Responsive Design** | Works on desktop and tablet |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend                            │
│              http://localhost:5173                           │
│         (Beautiful UI for PR submission & results)           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ REST API (HTTP)
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                 FastAPI Backend                              │
│              http://localhost:8000                           │
│      - PR submission endpoint (POST /api/v1/analyze-pr)     │
│      - Status polling endpoint (GET /api/v1/status/:id)     │
│      - Results endpoint (GET /api/v1/results/:id)           │
│      - Health check (GET /api/v1/health)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
    Celery        GitHub API      Ollama LLM
    Worker        (PR details,    (llama3 model
    (Redis)       files, diffs)   for analysis)
```

### 📦 Component Overview

| Component | Purpose | Technology |
|-----------|---------|----------|
| **Frontend** | User interface for PR analysis | React 18 + Vite |
| **Backend API** | REST endpoints for task submission & status | FastAPI |
| **Task Queue** | Async task processing | Celery + Redis |
| **AI Engine** | Code analysis using local LLM | Ollama llama3 |
| **GitHub** | PR data & diff retrieval | PyGithub library |
| **Cache** | Result caching & task storage | Redis |

---

## 📋 Prerequisites

Before you begin, ensure you have:

- **Python 3.9+** — [Download](https://www.python.org/downloads/)
- **Node.js 16+** — [Download](https://nodejs.org/)
- **Ollama** — [Download](https://ollama.ai/) (includes llama3)
- **Redis** — [Download](https://redis.io/) or use Redis Cloud
- **Git** — [Download](https://git-scm.com/)
- **GitHub Account** — For accessing PRs

### System Requirements

- **Disk Space:** 5GB+ (for Ollama models)
- **RAM:** 8GB+ (recommended 16GB)
- **CPU:** Multi-core processor recommended
- **Network:** Internet for GitHub API & Ollama model download

---

## 🚀 Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/pull-request-reviewer.git
cd pull-request-reviewer
```

### Step 2: Install Ollama & Download llama3

```bash
# Download and install Ollama from https://ollama.ai
# After installation, pull the llama3 model

ollama pull llama3
```

### Step 3: Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 4: Install Node Dependencies

```bash
# From project root
npm install
```

### Step 5: Configure Environment (Optional)

Create `backend/.env` file:

```bash
# Redis Configuration (local)
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379

# OR for Redis Cloud
# REDIS_URL=rediss://user:password@host:port
# CELERY_BROKER_URL=rediss://user:password@host:port

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
OLLAMA_TIMEOUT=300

# GitHub (Optional - for private repos)
GITHUB_TOKEN=ghp_your_token_here

# Application
DEBUG=False
LOG_LEVEL=INFO
```

---

## ⚡ Quick Start

### Method 1: Run All Services (5 Terminals)

**Terminal 1 — Start Ollama Server**
```bash
ollama serve
```
Expected output: `Listening on 127.0.0.1:11434`

**Terminal 2 — Start Redis Server**
```bash
redis-server
```
Expected output: `Ready to accept connections`

**Terminal 3 — Start Celery Worker**
```bash
cd backend
python -m celery -A app.core.celery_app.celery_app worker --loglevel=info -Q analysis --pool=solo
```
Expected output: `celery@hostname ready to accept tasks`

**Terminal 4 — Start FastAPI Backend**
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Expected output: `Uvicorn running on http://0.0.0.0:8000`

**Terminal 5 — Start React Frontend**
```bash
npm run dev
```
Expected output: `Local: http://localhost:5173`

### Method 2: Verify Everything is Running

```bash
python check_health.py
```

Expected output:
```
✓ FastAPI backend (http://localhost:8000)
✓ Redis connection
✓ Celery worker
✓ Ollama with llama3
✓ React frontend (http://localhost:5173)
```

### Step 3: Open Browser & Start Analyzing

Navigate to: **http://localhost:5173**

---

## 📖 Usage Guide

### Step 1: Open Application

Visit `http://localhost:5173` in your browser. You'll see a beautiful dark-themed interface.

### Step 2: Enter PR Details

Fill in the form:
- **Repository** — `owner/repo` or full GitHub URL
  - Example: `torvalds/linux` or `https://github.com/torvalds/linux`
- **PR Number** — Just the number (e.g., `1`, `42`, `1234`)
- **GitHub Token** — (Optional) for private repos or higher rate limits
  - Leave blank for public repos

### Step 3: Submit for Analysis

Click **"Analyze PR"** button. You'll see:
- 🔄 Progress bar advancing from 0-100%
- 📊 Real-time status messages showing current phase
- ⏱️ Processing time estimates

### Step 4: View Results

Once analysis completes (30-60 seconds), you'll see:

```
📝 PR Summary
  - Title & Author
  - Files changed, additions, deletions
  - Commit count

🎯 Code Quality Score
  - Circular badge showing 0-100 score

📌 Summary
  - Executive overview of the PR

✅ Recommendations
  - Bullet-list of actionable improvements

🔴 Issues Found
  - Color-coded by severity (Critical/High/Medium/Low)
  - Category (Security/Bug/Performance/Style/Best-Practice)
  - Description & suggested fix
  - File path & line number
```

### Example Usage

1. Repository: `TheAlgorithms/Python`
2. PR Number: `14017`
3. Click "Analyze PR"
4. Wait for analysis (~45 seconds)
5. View detailed issues and recommendations

---

## 🔌 API Reference

### 📤 Submit PR for Analysis

```http
POST /api/v1/analyze-pr
Content-Type: application/json

{
  "repo": "owner/repo",
  "pr_number": 123,
  "github_token": "ghp_..." (optional)
}
```

**Response (202 Accepted):**
```json
{
  "task_id": "6a9d900c-37bc-4411-ab0c-34fe69fe7b08",
  "status": "pending",
  "message": "PR analysis task submitted successfully"
}
```

---

### 📊 Check Analysis Status

```http
GET /api/v1/status/{task_id}
```

**Response:**
```json
{
  "task_id": "6a9d900c-37bc-4411-ab0c-34fe69fe7b08",
  "status": "processing",
  "progress": 45,
  "message": "Analyzing code changes...",
  "started_at": "2024-01-15T10:30:05Z"
}
```

**Status Values:**
- `pending` — Waiting in queue
- `started` — Task started
- `processing` — Currently analyzing (shows progress)
- `success` — Analysis complete
- `failure` — Analysis failed
- `retry` — Retrying after error

---

### 📥 Get Analysis Results

```http
GET /api/v1/results/{task_id}
```

**Response (200 OK):**
```json
{
  "task_id": "6a9d900c-37bc-4411-ab0c-34fe69fe7b08",
  "pr_summary": {
    "title": "Add new authentication feature",
    "author": "john-dev",
    "files_changed": 5,
    "additions": 150,
    "deletions": 30,
    "commits": 3
  },
  "issues": [
    {
      "severity": "high",
      "category": "security",
      "title": "Potential SQL Injection",
      "description": "User input concatenated into query",
      "file_path": "src/database.py",
      "line_number": 42,
      "suggestion": "Use parameterized queries"
    }
  ],
  "overall_score": 78,
  "summary": "The PR introduces a new authentication feature...",
  "recommendations": [
    "Fix SQL injection vulnerability",
    "Add unit tests",
    "Document the API"
  ],
  "analyzed_at": "2024-01-15T10:35:00Z",
  "processing_time": 45.2
}
```

---

### 🏥 Health Check

```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "redis_connected": true,
  "celery_active": true,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## ⚙️ Configuration

### Backend Configuration (`backend/.env`)

```bash
# ============= Redis =============
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379

# For Redis Cloud (rediss://)
# REDIS_URL=rediss://user:password@host:port
# CELERY_BROKER_URL=rediss://user:password@host:port

# ============= Ollama =============
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
OLLAMA_TIMEOUT=300  # seconds

# ============= GitHub =============
GITHUB_TOKEN=ghp_your_token_here  # Optional

# ============= Application =============
DEBUG=False
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
APP_NAME="Code Review Agent"
APP_VERSION="1.0.0"

# ============= Celery =============
CELERY_TASK_TIME_LIMIT=1800  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT=1500  # 25 minutes
TASK_RESULT_TTL=86400  # 24 hours

# ============= Cache =============
CACHE_TTL=3600  # 1 hour
CACHE_ENABLED=True
```

### Frontend Configuration (`vite.config.js`)

The frontend is pre-configured to connect to `http://localhost:8000/api/v1`. For production, update API base URL in `src/App.jsx`.

---

## 🐛 Troubleshooting

### ❌ Frontend Can't Connect to Backend

**Symptom:** "Failed to submit analysis request"

**Solutions:**
1. Verify FastAPI is running on port 8000
   ```bash
   curl http://localhost:8000/api/v1/health
   ```
2. Check CORS is enabled (should be by default)
3. Check firewall/network settings

---

### ❌ Celery Worker Not Receiving Tasks

**Symptom:** Task stays in "pending" state forever

**Solutions:**
1. Verify worker is running with correct app path:
   ```bash
   python -m celery -A app.core.celery_app.celery_app worker --loglevel=info -Q analysis
   ```
2. Check Redis connection:
   ```bash
   redis-cli ping  # Should return PONG
   ```
3. Verify broker URL in logs:
   ```bash
   python -c "from app.config import settings; print(settings.redis_dsn)"
   ```

---

### ❌ Ollama Connection Error

**Symptom:** "Failed to analyze code" or LLMException

**Solutions:**
1. Ensure Ollama is running:
   ```bash
   ollama serve
   ```
2. Verify llama3 is downloaded:
   ```bash
   ollama list  # Should show llama3
   ```
3. Test Ollama API:
   ```bash
   curl http://localhost:11434/api/tags
   ```
4. Check Ollama is accessible at configured URL (default: http://localhost:11434)

---

### ❌ Redis Connection Error

**Symptom:** "Redis connection refused" or "Error connecting to Redis"

**Solutions:**
1. If using local Redis:
   ```bash
   redis-server
   ```
2. If using Redis Cloud, verify connection string in `.env`:
   ```bash
   python - <<'PY'
   import redis, os
   r = redis.from_url(os.environ.get("REDIS_URL"))
   print("Ping:", r.ping())
   PY
   ```
3. For Windows, use WSL or Docker:
   ```bash
   docker run --name redis -p 6379:6379 -d redis:7
   ```

---

### ❌ Analysis Takes Too Long

**Symptom:** Analysis takes > 2 minutes

**Causes & Solutions:**
- Large PR (100+ files): Normal, Ollama takes time for large code
- Slow machine: More RAM helps
- Slow internet: Check network
- Ollama overloaded: Close other apps, restart Ollama

**Typical timings:**
- Small PR (1-5 files): 15-30 seconds
- Medium PR (5-20 files): 30-60 seconds
- Large PR (20+ files): 1-2+ minutes

---

### ❌ "Task Results Not Found"

**Symptom:** Get 404 when fetching results

**Solutions:**
1. Task may have expired (24-hour default TTL)
2. Re-submit the PR for fresh analysis
3. Check Redis is storing results:
   ```bash
   redis-cli KEYS "*"
   ```

---

### ❌ GitHub Rate Limit Error

**Symptom:** "GitHub API rate limit exceeded"

**Solutions:**
1. Add GitHub token (5000 req/hour vs 60 req/hour unauthenticated)
   ```bash
   # Get token: https://github.com/settings/tokens
   # Add to .env: GITHUB_TOKEN=ghp_xxx
   ```
2. Wait 1 hour for rate limit reset
3. Use different IP/network

---

## 📁 Project Structure

```
pull-request-reviewer/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   └── code_review_agent.py       # Main analysis logic
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── analysis.py        # PR analysis endpoints
│   │   │       │   └── health.py          # Health check endpoint
│   │   │       └── router.py
│   │   ├── core/
│   │   │   ├── celery_app.py             # Celery configuration
│   │   │   ├── redis_client.py           # Redis client
│   │   │   └── logging.py                # Logging setup
│   │   ├── models/
│   │   │   ├── requests.py               # Request models
│   │   │   └── responses.py              # Response models
│   │   ├── services/
│   │   │   ├── github_service.py         # GitHub API wrapper
│   │   │   ├── llm_service.py            # Ollama integration
│   │   │   └── cache_service.py          # Redis cache
│   │   ├── tasks/
│   │   │   └── analysis_tasks.py         # Celery task definitions
│   │   ├── utils/
│   │   │   └── exceptions.py             # Custom exceptions
│   │   ├── config.py                     # Settings
│   │   └── main.py                       # FastAPI app
│   ├── .env                              # Environment variables
│   └── requirements.txt                  # Python dependencies
│
├── src/
│   ├── App.jsx                           # Main React component
│   ├── App.css                           # Styles
│   ├── main.jsx                          # React entry point
│   └── index.css                         # Global styles
│
├── public/                               # Static assets
├── package.json                          # Node dependencies
├── vite.config.js                        # Vite configuration
├── README.md                             # This file
├── START_HERE.md                         # Quick start guide
├── QUICKSTART.md                         # Detailed setup
├── CHANGES.md                            # Changelog
├── check_health.py                       # Health check script
└── system_status.py                      # System status script
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make** your changes
4. **Commit** with clear messages
   ```bash
   git commit -m "Add amazing feature"
   ```
5. **Push** to your fork
   ```bash
   git push origin feature/amazing-feature
   ```
6. **Create** a Pull Request

---

## 📝 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Keep discussions on-topic
- Report issues professionally

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) file for details.

You're free to use, modify, and distribute this project for personal and commercial purposes.

---

## 🙏 Acknowledgments

- **FastAPI** — Modern, fast web framework
- **Celery** — Distributed task queue
- **Ollama** — Local LLM engine
- **PyGithub** — GitHub API wrapper
- **React** — UI library
- **Vite** — Lightning-fast build tool

---

## 📞 Support & Contact

### Need Help?

1. **Check** [Troubleshooting](#-troubleshooting) section
2. **Run** `python check_health.py` to diagnose issues
3. **Read** [START_HERE.md](START_HERE.md) for quick setup
4. **Review** [QUICKSTART.md](QUICKSTART.md) for detailed steps

### Report Issues

Found a bug? [Create an Issue](https://github.com/yourusername/pull-request-reviewer/issues)

### Documentation

- [START_HERE.md](START_HERE.md) — Beginner's guide
- [QUICKSTART.md](QUICKSTART.md) — Setup instructions
- [CHANGES.md](CHANGES.md) — What changed
- [COMPLETION_SUMMARY.md](COMPLETION_SUMMARY.md) — Technical details

---

## 🚀 Performance Metrics

| Metric | Value |
|--------|-------|
| Time to first analysis | 30-60 seconds |
| Cached PR reanalysis | < 0.5 seconds |
| Max PR diff size | 15,000 chars |
| Max files analyzed | 10 (important ones) |
| API response time | < 100ms |
| Celery task timeout | 30 minutes |

---

## 🔮 Roadmap

Future features planned:

- [ ] Web UI improvements (dark/light theme toggle)
- [ ] Multiple AI model support
- [ ] Slack/Teams notifications
- [ ] GitHub webhook integration
- [ ] Batch PR analysis
- [ ] Custom rule definitions
- [ ] Team/org dashboards
- [ ] Historical trend analysis
- [ ] Docker containerization
- [ ] Cloud deployment (AWS, GCP, Azure)

---

## 📊 Status

- ✅ Backend API — **Production Ready**
- ✅ Frontend UI — **Production Ready**
- ✅ Celery Integration — **Production Ready**
- ✅ Ollama Integration — **Production Ready**
- ✅ GitHub Integration — **Production Ready**

---

**Last Updated:** January 1, 2026  
**Version:** 1.0.0
