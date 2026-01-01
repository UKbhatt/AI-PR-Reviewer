class CodeReviewAgentException(Exception):
    """Base exception for the application."""
    pass


class GitHubAPIException(CodeReviewAgentException):
    """Exception raised for GitHub API errors."""
    pass


class LLMException(CodeReviewAgentException):
    """Exception raised for LLM service errors."""
    pass


class TaskNotFoundException(CodeReviewAgentException):
    """Exception raised when task is not found."""
    pass


class CacheException(CodeReviewAgentException):
    """Exception raised for cache operations."""
    pass


class AgentException(CodeReviewAgentException):
    """Exception raised during agent execution."""
    pass


class ValidationException(CodeReviewAgentException):
    """Exception raised for validation errors."""
    pass