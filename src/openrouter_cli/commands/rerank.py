from typing import Optional

import typer

from openrouter_cli.config import get_api_key, get_base_url, get_rerank_model, get_run_ctx
from openrouter_cli.output import echo, emit_result, handle_errors
from openrouter_cli import sdk_adapter


@handle_errors
def rerank(
    query: str = typer.Option(..., "--query", "-q", help="The search query to rank documents against."),
    document: list[str] = typer.Option(
        ..., "--document", "-d", help="A candidate document to rank. Repeatable."
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Rerank model to use. Defaults to $OPENROUTER_RERANK_MODEL."
    ),
    top_n: Optional[int] = typer.Option(None, "--top-n", help="Only return the top N ranked documents."),
) -> None:
    """Rank a set of documents by relevance to a query.

    Examples:
      orouter rerank --query "best kite string" \\
        --document "Barbanne is a nylon string used for kite fighting" \\
        --document "Cotton thread frays quickly against glass-coated manja" \\
        --model cohere/rerank-v3.5 --top-n 1
    """
    run_ctx = get_run_ctx()
    api_key = get_api_key(run_ctx)
    resolved_model = get_rerank_model(model)

    with sdk_adapter.build_adapter(api_key, get_base_url(run_ctx)) as adapter:
        result = adapter.rerank(model=resolved_model, query=query, documents=document, top_n=top_n)

    def render(data):
        for r in data["results"]:
            doc = r.get("document") or {}
            text = doc.get("text") if isinstance(doc, dict) else None
            preview = f": {text[:80]}" if text else ""
            echo(f"[{r['index']}] score={r['relevance_score']:.4f}{preview}")

    emit_result({"model": resolved_model, "results": result.results}, render)
