from pydantic import BaseModel, Field, validator
from typing import Optional


class AnalyzePRRequest(BaseModel):
    """Request model for PR analysis."""
    
    repo: str = Field(
        ...,
        description="Repository in format 'owner/repo'",
        example="facebook/react"
    )
    pr_number: int = Field(
        ...,
        description="Pull request number",
        gt=0,
        example=12345
    )
    github_token: Optional[str] = Field(
        None,
        description="GitHub personal access token (optional)"
    )
    
    @validator("repo")
    def validate_repo_format(cls, v):
        """Validate repository format."""
        if "/" not in v or v.count("/") != 1:
            raise ValueError("Repository must be in format 'owner/repo'")
        owner, repo = v.split("/")
        if not owner or not repo:
            raise ValueError("Owner and repo name cannot be empty")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "repo": "facebook/react",
                "pr_number": 12345,
                "github_token": "ghp_xxxxxxxxxxxx"
            }
        }