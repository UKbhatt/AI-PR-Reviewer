from fastapi import APIRouter, HTTPException, Depends, status
from celery.result import AsyncResult
from typing import Optional
import logging
from app.models.requests import AnalyzePRRequest
from app.models.responses import (
    AnalyzePRResponse, 
    TaskStatusResponse, 
    AnalysisResults,
    TaskStatus
)
from app.tasks.analysis_tasks import analyze_pr_task
from app.core.celery_app import celery_app
from app.services.cache_service import cache_service
from app.utils.exceptions import TaskNotFoundException

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/analyze-pr",
    response_model=AnalyzePRResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit PR for analysis",
    description="Submit a GitHub pull request for asynchronous code review analysis"
)
async def analyze_pr(request: AnalyzePRRequest) -> AnalyzePRResponse:
    """
    Submit a pull request for code review analysis.
    
    The analysis is performed asynchronously. Use the returned task_id
    to check status and retrieve results.
    """
    try:
        # Check cache first
        cached_result = await cache_service.get_analysis(request.repo, request.pr_number)
        
        if cached_result:
            logger.info(f"Returning cached result for {request.repo}#{request.pr_number}")
            # Return cached task_id if available
            if 'task_id' in cached_result:
                return AnalyzePRResponse(
                    task_id=cached_result['task_id'],
                    status=TaskStatus.SUCCESS,
                    message="Analysis already completed (cached result available)"
                )
        
        # Submit task to Celery
        try:
            task = analyze_pr_task.apply_async(
                args=[request.repo, request.pr_number, request.github_token],
                queue='analysis'
            )
            
            logger.info(f"Submitted analysis task {task.id} for {request.repo}#{request.pr_number}")
            
            return AnalyzePRResponse(
                task_id=task.id,
                status=TaskStatus.PENDING,
                message=f"PR analysis task submitted successfully for {request.repo}#{request.pr_number}. Make sure Celery worker is running with: celery -A app.core.celery_app.celery_app worker --loglevel=info -Q analysis"
            )
        except Exception as celery_error:
            logger.error(f"Failed to submit task to Celery: {celery_error}", exc_info=True)
            # Check if it's a connection error
            error_msg = str(celery_error)
            if "connection" in error_msg.lower() or "broker" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Cannot connect to Celery broker. Make sure Redis is running and CELERY_BROKER_URL is configured correctly. Error: {error_msg}"
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to submit analysis task: {error_msg}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit analysis task: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit analysis task: {str(e)}"
        )


@router.get(
    "/status/{task_id}",
    response_model=TaskStatusResponse,
    summary="Get task status",
    description="Check the status of an analysis task"
)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """
    Get the current status of an analysis task.
    
    Returns information about task progress, current phase, and any errors.
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        
        # Build response based on task state
        response_data = {
            "task_id": task_id,
            "status": TaskStatus.PENDING,
            "message": None,
            "progress": None,
            "error": None
        }
        
        # Try to get task state, handle corrupted metadata gracefully
        try:
            task_state = task_result.state
        except (ValueError, KeyError) as decode_error:
            # Task metadata is corrupted (e.g., from previous failed retry)
            logger.warning(f"Task {task_id} has corrupted metadata: {decode_error}")
            # Try to delete the corrupted task result and return error
            try:
                task_result.backend.delete(task_id)
            except:
                pass
            response_data["status"] = "failure"
            response_data["message"] = "Task metadata corrupted. Please submit a new analysis request."
            response_data["error"] = "Previous task failed and metadata could not be decoded. Please try again."
            response_data["progress"] = 0
            return TaskStatusResponse(**response_data)
        
        if task_state == 'PENDING':
            # Check if task is actually pending or if worker isn't running
            try:
                task_info = task_result.info
            except (ValueError, KeyError):
                task_info = None
                
            if task_info is None:
                # Task hasn't been picked up by worker yet
                response_data["status"] = "pending"
                response_data["message"] = "Task is queued and waiting for worker to start processing. Make sure Celery worker is running with: celery -A app.core.celery_app.celery_app worker --loglevel=info -Q analysis --pool=solo"
                response_data["progress"] = 0
            else:
                # Task info exists but state is PENDING (unusual)
                response_data["status"] = "pending"
                response_data["message"] = "Task is waiting to be processed"
                response_data["progress"] = 0
            
        elif task_state == 'STARTED':
            response_data["status"] = "started"
            response_data["message"] = "Task has been started"
            response_data["progress"] = 5
            try:
                info = task_result.info or {}
                response_data["started_at"] = info.get('started_at') if isinstance(info, dict) else None
            except (ValueError, KeyError):
                pass
            
        elif task_state == 'PROCESSING':
            response_data["status"] = "processing"
            try:
                info = task_result.info or {}
                if isinstance(info, dict):
                    response_data["progress"] = info.get('progress', 0)
                    response_data["message"] = f"Processing: {info.get('phase', 'analyzing')}"
                else:
                    response_data["progress"] = 0
                    response_data["message"] = "Processing..."
            except (ValueError, KeyError):
                response_data["progress"] = 0
                response_data["message"] = "Processing..."
            
        elif task_state == 'SUCCESS':
            response_data["status"] = "success"
            response_data["message"] = "Analysis completed successfully"
            response_data["progress"] = 100
            try:
                info = task_result.info
                if isinstance(info, dict):
                    response_data["completed_at"] = info.get('analyzed_at')
            except (ValueError, KeyError):
                pass
            
        elif task_state == 'FAILURE':
            response_data["status"] = "failure"
            response_data["message"] = "Analysis failed"
            try:
                info = task_result.info
                if isinstance(info, dict):
                    response_data["error"] = info.get('error', 'Unknown error')
                else:
                    response_data["error"] = str(info) if info else "Unknown error"
            except (ValueError, KeyError) as e:
                response_data["error"] = f"Task failed but error details could not be retrieved: {str(e)}"
            
        elif task_state == 'RETRY':
            response_data["status"] = "retry"
            response_data["message"] = "Task is being retried after an error"
            
        else:
            response_data["status"] = task_state.lower() if isinstance(task_state, str) else "unknown"
            response_data["message"] = f"Task state: {task_state}"
        
        return TaskStatusResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Failed to get task status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.get(
    "/results/{task_id}",
    response_model=AnalysisResults,
    summary="Get analysis results",
    description="Retrieve the complete analysis results for a completed task"
)
async def get_task_results(task_id: str) -> AnalysisResults:
    """
    Get the complete analysis results for a task.
    
    Only available for successfully completed tasks.
    Raises 404 if task not found or not completed.
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        
        if task_result.state == 'PENDING':
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found or not yet started"
            )
        
        if task_result.state == 'PROCESSING' or task_result.state == 'STARTED':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task is still processing. Check status endpoint for progress."
            )
        
        if task_result.state == 'FAILURE':
            error_msg = str(task_result.info) if task_result.info else "Unknown error"
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Task failed: {error_msg}"
            )
        
        if task_result.state != 'SUCCESS':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Task is in {task_result.state} state"
            )
        
        # Get results
        results = task_result.result
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task results not found"
            )
        
        # Cache the results
        if 'pr_summary' in results:
            repo = f"{results.get('repo', 'unknown')}"
            pr_number = results.get('pr_number', 0)
            if repo != 'unknown' and pr_number > 0:
                await cache_service.set_analysis(repo, pr_number, results)
        
        return AnalysisResults(**results)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task results: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task results: {str(e)}"
        )