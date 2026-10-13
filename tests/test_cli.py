import json
import subprocess
import sys


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "paper_rewrite.cli", *map(str, args)],
        capture_output=True,
        encoding="utf-8",
    )


def test_cli_check_exports_real_findings_without_model(tmp_path):
    source = tmp_path / "source.txt"
    candidate = tmp_path / "candidate.txt"
    source.write_text("实验重复5次。", encoding="utf-8")
    candidate.write_text("实验重复7次。", encoding="utf-8")
    result = run_cli("check", source, candidate)
    assert result.returncode == 2
    assert json.loads(result.stdout)["blocked"] is True


def test_cli_check_requires_review_even_if_no_obvious_difference(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("研究仍有局限。", encoding="utf-8")
    result = run_cli("check", source, source)
    assert result.returncode == 0
    assert json.loads(result.stdout)["requires_review"] is True


def test_cli_unavailable_model_does_not_write_fake_success(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("实验重复5次。", encoding="utf-8")
    output = tmp_path / "output.txt"
    result = run_cli("rewrite", source, "-o", output, "--model-url", "http://127.0.0.1:1")
    assert result.returncode == 3
    assert not output.exists()


def test_cli_never_overwrites_original_input(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("original", encoding="utf-8")
    result = run_cli("rewrite", source, "-o", source, "--model-url", "http://127.0.0.1:1")
    assert result.returncode != 0
    assert source.read_text(encoding="utf-8") == "original"


def test_cli_backend_option_selects_qwen_and_exports_model_identity(tmp_path, monkeypatch):
    import httpx

    import paper_rewrite.cli as cli_module
    from paper_rewrite.model import create_model

    source = tmp_path / "source.txt"
    source.write_text("BM25用于检索。", encoding="utf-8")
    output, report = tmp_path / "output.txt", tmp_path / "report.json"

    def respond(request):
        assert request.url.path == "/v1/chat/completions"
        body = json.loads(request.content)
        assert body["temperature"] == 0.7
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

    monkeypatch.delenv("PAPER_MODEL_NAME", raising=False)
    monkeypatch.setattr(
        cli_module,
        "create_model",
        lambda *args, **kwargs: create_model(
            *args, transport=httpx.MockTransport(respond), **kwargs
        ),
        raising=False,
    )
    result = cli_module.main(
        [
            "rewrite",
            str(source),
            "-o",
            str(output),
            "--report",
            str(report),
            "--backend",
            "qwen",
            "--keep",
            "BM25",
            "--candidates",
            "1",
        ]
    )
    assert result == 0
    assert output.read_text(encoding="utf-8") == "BM25适用于检索。"
    assert json.loads(report.read_text(encoding="utf-8"))["model"] == "qwen3.5-4b"
