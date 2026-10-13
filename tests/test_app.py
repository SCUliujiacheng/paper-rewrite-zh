import httpx
import pytest
from fastapi.testclient import TestClient

from paper_rewrite.app import create_app
from paper_rewrite.model import LocalModel


@pytest.fixture
def client():
    def respond(request):
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        return httpx.Response(200, json={"content": "本实验共重复5次。", "stop_type": "eos"})

    app = create_app(model=LocalModel(transport=httpx.MockTransport(respond)))
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        yield client


def test_actual_rewrite_route_checks_and_returns_output(client):
    response = client.post(
        "/api/rewrite", json={"text": "实验重复5次。", "language": "zh", "candidates": 1}
    )
    assert response.status_code == 200
    assert response.json()["output"] == "本实验共重复5次。"
    assert response.json()["detector_status"] == "not_run"


def test_cross_origin_cannot_trigger_model_or_read_health(client):
    assert (
        client.post(
            "/api/rewrite", headers={"Origin": "https://evil.test"}, json={"text": "hello"}
        ).status_code
        == 403
    )
    assert client.get("/api/health", headers={"Origin": "null"}).status_code == 403
    assert client.get("/api/health", headers={"Origin": "http://127.0.0.1:8765"}).status_code == 200


def test_dns_rebinding_host_rejected(client):
    assert client.get("/api/health", headers={"Host": "evil.test"}).status_code == 400


def test_request_body_and_field_limits(client):
    assert (
        client.post(
            "/api/check", content="x" * 160001, headers={"Content-Type": "application/json"}
        ).status_code
        == 413
    )
    assert client.post("/api/rewrite", json={"text": "x" * 12001}).status_code == 422
    assert client.post("/api/rewrite", json={"text": "  "}).status_code == 422
    assert client.post("/api/rewrite", json={"text": "ok", "candidates": 4}).status_code == 422
    assert (
        client.post(
            "/api/rewrite", json={"text": "ok", "model_url": "https://evil.test"}
        ).status_code
        == 422
    )


def test_check_endpoint_flags_changed_fact(client):
    reply = client.post(
        "/api/check", json={"source": "准确率为80%。", "candidate": "准确率为90%。"}
    )
    assert reply.status_code == 200
    assert reply.json()["blocked"]


def test_detector_consent_required_even_without_configured_key(client):
    assert (
        client.post(
            "/api/detect", json={"source": "one", "candidate": "two", "consent": False}
        ).json()["status"]
        == "not_run"
    )
    assert (
        client.post(
            "/api/detect", json={"source": "one", "candidate": "two", "consent": True}
        ).json()["status"]
        == "not_configured"
    )


def test_health_no_key_or_endpoint_secrets_and_security_headers(client):
    response = client.get("/api/health")
    assert response.json()["model_ready"] is True
    assert "api_key" not in response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_validation_does_not_echo_manuscript(client):
    response = client.post("/api/rewrite", json={"text": "PRIVATE-PAPER", "language": "bad"})
    assert response.status_code == 422
    assert "PRIVATE-PAPER" not in response.text


def test_second_concurrent_rewrite_is_busy():
    import asyncio

    async def run():
        started = asyncio.Event()
        finish = asyncio.Event()

        class WaitingModel:
            name = "test"

            async def complete(self, text, seed=0, protected_terms=()):
                started.set()
                await finish.wait()
                return "本实验重复5次。"

        app = create_app(model=WaitingModel())
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app), base_url="http://127.0.0.1"
        ) as session:
            task = asyncio.create_task(session.post("/api/rewrite", json={"text": "实验重复5次。"}))
            await started.wait()
            other = await session.post("/api/rewrite", json={"text": "实验重复5次。"})
            finish.set()
            await task
            assert other.status_code == 429

    asyncio.run(run())


def test_check_endpoint_protects_blockquoted_fenced_code(client):
    reply = client.post(
        "/api/check",
        json={
            "source": "> ```python\n> result = first + second\n> ```",
            "candidate": "> ```python\n> result = first - second\n> ```",
        },
    )
    assert reply.status_code == 200
    assert reply.json()["blocked"]
    assert any(issue["code"] == "code" for issue in reply.json()["issues"])


def test_app_uses_configured_qwen_factory_and_passes_terms(monkeypatch):
    import json

    import paper_rewrite.app as app_module
    from paper_rewrite.model import create_model

    monkeypatch.setenv("PAPER_MODEL_BACKEND", "qwen")
    monkeypatch.setenv("PAPER_MODEL_NAME", "qwen-test-alias")

    def respond(request):
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        assert request.url.path == "/v1/chat/completions"
        body = json.loads(request.content)
        assert body["model"] == "qwen-test-alias"
        assert "Protected terms:\nBM25\n\n" in body["messages"][1]["content"]
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": "BM25适用于检索。"},
                    }
                ]
            },
        )

    def factory(**kwargs):
        return create_model(transport=httpx.MockTransport(respond), **kwargs)

    def old_constructor(*args, **kwargs):
        pytest.fail("App bypassed the configured backend factory")

    monkeypatch.setattr(app_module, "create_model", factory, raising=False)
    monkeypatch.setattr(app_module, "LocalModel", old_constructor, raising=False)
    with TestClient(app_module.create_app(), base_url="http://127.0.0.1") as session:
        assert session.get("/api/health").json()["model"] == "qwen-test-alias"
        response = session.post(
            "/api/rewrite",
            json={"text": "BM25用于检索。", "protected_terms": ["BM25"], "candidates": 1},
        )
    assert response.status_code == 200
    assert response.json()["output"] == "BM25适用于检索。"
    assert response.json()["model"] == "qwen-test-alias"
