import json
import ollama
from typing import Dict, List, Optional, Any
import logging
from app.config import settings
from app.utils.exceptions import LLMException

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with Ollama LLM."""
    
    def __init__(self):
        """Initialize LLM service."""
        self.client = ollama.Client(host=settings.OLLAMA_BASE_URL)
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate completion from the LLM."""
        try:
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            logger.info(f"Generating completion with model {self.model}")
            
            response = self.client.chat(
                model=self.model,
                messages=messages,
                format="json",
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens or 2048
                }
            )
            
            content = response['message']['content']
            logger.info(f"Generated completion of length {len(content)}")
            return content
            
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            raise LLMException(f"Failed to generate completion: {str(e)}")
    
    def _parse_json(self, response: str) -> Dict[str, Any]:
        json_str = response.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()
        start = json_str.find('{')
        end = json_str.rfind('}')
        if start >= 0 and end > start:
            json_str = json_str[start:end + 1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise LLMException(f"LLM reply was not valid JSON: {response[:200]!r}") from e
    
    def analyze_code(
        self, 
        code: str, 
        file_path: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze code for issues and improvements."""
        
        system_prompt = """You are an expert code reviewer. Analyze the provided code and identify issues.

IMPORTANT: You MUST respond with ONLY valid JSON, no other text. The JSON must have this exact structure:
{
  "issues": [
    {
      "severity": "critical|high|medium|low",
      "category": "bug|style|performance|security|best-practice",
      "title": "Brief title",
      "description": "Detailed description",
      "line_number": null,
      "suggestion": "How to fix it"
    }
  ],
  "summary": "Overall assessment"
}

Return empty issues array if no issues found."""
        
        prompt = f"""Analyze this code from {file_path}.
{f"Context: {context}" if context else ""}

Code:
{code}

Respond with ONLY the JSON object, nothing else."""
        
        response = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=4096
        )
        result = self._parse_json(response)
        logger.info(f"Code analysis parsed: {len(result.get('issues', []))} issues found")
        return result
    
    def analyze_diff(self, diff: str, pr_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze PR diff for issues."""
        
        system_prompt = """You are an expert code reviewer analyzing a pull request diff.
Focus on the changes being made (lines starting with + or -).
Identify issues in the NEW code (lines with +) and improvements over OLD code (lines with -).

IMPORTANT: You MUST respond with ONLY valid JSON, no other text. The JSON must have this exact structure:
{
  "issues": [
    {
      "severity": "critical|high|medium|low",
      "category": "bug|style|performance|security|best-practice",
      "title": "Brief title",
      "description": "Detailed description",
      "file_path": "path/to/file",
      "suggestion": "How to fix it"
    }
  ],
  "positive_changes": ["List of good changes"],
  "summary": "Overall assessment of the changes"
}

Return empty arrays if no issues or positive changes found."""
        
        pr_info = f"""PR Title: {pr_context.get('title', 'N/A')}
PR Description: {pr_context.get('description', 'N/A')}
Files Changed: {pr_context.get('files_changed', 0)}
Additions: {pr_context.get('additions', 0)}
Deletions: {pr_context.get('deletions', 0)}"""
        
        # Limit diff size to avoid token overflow
        diff_preview = diff[:15000] if len(diff) > 15000 else diff
        
        prompt = f"""{pr_info}

Diff:
{diff_preview}

Analyze the changes. Respond with ONLY the JSON object, nothing else."""
        
        response = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=4096
        )
        result = self._parse_json(response)
        logger.info(f"Diff analysis parsed: {len(result.get('issues', []))} issues found")
        return result
    
    def generate_summary(
        self, 
        issues: List[Dict[str, Any]], 
        pr_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate overall summary and recommendations."""
        
        system_prompt = """You are an expert code reviewer providing executive summary and recommendations.
Based on the identified issues and PR context, provide:
1. Overall code quality score (0-100)
2. Executive summary
3. Key recommendations

IMPORTANT: You MUST respond with ONLY valid JSON, no other text. The JSON must have this exact structure:
{
  "overall_score": 85,
  "summary": "The PR introduces...",
  "recommendations": ["Fix critical security issue", "Add tests"]
}"""
        
        issues_summary = "\n".join([
            f"- [{issue['severity']}] {issue['title']}"
            for issue in issues[:20]  # Limit to top 20
        ]) if issues else "No issues found"
        
        prompt = f"""PR: {pr_context.get('title')}
Files Changed: {pr_context.get('files_changed')}
Issues Found: {len(issues)}

Issues:
{issues_summary}

Provide overall assessment. Respond with ONLY the JSON object, nothing else."""
        
        try:
            response = self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.5,
                max_tokens=2048
            )
            result = self._parse_json(response)
        except LLMException as e:
            logger.error(f"Summary generation error: {e}")
            return {
                "overall_score": 50,
                "summary": "Analysis completed with some errors. Review the identified issues.",
                "recommendations": ["Review identified issues", "Consider code improvements"]
            }
        
        # Validate score is between 0-100
        score = result.get('overall_score', 50)
        if isinstance(score, (int, float)):
            result['overall_score'] = max(0, min(100, score))
        else:
            result['overall_score'] = 50
        
        logger.info(f"Summary generated: score={result['overall_score']}")
        return result
    
    def check_health(self) -> bool:
        """Check if LLM service is available."""
        try:
            # Try to list models to check connection
            self.client.list()
            return True
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return False