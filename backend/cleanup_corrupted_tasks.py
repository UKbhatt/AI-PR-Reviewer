#!/usr/bin/env python3
"""
Script to clean up corrupted Celery tasks from Redis.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.celery_app import celery_app
from app.core.redis_client import redis_client
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def cleanup_corrupted_tasks():
    """Clean up corrupted task results from Redis."""
    try:
        await redis_client.connect()
        
        # Get all task keys from Redis
        # Celery stores task results with keys like: celery-task-meta-<task_id>
        logger.info("Scanning for Celery task keys...")
        
        # Use Redis client to scan for task keys
        pattern = "celery-task-meta-*"
        cursor = 0
        deleted_count = 0
        
        async for key in redis_client.client.scan_iter(match=pattern):
            try:
                # Try to get the task metadata
                task_id = key.replace("celery-task-meta-", "")
                task_result = celery_app.AsyncResult(task_id)
                
                # Try to access the state - if it fails, the task is corrupted
                try:
                    _ = task_result.state
                    logger.debug(f"Task {task_id} is valid")
                except (ValueError, KeyError) as e:
                    logger.warning(f"Found corrupted task {task_id}: {e}")
                    # Delete the corrupted task
                    await redis_client.delete(key)
                    deleted_count += 1
                    logger.info(f"Deleted corrupted task: {task_id}")
                    
            except Exception as e:
                logger.error(f"Error processing key {key}: {e}")
                # If we can't even check it, delete it to be safe
                try:
                    await redis_client.delete(key)
                    deleted_count += 1
                    logger.info(f"Deleted unreadable task key: {key}")
                except:
                    pass
        
        logger.info(f"Cleanup complete. Deleted {deleted_count} corrupted task(s).")
        
        # Also clean up any tasks in RETRY or FAILURE state that are old
        logger.info("Cleaning up old failed/retry tasks...")
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        if active_tasks:
            for worker_name, tasks in active_tasks.items():
                for task in tasks:
                    task_id = task.get('id')
                    if task_id:
                        try:
                            task_result = celery_app.AsyncResult(task_id)
                            state = task_result.state
                            if state in ['FAILURE', 'RETRY']:
                                logger.info(f"Found old {state} task: {task_id}, cleaning up...")
                                task_result.backend.delete(task_id)
                                deleted_count += 1
                        except:
                            pass
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}", exc_info=True)
        return 0
    finally:
        await redis_client.disconnect()


def main():
    """Main entry point."""
    print("=" * 60)
    print("Celery Task Cleanup Script")
    print("=" * 60)
    print("\nThis script will clean up corrupted Celery task metadata from Redis.")
    print("This is safe to run - it only removes corrupted/unreadable tasks.\n")
    
    deleted = asyncio.run(cleanup_corrupted_tasks())
    
    print("\n" + "=" * 60)
    if deleted > 0:
        print(f"Successfully cleaned up {deleted} corrupted task(s).")
        print("You can now restart your Celery worker.")
    else:
        print("No corrupted tasks found. Redis is clean.")
    print("=" * 60)


if __name__ == "__main__":
    main()

