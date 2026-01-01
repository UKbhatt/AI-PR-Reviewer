from typing import Dict, List, Optional, Any
from github import Github, GithubException
from github.PullRequest import PullRequest
from github.File import File
import logging
from app.config import settings
from app.utils.exceptions import GitHubAPIException


logger = logging.getLogger(__name__)


class GitHubService:
    """Service for interacting with GitHub API."""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub service with authentication."""
        self.token = token or settings.GITHUB_TOKEN
        if not self.token:
            logger.warning("No GitHub token provided, using unauthenticated access")
        self.client = Github(self.token) if self.token else Github()
    
    def get_pull_request(self, repo: str, pr_number: int) -> PullRequest:
        """Fetch pull request details."""
        try:
            repository = self.client.get_repo(repo)
            pr = repository.get_pull(pr_number)
            logger.info(f"Fetched PR #{pr_number} from {repo}")
            return pr
        except GithubException as e:
            logger.error(f"GitHub API error: {e.status} - {e.data}")
            raise GitHubAPIException(f"Failed to fetch PR: {e.data.get('message', str(e))}")
        except Exception as e:
            logger.error(f"Unexpected error fetching PR: {e}")
            raise GitHubAPIException(f"Failed to fetch PR: {str(e)}")
    
    def get_pr_details(self, repo: str, pr_number: int) -> Dict[str, Any]:
        """Get comprehensive PR details."""
        pr = self.get_pull_request(repo, pr_number)
        
        try:
            return {
                "number": pr.number,
                "title": pr.title,
                "description": pr.body or "",
                "state": pr.state,
                "author": pr.user.login,
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat(),
                "base_branch": pr.base.ref,
                "head_branch": pr.head.ref,
                "files_changed": pr.changed_files,
                "additions": pr.additions,
                "deletions": pr.deletions,
                "commits": pr.commits,
                "mergeable": pr.mergeable,
                "draft": pr.draft,
                "labels": [label.name for label in pr.labels],
                "url": pr.html_url
            }
        except Exception as e:
            logger.error(f"Error extracting PR details: {e}")
            raise GitHubAPIException(f"Failed to extract PR details: {str(e)}")
    
    def get_pr_files(self, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """Get list of files changed in the PR."""
        pr = self.get_pull_request(repo, pr_number)
        
        try:
            files_data = []
            for file in pr.get_files():
                files_data.append({
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "patch": file.patch if hasattr(file, 'patch') else None,
                    "raw_url": file.raw_url,
                    "blob_url": file.blob_url
                })
            
            logger.info(f"Fetched {len(files_data)} files from PR #{pr_number}")
            return files_data
        except Exception as e:
            logger.error(f"Error fetching PR files: {e}")
            raise GitHubAPIException(f"Failed to fetch PR files: {str(e)}")
    
    def get_file_content(self, repo: str, file_path: str, ref: str) -> str:
        """Get content of a specific file at a given ref."""
        try:
            repository = self.client.get_repo(repo)
            content = repository.get_contents(file_path, ref=ref)
            
            if isinstance(content, list):
                raise GitHubAPIException(f"{file_path} is a directory, not a file")
            
            return content.decoded_content.decode('utf-8')
        except GithubException as e:
            logger.error(f"GitHub API error fetching file: {e.status} - {e.data}")
            raise GitHubAPIException(f"Failed to fetch file: {e.data.get('message', str(e))}")
        except Exception as e:
            logger.error(f"Error fetching file content: {e}")
            raise GitHubAPIException(f"Failed to fetch file content: {str(e)}")
    
    def get_pr_diff(self, repo: str, pr_number: int) -> str:
        """Get the complete diff for a PR."""
        pr = self.get_pull_request(repo, pr_number)
        
        try:
            # Get all files and combine their patches
            files = pr.get_files()
            diff_parts = []
            
            for file in files:
                if hasattr(file, 'patch') and file.patch:
                    diff_parts.append(f"diff --git a/{file.filename} b/{file.filename}")
                    diff_parts.append(f"--- a/{file.filename}")
                    diff_parts.append(f"+++ b/{file.filename}")
                    diff_parts.append(file.patch)
                    diff_parts.append("")  # Empty line between files
            
            return "\n".join(diff_parts)
        except Exception as e:
            logger.error(f"Error fetching PR diff: {e}")
            raise GitHubAPIException(f"Failed to fetch PR diff: {str(e)}")
    
    def get_pr_commits(self, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """Get list of commits in the PR."""
        pr = self.get_pull_request(repo, pr_number)
        
        try:
            commits_data = []
            for commit in pr.get_commits():
                commits_data.append({
                    "sha": commit.sha,
                    "message": commit.commit.message,
                    "author": commit.commit.author.name,
                    "date": commit.commit.author.date.isoformat(),
                    "url": commit.html_url
                })
            
            return commits_data
        except Exception as e:
            logger.error(f"Error fetching PR commits: {e}")
            raise GitHubAPIException(f"Failed to fetch PR commits: {str(e)}")
    
    def close(self):
        """Close the GitHub client connection."""
        if hasattr(self.client, 'close'):
            self.client.close()