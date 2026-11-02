import pytest
from app.core.celery_app import celery_app
from app.tasks import analysis_tasks
from app.utils.exceptions import AgentException


class FailingAgent:
    constructions = 0

    def __init__(self, github_token=None):
        FailingAgent.constructions += 1
        self.analysis_state = {"files_analyzed": 0}

    def update_progress(self, phase, progress):
        pass

    def execute(self, repo, pr_number):
        raise AgentException("Failed to fetch PR metadata: Bad credentials")


@pytest.fixture
def eager_failing_task(monkeypatch):
    celery_app.conf.update(task_always_eager=True, task_eager_propagates=False,
                           task_store_eager_result=False)
    monkeypatch.setattr(analysis_tasks, "CodeReviewAgent", FailingAgent)
    recorded_states = []
    monkeypatch.setattr(analysis_tasks.analyze_pr_task, "update_state",
                        lambda state=None, meta=None, **kw: recorded_states.append(state))
    FailingAgent.constructions = 0
    yield recorded_states
    celery_app.conf.update(task_always_eager=False)


def test_failed_analysis_surfaces_the_agent_error_without_retrying(eager_failing_task):
    result = analysis_tasks.analyze_pr_task.apply(args=["owner/repo", 1, None])

    assert result.state == "FAILURE"
    assert isinstance(result.result, AgentException)
    assert "Bad credentials" in str(result.result)
    assert FailingAgent.constructions == 1


def test_failed_analysis_leaves_failure_bookkeeping_to_celery(eager_failing_task):
    analysis_tasks.analyze_pr_task.apply(args=["owner/repo", 1, None])

    assert "FAILURE" not in eager_failing_task


class SucceedingAgent(FailingAgent):
    def execute(self, repo, pr_number):
        return {"pr_summary": {}, "issues": []}


@pytest.fixture
def eager_succeeding_task(monkeypatch):
    from cryptography.fernet import Fernet
    from app.config import settings
    from app.core.token_crypto import encrypt_token
    celery_app.conf.update(task_always_eager=True, task_eager_propagates=True,
                           task_store_eager_result=False)
    monkeypatch.setattr(settings, "TOKEN_ENCRYPTION_KEY", Fernet.generate_key().decode())
    monkeypatch.setattr(analysis_tasks, "CodeReviewAgent", SucceedingAgent)
    monkeypatch.setattr(analysis_tasks.analyze_pr_task, "update_state", lambda **kw: None)
    yield encrypt_token
    celery_app.conf.update(task_always_eager=False)


def test_results_record_whether_a_token_was_used(eager_succeeding_task):
    encrypt_token = eager_succeeding_task

    anonymous = analysis_tasks.analyze_pr_task.apply(args=["owner/repo", 1, None]).result
    authenticated = analysis_tasks.analyze_pr_task.apply(
        args=["owner/repo", 1, encrypt_token("ghp_x")]).result

    assert (anonymous["authenticated"], authenticated["authenticated"]) == (False, True)
