import pytest
from app.agents.code_review_agent import CodeReviewAgent
from app.utils.exceptions import AgentException, GitHubAPIException, LLMException

PR_DETAILS = {"title": "Fix", "description": "", "author": "a", "files_changed": 1,
              "additions": 2, "deletions": 1, "commits": 1}
FILES = [{"filename": "a.py", "status": "modified", "changes": 3, "patch": "+x = 1"}]


class StubGitHub:
    def __init__(self, fail_with=None):
        self.fail_with = fail_with

    def get_pr_details(self, repo, pr_number):
        if self.fail_with:
            raise self.fail_with
        return PR_DETAILS

    def get_pr_files(self, repo, pr_number):
        return FILES

    def get_pr_diff(self, repo, pr_number):
        return "diff --git a/a.py b/a.py\n+x = 1"

    def close(self):
        pass


class StubLLM:
    def __init__(self, file_analysis_fails=False):
        self.file_analysis_fails = file_analysis_fails

    def analyze_diff(self, diff, pr_context):
        return {"issues": [{"title": "Diff issue", "file_path": "a.py", "severity": "low",
                            "category": "style", "description": "d"}], "summary": "s"}

    def analyze_code(self, code, file_path, context=None):
        if self.file_analysis_fails:
            raise LLMException("not json")
        return {"issues": [{"title": "File issue", "severity": "low", "category": "style",
                            "description": "d"}], "summary": "s"}

    def generate_summary(self, issues, pr_context):
        return {"overall_score": 80, "summary": "ok", "recommendations": []}


def agent_with(github, llm):
    agent = CodeReviewAgent()
    agent.github_service = github
    agent.llm_service = llm
    return agent


def test_execute_results_identify_the_analyzed_pr():
    agent = agent_with(StubGitHub(), StubLLM())

    results = agent.execute("owner/repo", 42)

    assert (results["repo"], results["pr_number"]) == ("owner/repo", 42)


def test_execute_keeps_original_failure_as_cause_without_rewrapping():
    agent = agent_with(StubGitHub(fail_with=GitHubAPIException("Bad credentials")), StubLLM())

    with pytest.raises(AgentException) as raised:
        agent.execute("owner/repo", 42)

    assert str(raised.value) == "Failed to fetch PR metadata: Bad credentials"
    assert isinstance(raised.value.__cause__, GitHubAPIException)


def test_execute_skips_a_file_whose_analysis_fails_and_keeps_diff_issues():
    agent = agent_with(StubGitHub(), StubLLM(file_analysis_fails=True))

    results = agent.execute("owner/repo", 42)

    assert [i["title"] for i in results["issues"]] == ["Diff issue"]
