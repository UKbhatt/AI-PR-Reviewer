# START HERE - Complete System Guide

## 🎯 What This System Does

**AI-Powered GitHub PR Code Review** using Ollama's llama3 model running locally on your machine.

Submit a PR → System analyzes it for bugs, security issues, style problems → Shows beautiful results with score and recommendations.

## ✅ What's Ready

- ✅ Backend API (FastAPI)
- ✅ Frontend UI (React)
- ✅ Task Queue (Celery + Redis)
- ✅ AI Integration (Ollama llama3)
- ✅ GitHub Integration (PyGithub)
- ✅ Error Handling (Proper exception propagation)
- ✅ Result Caching (Redis)

## 🚀 How to Run (Choose One Method)

### Method 1: Manual (Recommended for Learning)

You'll open 5 terminals. Run each command in its own terminal and leave it running.

**Terminal 1 - Ollama (AI Model)**
```bash
ollama serve
```
Wait for message: "Listening on 127.0.0.1:11434"

*(First time only: Download model)*
```bash
ollama pull llama3
```

**Terminal 2 - Redis (Database)**
```bash
redis-server
```
Should show: "Ready to accept connections"

**Terminal 3 - Celery Worker (Task Queue)**
```bash
cd backend
python -m celery -A app.core.celery_app.celery_app worker --loglevel=info -Q analysis
```
Should show: "celery@... ready to accept tasks"

**Terminal 4 - Backend API**
```bash
cd backend
pip install -r requirements.txt  # First time only
python -m uvicorn app.main:app --reload
```
Should show: "Uvicorn running on http://127.0.0.1:8000"

**Terminal 5 - Frontend**
```bash
npm install  # First time only
npm run dev
```
Should show: "Local: http://localhost:5173"

### Method 2: One-Command Setup (TODO - Create run script)

We can create a script to do this, but for now use Method 1.

## 💻 Using the System

### Step 1: Open Browser
```
http://localhost:5173
```

You'll see a beautiful interface with:
- Input fields for GitHub repo and PR number
- A button to "Analyze PR"

### Step 2: Enter PR Details

**Repository**: Can be:
- `owner/repo` format: `torvalds/linux`
- Full GitHub URL: `https://github.com/torvalds/linux`

**PR Number**: Just the number: `1`

**GitHub Token**: (Optional) 
- Leave blank for public repos
- Add `ghp_...` token for private repos

### Step 3: Click Analyze

Watch the progress bar fill from 0-100% as:
1. ✓ Fetching PR metadata
2. ✓ Fetching changed files
3. ✓ Analyzing code changes
4. ✓ Analyzing individual files
5. ✓ Generating summary

### Step 4: View Results

You'll see:

**PR Summary**
- Title, Author, Files Changed, Additions, Deletions

**Code Quality Score**
- 0-100 score in a nice circle

**Issues Found**
- Each with severity (Critical/High/Medium/Low)
- Category (security/bug/performance/style/best-practice)
- Description and suggestion for fix

**Recommendations**
- Key improvements suggested

**Summary**
- Overall assessment

## 📋 First Time Setup Checklist

- [ ] Install Ollama: https://ollama.ai
- [ ] Install Redis: `brew install redis` (Mac) or download from redis.io
- [ ] Install Python 3.9+: https://python.org
- [ ] Install Node.js 16+: https://nodejs.org
- [ ] Clone this repo or navigate to project folder
- [ ] Have 5 terminals ready

## 🔍 Verify Everything Works

After all 5 terminals are running, run:

```bash
python check_health.py
```

You should see:
```
✓ FastAPI backend
✓ Redis connection
✓ Celery worker
✓ Ollama with llama3
✓ React frontend
```

If anything shows ✗, follow the suggestions to fix it.

## 📝 Example: Analyze a Real PR

Public repo with real PRs: `torvalds/linux`
- Try PR #1 (simple PR from early Linux history)

Or try your own repo:
- Enter your repo owner/repo
- Add a GitHub token (optional but recommended)
- Pick a PR number
- Click Analyze!

## ⏱️ How Long Does It Take?

- **First analysis**: 30-60 seconds
  - Downloading PR data: 2-3s
  - Analyzing with AI: 25-50s
- **Second analysis (cached)**: < 0.5 seconds

The longer it takes, the larger the PR (more code to analyze).

## 🎨 UI Features

The interface is optimized for dark mode:
- Dark blue background
- Cyan and green accents
- Color-coded severity badges
- Smooth animations
- Mobile responsive

## 🛠️ What's Happening Behind the Scenes

1. **Frontend** sends PR info to Backend
2. **Backend** creates Celery task and returns task_id
3. **Frontend** polls for status every 2 seconds
4. **Celery Worker** runs analysis:
   - Fetches PR from GitHub
   - Downloads changed files
   - Sends code to Ollama AI
   - Gets analysis back
   - Generates summary
5. **Backend** caches results in Redis
6. **Frontend** displays results when ready

## 🔑 Key Files to Know About

**Frontend**
- `src/App.jsx` - Main UI component
- `src/App.css` - Styling

**Backend**
- `backend/app/main.py` - FastAPI app
- `backend/app/services/llm_service.py` - Ollama integration
- `backend/app/services/github_service.py` - GitHub integration
- `backend/app/agents/code_review_agent.py` - Analysis logic
- `backend/app/tasks/analysis_tasks.py` - Celery task

**Configuration**
- `backend/.env` - Settings

## 🐛 Troubleshooting

### "Connection refused" on http://localhost:5173
- Frontend not started
- Check Terminal 5: `npm run dev`

### "Failed to analyze code"
- Ollama not running
- Check Terminal 1: `ollama serve`
- Make sure you did: `ollama pull llama3`

### "Celery worker not responding"
- Worker not started
- Check Terminal 3: celery worker command
- Look for "ready to accept tasks"

### "Task not found"
- Task expired (24-hour limit)
- Re-submit the PR

### "Redis connection error"
- Redis not running
- Check Terminal 2: `redis-server`

## 📞 Need Help?

1. Run `python check_health.py` to see what's wrong
2. Check terminal output for error messages
3. Verify all 5 processes are actually running

## 🎓 Learning More

See these files:
- `QUICKSTART.md` - Detailed setup
- `CHANGES.md` - What changed in this session
- `COMPLETION_SUMMARY.md` - Technical summary

## 🚀 You're Ready!

Everything is set up and ready to go. 

**Just start the 5 terminals and visit http://localhost:5173**

Enjoy your AI code reviewer! 🤖
