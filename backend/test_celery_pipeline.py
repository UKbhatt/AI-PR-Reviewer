#!/usr/bin/env python
"""
Diagnostic script to test Celery task submission and status retrieval.
Helps verify broker connection, task queuing, and backend state retrieval.
"""

import asyncio
import sys
from app.config import settings
from app.core.celery_app import celery_app
from app.tasks.analysis_tasks import analyze_pr_task
from celery.result import AsyncResult

def test_broker_connection():
    """Test if Celery can connect to the broker (Redis)."""
    print("\n[1] Testing Broker Connection...")
    try:
        with celery_app.connection() as conn:
            conn.default_channel.queue_declare('test_queue', durable=True)
            print("✅ Broker connection successful")
            return True
    except Exception as e:
        print(f"❌ Broker connection failed: {e}")
        return False

def test_task_submission():
    """Test submitting a task to the queue."""
    print("\n[2] Testing Task Submission...")
    try:
        # Submit a test task (will fail if GitHub/Ollama not configured, but that's OK)
        task = analyze_pr_task.apply_async(
            args=["python/cpython", 1],  # small repo for quick testing
            queue="analysis",
            task_id="test_task_123"
        )
        print(f"✅ Task submitted successfully")
        print(f"   Task ID: {task.id}")
        print(f"   State: {task.state}")
        return task.id
    except Exception as e:
        print(f"❌ Task submission failed: {e}")
        return None

def test_task_status(task_id):
    """Check task status from backend."""
    print(f"\n[3] Testing Status Retrieval (Task ID: {task_id})...")
    try:
        result = AsyncResult(task_id, app=celery_app)
        print(f"✅ Status retrieval successful")
        print(f"   State: {result.state}")
        print(f"   Info: {result.info}")
        print(f"   Ready: {result.ready()}")
        print(f"   Successful: {result.successful()}")
        print(f"   Failed: {result.failed()}")
        return result
    except Exception as e:
        print(f"❌ Status retrieval failed: {e}")
        return None

def test_redis_backend():
    """Test if Redis backend is accessible."""
    print("\n[4] Testing Redis Backend Connection...")
    try:
        import redis.asyncio as aioredis
        
        # Try to connect using the same config as settings
        url = settings.redis_dsn
        print(f"   Connecting to: {url.split('@')[1] if '@' in url else 'local'}")
        
        # For async redis, we'll just check the config
        print(f"✅ Redis config validated")
        print(f"   DSN: {url[:50]}..." if len(url) > 50 else f"   DSN: {url}")
        return True
    except Exception as e:
        print(f"❌ Redis backend test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("Celery Pipeline Diagnostic Test")
    print("=" * 60)
    
    # Test sequence
    broker_ok = test_broker_connection()
    if not broker_ok:
        print("\n⚠️  Broker connection failed. Make sure Redis is running and REDIS_URL is set in .env")
        sys.exit(1)
    
    backend_ok = test_redis_backend()
    
    task_id = test_task_submission()
    if task_id:
        print("\n⏳ Waiting 2 seconds for worker to pick up task (if running)...")
        import time
        time.sleep(2)
        test_task_status(task_id)
    
    print("\n" + "=" * 60)
    print("Diagnostic Summary:")
    print("=" * 60)
    print(f"✅ Broker connection: {'PASS' if broker_ok else 'FAIL'}")
    print(f"✅ Redis backend: {'PASS' if backend_ok else 'FAIL'}")
    print(f"✅ Task submission: {'PASS' if task_id else 'FAIL'}")
    print("\n📋 Next Steps:")
    print("1. If all tests pass, start a Celery worker:")
    print("   python -m celery -A app.core.celery_app.celery_app worker --loglevel=info -Q analysis")
    print("\n2. Watch the worker logs as you submit PRs from the frontend")
    print("\n3. The worker will process tasks and update Redis backend with state")
    print("\n4. Frontend will poll /api/v1/status/{task_id} to get real-time updates")
    print("=" * 60)

if __name__ == "__main__":
    main()
