from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
from app.services.github_service import GitHubService
from app.services.llm_service import LLMService
from app.utils.exceptions import AgentException

logger = logging.getLogger(__name__)


class CodeReviewAgent:
    """Autonomous agent for code review analysis."""
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize the code review agent."""
        self.github_service = GitHubService(token=github_token)
        self.llm_service = LLMService()
        self.analysis_state = {
            "phase": "initialized",
            "progress": 0,
            "issues": [],
            "files_analyzed": 0
        }
    
    def update_progress(self, phase: str, progress: int):
        """Update analysis progress."""
        self.analysis_state["phase"] = phase
        self.analysis_state["progress"] = progress
        logger.info(f"Analysis progress: {phase} - {progress}%")
    
    def plan_analysis(self, pr_details: Dict[str, Any]) -> List[str]:
        """Plan the analysis strategy based on PR details."""
        plan = [
            "fetch_pr_metadata",
            "fetch_pr_files",
            "analyze_diff",
            "analyze_individual_files",
            "generate_summary"
        ]
        
        # Adjust plan based on PR size
        files_changed = pr_details.get("files_changed", 0)
        
        if files_changed > 20:
            logger.info("Large PR detected, focusing on diff analysis")
            plan.remove("analyze_individual_files")
        
        logger.info(f"Analysis plan: {' -> '.join(plan)}")
        return plan
    
    def fetch_pr_metadata(self, repo: str, pr_number: int) -> Dict[str, Any]:
        """Fetch PR metadata and details."""
        try:
            self.update_progress("Fetching PR metadata", 10)
            pr_details = self.github_service.get_pr_details(repo, pr_number)
            logger.info(f"Fetched PR metadata: {pr_details['title']}")
            return pr_details
        except Exception as e:
            logger.error(f"Failed to fetch PR metadata: {e}")
            raise AgentException(f"Failed to fetch PR metadata: {str(e)}")
    
    def fetch_pr_files(self, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """Fetch list of files changed in PR."""
        try:
            self.update_progress("Fetching changed files", 20)
            files = self.github_service.get_pr_files(repo, pr_number)
            logger.info(f"Fetched {len(files)} changed files")
            return files
        except Exception as e:
            logger.error(f"Failed to fetch PR files: {e}")
            raise AgentException(f"Failed to fetch PR files: {str(e)}")
    
    def analyze_diff(
        self, 
        repo: str, 
        pr_number: int, 
        pr_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze the PR diff using LLM."""
        try:
            self.update_progress("Analyzing code changes", 40)
            
            # Get the diff
            diff = self.github_service.get_pr_diff(repo, pr_number)
            
            if not diff:
                logger.warning("No diff available for analysis")
                return {"issues": [], "positive_changes": [], "summary": "No changes to analyze"}
            
            # Analyze with LLM
            analysis = self.llm_service.analyze_diff(diff, pr_details)
            
            logger.info(f"Diff analysis complete: {len(analysis.get('issues', []))} issues found")
            return analysis
            
        except Exception as e:
            logger.error(f"Diff analysis failed: {e}", exc_info=True)
            raise AgentException(f"Diff analysis failed: {str(e)}")
    
    def analyze_individual_files(
        self, 
        repo: str, 
        pr_number: int,
        files: List[Dict[str, Any]],
        pr_details: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze individual files for detailed issues."""
        all_issues = []
        
        try:
            self.update_progress("Analyzing individual files", 60)
            
            # Limit to important files to avoid overwhelming the LLM
            important_files = [
                f for f in files 
                if f['status'] != 'removed' and 
                f['changes'] < 500 and  # Skip very large files
                any(f['filename'].endswith(ext) for ext in ['.py', '.js', '.ts', '.java', '.go', '.cpp', '.c'])
            ][:10]  # Analyze max 10 files
            
            total_files = len(important_files)
            
            for idx, file in enumerate(important_files):
                try:
                    # Get file content from patch
                    if file.get('patch'):
                        # Extract added lines from patch
                        added_lines = [
                            line[1:] for line in file['patch'].split('\n') 
                            if line.startswith('+') and not line.startswith('+++')
                        ]
                        code = '\n'.join(added_lines)
                        
                        if code.strip():
                            # Analyze the code
                            analysis = self.llm_service.analyze_code(
                                code=code,
                                file_path=file['filename'],
                                context=pr_details.get('title', '')
                            )
                            
                            # Add file path to issues
                            for issue in analysis.get('issues', []):
                                issue['file_path'] = file['filename']
                                all_issues.append(issue)
                    
                    self.analysis_state["files_analyzed"] += 1
                    progress = 60 + int((idx + 1) / total_files * 20)
                    self.update_progress("Analyzing individual files", progress)
                    
                except Exception as e:
                    logger.warning(f"Failed to analyze file {file['filename']}: {e}")
                    continue
            
            logger.info(f"Analyzed {total_files} files, found {len(all_issues)} issues")
            return all_issues
            
        except Exception as e:
            logger.error(f"File analysis failed: {e}", exc_info=True)
            raise AgentException(f"File analysis failed: {str(e)}")
    
    def generate_summary(
        self, 
        all_issues: List[Dict[str, Any]], 
        pr_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate overall summary and recommendations."""
        try:
            self.update_progress("Generating summary", 90)
            
            summary_data = self.llm_service.generate_summary(all_issues, pr_details)
            
            logger.info("Summary generated successfully")
            return summary_data
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}", exc_info=True)
            raise AgentException(f"Summary generation failed: {str(e)}")
    
    def execute(self, repo: str, pr_number: int) -> Dict[str, Any]:
        """Execute the complete code review analysis."""
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting analysis for {repo}#{pr_number}")
            
            # Phase 1: Fetch PR metadata
            pr_details = self.fetch_pr_metadata(repo, pr_number)
            
            # Phase 2: Plan analysis
            analysis_plan = self.plan_analysis(pr_details)
            
            # Phase 3: Fetch files
            files = self.fetch_pr_files(repo, pr_number)
            
            # Phase 4: Analyze diff
            diff_analysis = self.analyze_diff(repo, pr_number, pr_details)
            all_issues = diff_analysis.get('issues', [])
            
            # Phase 5: Analyze individual files (if in plan)
            if "analyze_individual_files" in analysis_plan:
                file_issues = self.analyze_individual_files(repo, pr_number, files, pr_details)
                all_issues.extend(file_issues)
            
            # Remove duplicates based on title and file_path
            unique_issues = []
            seen = set()
            for issue in all_issues:
                key = (issue.get('title'), issue.get('file_path'))
                if key not in seen:
                    seen.add(key)
                    unique_issues.append(issue)
            
            # Phase 6: Generate summary
            summary_data = self.generate_summary(unique_issues, pr_details)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            self.update_progress("Complete", 100)
            
            # Compile final results
            results = {
                "pr_summary": {
                    "title": pr_details.get("title", ""),
                    "description": pr_details.get("description", ""),
                    "author": pr_details.get("author", ""),
                    "files_changed": pr_details.get("files_changed", 0),
                    "additions": pr_details.get("additions", 0),
                    "deletions": pr_details.get("deletions", 0),
                    "commits": pr_details.get("commits", 0)
                },
                "issues": unique_issues,
                "overall_score": summary_data.get("overall_score", 50),
                "summary": summary_data.get("summary", ""),
                "recommendations": summary_data.get("recommendations", []),
                "analyzed_at": datetime.now().isoformat(),
                "processing_time": processing_time,
                "files_analyzed": self.analysis_state["files_analyzed"]
            }
            
            logger.info(f"Analysis complete: {len(unique_issues)} issues, score: {results['overall_score']}")
            return results
            
        except Exception as e:
            logger.error(f"Analysis execution failed: {e}")
            raise AgentException(f"Analysis failed: {str(e)}")
        finally:
            # Cleanup
            self.github_service.close()