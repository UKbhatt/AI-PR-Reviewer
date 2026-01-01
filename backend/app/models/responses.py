from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    STARTED = "started"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"


class AnalyzePRResponse(BaseModel):
    """Response model for PR analysis submission."""
    
    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    message: str = Field(..., description="Status message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "abc123-def456-ghi789",
                "status": "pending",
                "message": "PR analysis task submitted successfully"
            }
        }


class TaskStatusResponse(BaseModel):
    """Response model for task status check."""
    
    task_id: str = Field(..., description="Task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    progress: Optional[int] = Field(None, description="Progress percentage (0-100)")
    message: Optional[str] = Field(None, description="Status message")
    created_at: Optional[datetime] = Field(None, description="Task creation time")
    started_at: Optional[datetime] = Field(None, description="Task start time")
    completed_at: Optional[datetime] = Field(None, description="Task completion time")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "abc123-def456-ghi789",
                "status": "processing",
                "progress": 45,
                "message": "Analyzing code changes...",
                "created_at": "2024-01-15T10:30:00Z",
                "started_at": "2024-01-15T10:30:05Z"
            }
        }


class CodeIssue(BaseModel):
    """Represents a code issue found during analysis."""
    
    severity: str = Field(..., description="Issue severity: critical, high, medium, low")
    category: str = Field(..., description="Issue category")
    title: str = Field(..., description="Issue title")
    description: str = Field(..., description="Detailed description")
    file_path: Optional[str] = Field(None, description="File path")
    line_number: Optional[int] = Field(None, description="Line number")
    suggestion: Optional[str] = Field(None, description="Suggested fix")
    code_snippet: Optional[str] = Field(None, description="Code snippet")


class PRSummary(BaseModel):
    """Pull request summary information."""
    
    title: str
    description: Optional[str]
    author: str
    files_changed: int
    additions: int
    deletions: int
    commits: int


class AnalysisResults(BaseModel):
    """Complete analysis results."""
    
    task_id: str
    pr_summary: PRSummary
    issues: List[CodeIssue]
    overall_score: float = Field(..., ge=0, le=100, description="Overall code quality score")
    summary: str = Field(..., description="Executive summary of the review")
    recommendations: List[str] = Field(..., description="Key recommendations")
    analyzed_at: datetime
    processing_time: float = Field(..., description="Processing time in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "abc123-def456-ghi789",
                "pr_summary": {
                    "title": "Add new authentication feature",
                    "author": "johndoe",
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
                        "description": "User input is directly concatenated into SQL query",
                        "file_path": "src/database.py",
                        "line_number": 45,
                        "suggestion": "Use parameterized queries"
                    }
                ],
                "overall_score": 78.5,
                "summary": "The PR introduces a new authentication feature with generally good code quality...",
                "recommendations": [
                    "Fix the SQL injection vulnerability in database.py",
                    "Add unit tests for the new authentication flow"
                ],
                "analyzed_at": "2024-01-15T10:35:00Z",
                "processing_time": 45.2
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    redis_connected: bool = Field(..., description="Redis connection status")
    celery_active: bool = Field(..., description="Celery worker status")
    timestamp: datetime = Field(..., description="Current timestamp")