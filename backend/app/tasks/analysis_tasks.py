from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from datetime import datetime
import logging
from typing import Optional
from app.core.celery_app import celery_app

from app.agents.code_review_agent import CodeReviewAgent
from app.config import settings
from app.utils.exceptions import AgentException

logger = logging.getLogger(__name__)


class AnalysisTask(Task):
    """Base task with custom error handling."""
    
    # Don't auto-retry on all exceptions - handle retries manually for better control
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': settings.MAX_RETRIES}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure - log and update state."""
        logger.error(f"Task {task_id} failed: {exc}", exc_info=einfo)
        return super().on_failure(exc, task_id, args, kwargs, einfo)


@celery_app.task(
    bind=True,
    base=AnalysisTask,
    name="app.tasks.analysis_tasks.analyze_pr_task",
    track_started=True
)
def analyze_pr_task(
    self, 
    repo: str, 
    pr_number: int, 
    github_token: Optional[str] = None
) -> dict:
    """
    Celery task to analyze a GitHub PR.
    
    Args:
        repo: Repository in format 'owner/repo'
        pr_number: Pull request number
        github_token: Optional GitHub token for authentication
    
    Returns:
        Dictionary containing analysis results
    """
    task_id = self.request.id
    logger.info(f"Task {task_id}: Starting analysis for {repo}#{pr_number}")
    
    # Update task state to PROCESSING
    self.update_state(
        state='PROCESSING',
        meta={
            'phase': 'initializing',
            'progress': 0,
            'repo': repo,
            'pr_number': pr_number,
            'started_at': datetime.now().isoformat()
        }
    )
    
    try:
        # Initialize agent
        agent = CodeReviewAgent(github_token=github_token)
        
        # Create callback to update task state during execution
        original_update = agent.update_progress
        
        def update_with_celery(phase: str, progress: int):
            original_update(phase, progress)
            self.update_state(
                state='PROCESSING',
                meta={
                    'phase': phase,
                    'progress': progress,
                    'repo': repo,
                    'pr_number': pr_number,
                    'files_analyzed': agent.analysis_state.get('files_analyzed', 0)
                }
            )
        
        agent.update_progress = update_with_celery
        
        # Execute analysis
        results = agent.execute(repo, pr_number)
        
        # Add task metadata
        results['task_id'] = task_id
        results['status'] = 'success'
        
        logger.info(f"Task {task_id}: Analysis completed successfully")
        return results
        
    except SoftTimeLimitExceeded:
        logger.error(f"Task {task_id}: Soft time limit exceeded")
        self.update_state(
            state='FAILURE',
            meta={
                'error': 'Task execution time limit exceeded',
                'phase': 'timeout',
                'repo': repo,
                'pr_number': pr_number
            }
        )
        raise
        
    except AgentException as e:
        logger.error(f"Task {task_id}: Agent error - {e}")
        error_msg = str(e)
        error_type = type(e).__name__
        
        # Check if it's an authentication error - don't retry these
        from app.utils.exceptions import GitHubAPIException
        if isinstance(e, GitHubAPIException) and ("Bad credentials" in error_msg or "401" in error_msg):
            logger.warning(f"Task {task_id}: GitHub authentication failed - task will not retry")
            self.update_state(
                state='FAILURE',
                meta={
                    'error': error_msg,
                    'error_type': error_type,
                    'phase': 'authentication_error',
                    'repo': repo,
                    'pr_number': pr_number
                }
            )
            # Raise a standard Exception (not custom) to avoid serialization issues
            # This ensures Celery can properly serialize the exception
            raise RuntimeError(f"GitHub authentication failed: {error_msg}") from e
        
        self.update_state(
            state='FAILURE',
            meta={
                'error': error_msg,
                'error_type': error_type,
                'phase': 'agent_error',
                'repo': repo,
                'pr_number': pr_number
            }
        )
        # Re-raise as RuntimeError to ensure proper serialization
        raise RuntimeError(f"Analysis failed: {error_msg}") from e
        
    except Exception as e:
        logger.error(f"Task {task_id}: Unexpected error - {e}", exc_info=True)
        error_msg = str(e)
        error_type = type(e).__name__
        
        self.update_state(
            state='FAILURE',
            meta={
                'error': error_msg,
                'error_type': error_type,
                'phase': 'unexpected_error',
                'repo': repo,
                'pr_number': pr_number
            }
        )
        # Re-raise as RuntimeError to ensure proper serialization by Celery
        # Custom exceptions sometimes don't serialize well
        if not isinstance(e, (RuntimeError, ValueError, KeyError, TypeError)):
            raise RuntimeError(f"Task failed: {error_msg}") from e
        raise


@celery_app.task(name="app.tasks.analysis_tasks.cleanup_old_results")
def cleanup_old_results():
    """Periodic task to cleanup old task results."""
    logger.info("Running cleanup task for old results")
    # This would be implemented with actual cleanup logic
    # For now, Redis will handle TTL-based expiration
    pass