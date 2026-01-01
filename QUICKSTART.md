# Quick Start Guide

## Prerequisites
- Python 3.9+
- Node.js 16+
- Ollama running with llama3 model
- Redis (local or Redis Cloud with connection string)

## Step 1: Start Ollama
```bash
ollama serve
```
This starts Ollama on `http://localhost:11434`

## Step 2: Download llama3 model
```bash
ollama pull llama3
```

## Step 3: Start Redis (if local)
```bash
redis-server
```
Or use Redis Cloud with your connection URL in `.env`

## Step 4: Setup Backend
```bash
cd backend
pip install -r requirements.txt
```

Create `.env` file:
```
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

## Step 5: Start Celery Worker

**On Windows:**
```bash
cd backend
python -m celery -A app.core.celery_app.celery_app worker --loglevel=info -Q analysis --pool=solo
```
Or use the batch script:
```bash
cd backend
start_celery_worker.bat
```

**On Linux/Mac:**
```bash
cd backend
python -m celery -A app.core.celery_app.celery_app worker --loglevel=info -Q analysis
```
Or use the shell script:
```bash
cd backend
chmod +x start_celery_worker.sh
./start_celery_worker.sh
```

**Note:** Windows requires the `--pool=solo` flag because the default prefork pool doesn't work on Windows due to multiprocessing limitations.

## Step 6: Start FastAPI Backend
In a new terminal:
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Step 7: Start React Frontend
In a new terminal:
```bash
npm install
npm run dev
```

This starts the frontend on `http://localhost:5173`

## Step 8: Test It Out

1. Open http://localhost:5173
2. Enter a public GitHub repo (e.g., `torvalds/linux`)
3. Enter a PR number (e.g., `1`)
4. (Optional) Add your GitHub token for higher rate limits
5. Click "Analyze PR"
6. Watch the progress bar as the AI analyzes the PR
7. View the analysis results with issues, score, and recommendations

## Troubleshooting

### "Celery active: false" in health check
- Make sure the Celery worker is running from Step 5

### "Failed to analyze code" errors
- Make sure Ollama is running with `ollama serve`
- Make sure llama3 model is downloaded with `ollama pull llama3`

### Redis connection errors
- For local: Make sure Redis server is running
- For Redis Cloud: Ensure your connection URL in `.env` is correct

### "Task not found" when checking status
- The task might have expired. Tasks are kept for 24 hours by default

## API Endpoints

- `POST /api/v1/analyze-pr` - Submit PR for analysis
- `GET /api/v1/status/{task_id}` - Check analysis progress
- `GET /api/v1/results/{task_id}` - Get analysis results
- `GET /api/v1/health` - Check service health
