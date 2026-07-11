import requests

from utils.http import get_with_retry


class _FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code


def test_returns_immediately_on_success(monkeypatch):
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        return _FakeResponse(200)

    monkeypatch.setattr(requests, "get", fake_get)
    resp = get_with_retry("http://example.test", base_delay=0)
    assert resp.status_code == 200
    assert len(calls) == 1


def test_retries_on_retryable_status_then_succeeds(monkeypatch):
    responses = iter([_FakeResponse(503), _FakeResponse(503), _FakeResponse(200)])
    monkeypatch.setattr(requests, "get", lambda url, **kwargs: next(responses))

    resp = get_with_retry("http://example.test", base_delay=0)
    assert resp.status_code == 200


def test_retries_on_connection_error_then_succeeds(monkeypatch):
    attempts = {"n": 0}

    def fake_get(url, **kwargs):
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise requests.exceptions.ConnectionError("boom")
        return _FakeResponse(200)

    monkeypatch.setattr(requests, "get", fake_get)
    resp = get_with_retry("http://example.test", base_delay=0)
    assert resp.status_code == 200
    assert attempts["n"] == 3


def test_raises_last_exception_after_max_attempts(monkeypatch):
    def fake_get(url, **kwargs):
        raise requests.exceptions.Timeout("always fails")

    monkeypatch.setattr(requests, "get", fake_get)
    try:
        get_with_retry("http://example.test", max_attempts=3, base_delay=0)
        assert False, "should have raised"
    except requests.exceptions.Timeout:
        pass


def test_returns_last_response_after_exhausting_retryable_statuses(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda url, **kwargs: _FakeResponse(503))
    resp = get_with_retry("http://example.test", max_attempts=2, base_delay=0)
    assert resp.status_code == 503
