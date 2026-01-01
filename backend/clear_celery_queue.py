#!/usr/bin/env python3
"""
Script to clear all queued Celery tasks from Redis.
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


async def clear_celery_queue():
    """Clear all queued tasks from Celery queues."""
    try:
        await redis_client.connect()
        
        # Get the queue name
        queue_name = "analysis"
        
        logger.info(f"Clearing queue: {queue_name}")
        
        # Use Celery's control to purge the queue
        # This is the proper way to clear a queue
        try:
            purged = celery_app.control.purge()
            logger.info(f"Purged {purged} message(s) from all queues")
        except Exception as e:
            logger.warning(f"Could not purge via control API: {e}")
            purged = 0
            # Try manual Redis cleanup instead
            logger.info("Attempting manual queue cleanup...")
        
        # Also manually clear Redis keys for the queue
        # Celery stores queue messages with pattern: _kombu.binding.<queue_name>
        pattern = f"_kombu.binding.{queue_name}*"
        deleted_count = 0
        
        async for key in redis_client.client.scan_iter(match=pattern):
            try:
                await redis_client.delete(key)
                deleted_count += 1
                logger.debug(f"Deleted queue binding: {key}")
            except Exception as e:
                logger.error(f"Error deleting key {key}: {e}")
        
        # Also clear any direct queue keys
        queue_patterns = [
            f"celery-task-meta-*",
            f"celery-*",
        ]
        
        for pattern in queue_patterns:
            async for key in redis_client.client.scan_iter(match=pattern):
                # Don't delete active task results, only queued/pending ones
                if "task-meta" not in key:
                    try:
                        await redis_client.delete(key)
                        deleted_count += 1
                        logger.debug(f"Deleted queue key: {key}")
                    except Exception as e:
                        logger.error(f"Error deleting key {key}: {e}")
        
        logger.info(f"Additional cleanup: Deleted {deleted_count} queue-related key(s)")
        
        return purged + deleted_count
        
    except Exception as e:
        logger.error(f"Queue cleanup failed: {e}", exc_info=True)
        return 0
    finally:
        await redis_client.disconnect()


def main():
    """Main entry point."""
    print("=" * 60)
    print("Celery Queue Cleanup Script")
    print("=" * 60)
    print("\nThis script will clear all queued tasks from Celery.")
    print("WARNING: This will remove all pending tasks from the queue!")
    print("\nPress Ctrl+C to cancel, or wait 3 seconds to continue...")
    
    try:
        import time
        time.sleep(3)
    except KeyboardInterrupt:
        print("\nCancelled.")
        return
    
    print("\nClearing queue...")
    deleted = asyncio.run(clear_celery_queue())
    
    print("\n" + "=" * 60)
    print(f"Successfully cleared {deleted} queued task(s).")
    print("You can now submit a new task and it will be processed immediately.")
    print("=" * 60)


if __name__ == "__main__":
    main()

