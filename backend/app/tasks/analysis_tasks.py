from celery import Task
from datetime import datetime
import logging
from typing import Optional
from app.core.celery_app import celery_app
from app.core.token_crypto import decrypt_token

from app.agents.code_review_agent import CodeReviewAgent

logger = logging.getLogger(__name__)


class AnalysisTask(Task):
    """Base task with custom error handling."""
    
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
        github_token: Optional GitHub token, encrypted with TOKEN_ENCRYPTION_KEY by the API

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
    
    agent = CodeReviewAgent(github_token=decrypt_token(github_token))
    
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
    
    results = agent.execute(repo, pr_number)
    results['task_id'] = task_id
    results['status'] = 'success'
    results['authenticated'] = github_token is not None
    
    logger.info(f"Task {task_id}: Analysis completed successfully")
    return results


@celery_app.task(name="app.tasks.analysis_tasks.cleanup_old_results")
def cleanup_old_results():
    """Periodic task to cleanup old task results."""
    logger.info("Running cleanup task for old results")
    # This would be implemented with actual cleanup logic
    # For now, Redis will handle TTL-based expiration
    pass