from openrouter_cli import sdk_adapter
from openrouter_cli.app import app
from openrouter_cli.sdk_adapter import RerankResult
from tests.fakes import FakeAdapter, build_adapter_factory


def _patch(monkeypatch, fake: FakeAdapter):
    monkeypatch.setattr(sdk_adapter, "build_adapter", build_adapter_factory(fake))


def test_rerank_basic(runner, api_key_env, monkeypatch):
    fake = FakeAdapter(
        rerank_result=RerankResult(
            model="cohere/rerank-v3.5",
            results=[
                {"index": 1, "relevance_score": 0.9, "document": {"text": "nylon manja"}},
                {"index": 0, "relevance_score": 0.2, "document": {"text": "cotton thread"}},
            ],
            raw={},
        )
    )
    _patch(monkeypatch, fake)

    result = runner.invoke(
        app,
        [
            "rerank", "--query", "best kite string",
            "--document", "cotton thread", "--document", "nylon manja",
            "--model", "cohere/rerank-v3.5",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "nylon manja" in result.output
    call = fake.calls[0]
    assert call[0] == "rerank"
    assert call[1]["documents"] == ["cotton thread", "nylon manja"]
    assert call[1]["query"] == "best kite string"


def test_rerank_top_n_passed_through(runner, api_key_env, monkeypatch):
    fake = FakeAdapter(rerank_result=RerankResult(model="m", results=[], raw={}))
    _patch(monkeypatch, fake)

    result = runner.invoke(
        app,
        ["rerank", "--query", "q", "--document", "d", "--model", "m", "--top-n", "1"],
    )

    assert result.exit_code == 0, result.output
    assert fake.calls[0][1]["top_n"] == 1


def test_rerank_missing_model_is_config_error(runner, api_key_env, monkeypatch):
    fake = FakeAdapter(rerank_result=RerankResult(model="m", results=[], raw={}))
    _patch(monkeypatch, fake)
    monkeypatch.delenv("OPENROUTER_RERANK_MODEL", raising=False)

    result = runner.invoke(app, ["rerank", "--query", "q", "--document", "d"])

    assert result.exit_code == 2
    assert not fake.calls
