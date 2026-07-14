from openrouter_cli import sdk_adapter
from openrouter_cli.app import app
from openrouter_cli.sdk_adapter import EmbeddingResult
from tests.fakes import FakeAdapter, build_adapter_factory


def _patch(monkeypatch, fake: FakeAdapter):
    monkeypatch.setattr(sdk_adapter, "build_adapter", build_adapter_factory(fake))


def test_embed_single_input(runner, api_key_env, monkeypatch):
    fake = FakeAdapter(
        embedding_result=EmbeddingResult(model="openai/text-embedding-3-small", embeddings=[[0.1, 0.2]], raw={})
    )
    _patch(monkeypatch, fake)

    result = runner.invoke(
        app, ["embed", "--input", "hello world", "--model", "openai/text-embedding-3-small"]
    )

    assert result.exit_code == 0, result.output
    assert "dim=2" in result.output
    call = fake.calls[0]
    assert call[0] == "embeddings_generate"
    assert call[1]["input"] == "hello world"


def test_embed_multiple_inputs_sent_as_list(runner, api_key_env, monkeypatch):
    fake = FakeAdapter(
        embedding_result=EmbeddingResult(
            model="openai/text-embedding-3-small", embeddings=[[0.1], [0.2]], raw={}
        )
    )
    _patch(monkeypatch, fake)

    result = runner.invoke(
        app,
        [
            "embed", "--input", "doc one", "--input", "doc two",
            "--model", "openai/text-embedding-3-small",
        ],
    )

    assert result.exit_code == 0, result.output
    call = fake.calls[0]
    assert call[1]["input"] == ["doc one", "doc two"]


def test_embed_reads_stdin_when_no_input(runner, api_key_env, monkeypatch):
    fake = FakeAdapter(
        embedding_result=EmbeddingResult(model="openai/text-embedding-3-small", embeddings=[[0.1]], raw={})
    )
    _patch(monkeypatch, fake)

    result = runner.invoke(
        app, ["embed", "--model", "openai/text-embedding-3-small"], input="piped text\n"
    )

    assert result.exit_code == 0, result.output
    call = fake.calls[0]
    assert call[1]["input"] == "piped text"


def test_embed_no_input_no_stdin_is_validation_error(runner, api_key_env, monkeypatch):
    fake = FakeAdapter(embedding_result=EmbeddingResult(model="m", embeddings=[], raw={}))
    _patch(monkeypatch, fake)

    result = runner.invoke(app, ["embed", "--model", "m"], input="")

    assert result.exit_code == 2
    assert not fake.calls


def test_embed_missing_model_is_config_error(runner, api_key_env, monkeypatch):
    fake = FakeAdapter(embedding_result=EmbeddingResult(model="m", embeddings=[], raw={}))
    _patch(monkeypatch, fake)
    monkeypatch.delenv("OPENROUTER_EMBEDDING_MODEL", raising=False)

    result = runner.invoke(app, ["embed", "--input", "hi"])

    assert result.exit_code == 2
    assert not fake.calls
