import json
import pytest
from app.services.llm_service import LLMService
from app.utils.exceptions import LLMException


class StubChatClient:
    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        return {"message": {"content": self.reply}}


def service_replying(reply):
    service = LLMService()
    service.client = StubChatClient(reply)
    return service


DIFF_RESULT = {
    "issues": [{"severity": "high", "category": "bug", "title": "Off by one",
                "description": "Loop bound", "file_path": "a.py", "suggestion": "Use <="}],
    "positive_changes": [],
    "summary": "One bug",
}


def test_analyze_diff_returns_issues_from_json_reply():
    service = service_replying(json.dumps(DIFF_RESULT))

    result = service.analyze_diff("diff --git a/a.py", {"title": "t"})

    assert result["issues"][0]["title"] == "Off by one"


def test_analyze_diff_accepts_json_wrapped_in_code_fence():
    service = service_replying("```json\n" + json.dumps(DIFF_RESULT) + "\n```")

    result = service.analyze_diff("diff", {"title": "t"})

    assert len(result["issues"]) == 1


def test_analyze_diff_raises_when_reply_is_not_json():
    service = service_replying("Sure! Here is my review in prose.")

    with pytest.raises(LLMException):
        service.analyze_diff("diff", {"title": "t"})


def test_analyze_code_raises_when_reply_is_not_json():
    service = service_replying("not json at all")

    with pytest.raises(LLMException):
        service.analyze_code("print(1)", "a.py")


def test_generate_requests_json_formatted_output_from_ollama():
    service = service_replying("{}")

    service.generate("prompt")

    assert service.client.calls[0]["format"] == "json"


def test_generate_summary_falls_back_to_neutral_score_when_reply_is_not_json():
    service = service_replying("no json here")

    result = service.generate_summary([], {"title": "t"})

    assert result["overall_score"] == 50
