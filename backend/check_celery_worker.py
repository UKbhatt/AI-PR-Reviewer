#!/usr/bin/env python3
"""
Quick diagnostic script to check if Celery worker is running and can process tasks.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.celery_app import celery_app
from app.config import settings

def check_celery_worker():
    """Check if Celery worker is active and can process tasks."""
    print("=" * 60)
    print("Celery Worker Diagnostic")
    print("=" * 60)
    
    # Check broker connection
    print("\n1. Checking Celery broker connection...")
    try:
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            print(f"[OK] Found {len(active_workers)} active worker(s):")
            for worker_name in active_workers.keys():
                print(f"   - {worker_name}")
            
            # Check if worker is listening to 'analysis' queue
            registered_queues = inspect.active_queues()
            print("\n2. Checking registered queues...")
            for worker_name, queues in registered_queues.items():
                queue_names = [q['name'] for q in queues]
                print(f"   Worker {worker_name} listening to: {', '.join(queue_names)}")
                if 'analysis' in queue_names:
                    print(f"   [OK] Worker {worker_name} is listening to 'analysis' queue")
                else:
                    print(f"   [WARNING] Worker {worker_name} is NOT listening to 'analysis' queue")
                    print(f"      Start worker with: celery -A app.core.celery_app.celery_app worker --loglevel=info -Q analysis")
        else:
            print("[ERROR] No active Celery workers found!")
            print("\n   To start a worker, run:")
            print("   cd backend")
            print("   python -m celery -A app.core.celery_app.celery_app worker --loglevel=info -Q analysis")
            return False
            
    except Exception as e:
        print(f"[ERROR] Failed to connect to Celery broker: {e}")
        print(f"\n   Broker URL: {settings.celery_broker_url}")
        print("   Make sure Redis is running and accessible")
        return False
    
    print("\n3. Checking broker URL...")
    print(f"   Broker: {settings.celery_broker_url}")
    print(f"   Backend: {settings.celery_result_backend}")
    
    print("\n" + "=" * 60)
    return True

if __name__ == "__main__":
    success = check_celery_worker()
    sys.exit(0 if success else 1)

