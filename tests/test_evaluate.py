import asyncio
import importlib.util
import json
from pathlib import Path

import httpx

from paper_rewrite.model import LocalModel, create_model


def test_evaluation_counts_retained_cases_not_success(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "evaluate", Path(__file__).parents[1] / "scripts/evaluate.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def respond(request):
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        return httpx.Response(200, json={"content": "实验重复999次。", "stop_type": "eos"})

    monkeypatch.setattr(
        module,
        "create_model",
        lambda *args, **kwargs: create_model(
            *args, transport=httpx.MockTransport(respond), **kwargs
        ),
        raising=False,
    )
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(
        json.dumps(
            {"id": "test", "text": "实验重复5次。", "language": "zh", "protected_terms": []}
        ),
        encoding="utf-8",
    )
    result = asyncio.run(module.evaluate(corpus, "http://127.0.0.1", 1))
    assert result["totals"]["zh"]["changed_cases"] == 0
    assert result["totals"]["zh"]["rejected_candidates"] == 1
    assert result["totals"]["zh"]["hard_blocked_candidates"] == 1
    assert result["totals"]["zh"]["warning_only_withheld_candidates"] == 0
    assert result["detector_evaluation"] == "not_run_no_commercial_credentials"
    assert result["model_artifact"] is None
    assert result["runtime"] is None
    assert result["backend_identity_verification"] == "not_verified"


def test_model_provenance_hashes_supplied_file_not_an_assumed_model(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "evaluate", Path(__file__).parents[1] / "scripts/evaluate.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    model = tmp_path / "custom.gguf"
    model.write_bytes(b"abc")
    result = module.artifact_metadata(model, "example/model", "revision-1")
    assert result == {
        "file": "custom.gguf",
        "repo": "example/model",
        "revision": "revision-1",
        "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        "size_bytes": 3,
        "provenance": "local_file_verified_server_binding_not_verified",
    }


def test_evaluation_separates_warning_withheld_from_hard_rejection(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "evaluate", Path(__file__).parents[1] / "scripts/evaluate.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def respond(request):
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        return httpx.Response(200, json={"content": "结果一定适用于室温。", "stop_type": "eos"})

    model = LocalModel(transport=httpx.MockTransport(respond))
    model.prompt_profile = "test_profile"
    monkeypatch.setattr(module, "create_model", lambda *args, **kwargs: model, raising=False)
    # Hand-known SHA256 of abc tests hashing of actual configured instruction bytes.
    model.instruction = "abc"
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(
        json.dumps(
            {
                "id": "warning",
                "text": "结果可能适用于室温。",
                "language": "zh",
                "protected_terms": [],
            }
        ),
        encoding="utf-8",
    )
    result = asyncio.run(module.evaluate(corpus, "http://127.0.0.1", 1))
    totals = result["totals"]["zh"]
    assert totals["changed_cases"] == 0
    assert totals["rejected_candidates"] == 0
    assert totals["hard_blocked_candidates"] == 0
    assert totals["warning_only_withheld_candidates"] == 1
    assert result["selection_policy"] == "no_audit_issues_v1"
    assert result["prompt_profile"] == "test_profile"
    assert result["prompt_instruction_sha256"] == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_evaluator_reports_and_uses_actual_temperature(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "evaluate", Path(__file__).parents[1] / "scripts/evaluate.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def respond(request):
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        assert json.loads(request.content)["temperature"] == 0.35
        return httpx.Response(200, json={"content": "本实验重复5次。", "stop_type": "eos"})

    monkeypatch.setattr(
        module,
        "create_model",
        lambda *args, **kwargs: create_model(
            *args, transport=httpx.MockTransport(respond), **kwargs
        ),
        raising=False,
    )
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(
        json.dumps(
            {"id": "sampling", "text": "实验重复5次。", "language": "zh", "protected_terms": []}
        ),
        encoding="utf-8",
    )
    result = asyncio.run(module.evaluate(corpus, "http://127.0.0.1", 1, temperature=0.35))
    assert result["temperature"] == 0.35
    assert result["cases"][0]["report"]["output"] == "本实验重复5次。"


def test_qwen_evaluation_metadata_uses_backend_default_and_actual_instruction(
    tmp_path, monkeypatch
):
    spec = importlib.util.spec_from_file_location(
        "evaluate", Path(__file__).parents[1] / "scripts/evaluate.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def respond(request):
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        body = json.loads(request.content)
        assert body["temperature"] == 0.7
        assert body["messages"][0]["content"] == "abc"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": "本实验重复5次。"},
                    }
                ]
            },
        )

    def factory(*args, **kwargs):
        model = create_model(*args, transport=httpx.MockTransport(respond), **kwargs)
        model.instruction = "abc"
        return model

    monkeypatch.setattr(module, "create_model", factory, raising=False)
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(
        json.dumps(
            {"id": "qwen", "text": "实验重复5次。", "language": "zh", "protected_terms": []}
        ),
        encoding="utf-8",
    )
    result = asyncio.run(module.evaluate(corpus, "http://127.0.0.1", 1, backend="qwen"))
    assert result["model"] == "qwen3.5-4b"
    assert result["backend"] == "qwen"
    assert result["temperature"] == 0.7
    assert result["prompt_profile"] == "qwen_academic_editing_chat_v3_literal"
    assert result["prompt_instruction_sha256"] == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )
