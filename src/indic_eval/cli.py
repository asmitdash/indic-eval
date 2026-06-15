"""indic-eval CLI.

Subcommands:
  list-benchmarks         show shipped benchmarks
  run --model bedrock|echo|scripted --benchmark <id> [--max N]
  run-all --model ...     run every benchmark and emit a Scorecard JSON
  serve-leaderboard       run the FastAPI leaderboard
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


@click.group()
def cli() -> None:
    """indic-eval — eval harness, observability SDK, leaderboard for Indic LLMs."""


@cli.command("list-benchmarks")
def list_benchmarks() -> None:
    from .benchmarks.loader import load_all
    console = Console()
    benchmarks = load_all()
    t = Table(title=f"Indic Benchmarks ({len(benchmarks)})")
    t.add_column("ID", style="bold cyan")
    t.add_column("Name")
    t.add_column("Examples", justify="right")
    t.add_column("Primary metric")
    for b in benchmarks:
        t.add_row(b.id, b.name, str(len(b.examples)), b.primary_metric)
    console.print(t)


def _build_adapter(kind: str, model_id: Optional[str]) -> object:
    if kind == "echo":
        from .benchmarks.adapters import EchoAdapter
        return EchoAdapter()
    if kind == "bedrock":
        from .benchmarks.adapters import BedrockClaudeAdapter
        return BedrockClaudeAdapter(model_id=model_id or "global.anthropic.claude-opus-4-7")
    if kind == "scripted":
        from .benchmarks.adapters import ScriptedAdapter
        return ScriptedAdapter(model_id="scripted-test", scripted={}, default="ok")
    raise click.UsageError(f"Unknown adapter kind: {kind}")


@cli.command("run")
@click.option("--model", "model_kind", required=True, type=click.Choice(["echo", "bedrock", "scripted"]))
@click.option("--model-id", default=None, help="Override model id (e.g. global.anthropic.claude-opus-4-7)")
@click.option("--benchmark", "benchmark_id", required=True, help="Benchmark id (see list-benchmarks)")
@click.option("--max", "max_examples", type=int, default=None)
@click.option("--out", "out_path", type=click.Path(), default=None, help="Save scorecard JSON")
def run_one(model_kind: str, model_id: Optional[str], benchmark_id: str,
             max_examples: Optional[int], out_path: Optional[str]) -> None:
    from .benchmarks.loader import load_all, BENCHMARK_REGISTRY
    from .harness.runner import run_benchmark

    benchmarks = {b.id: b for b in load_all()}
    if benchmark_id not in benchmarks:
        raise click.UsageError(f"Unknown benchmark {benchmark_id}; known: {sorted(benchmarks)}")
    b = benchmarks[benchmark_id]
    scorer_name = BENCHMARK_REGISTRY.get(benchmark_id, "exact_match")

    adapter = _build_adapter(model_kind, model_id)
    result = run_benchmark(adapter, b, scorer_name=scorer_name, max_examples=max_examples)

    console = Console()
    console.print(f"[bold]{result.benchmark_name}[/]  primary_score={result.primary_score:.4f}  "
                   f"{result.n_passed}/{result.n_examples} passed")
    for k, v in result.metric_aggregates.items():
        console.print(f"  {k:20} {v:.4f}")

    if out_path:
        Path(out_path).write_text(result.model_dump_json(indent=2), encoding="utf-8")
        console.print(f"[dim]wrote {out_path}[/]")


@cli.command("run-all")
@click.option("--model", "model_kind", required=True, type=click.Choice(["echo", "bedrock", "scripted"]))
@click.option("--model-id", default=None)
@click.option("--max", "max_examples", type=int, default=None)
@click.option("--out", "out_path", type=click.Path(), default="scorecard.json")
def run_all_cmd(model_kind: str, model_id: Optional[str], max_examples: Optional[int],
                  out_path: str) -> None:
    from .benchmarks.loader import load_all, BENCHMARK_REGISTRY
    from .harness.runner import run_all

    adapter = _build_adapter(model_kind, model_id)
    benchmarks = load_all()
    card = run_all(adapter, benchmarks, scorer_for=BENCHMARK_REGISTRY,
                    max_examples=max_examples,
                    notes=f"Run by indic-eval CLI; adapter={model_kind}")
    Path(out_path).write_text(card.model_dump_json(indent=2), encoding="utf-8")

    console = Console()
    console.print(f"[bold green]Scorecard written[/]: {out_path}")
    console.print(json.dumps(card.to_summary(), indent=2))


@cli.command("serve-leaderboard")
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=8090, type=int)
@click.option("--store-file", default=None, help="JSON-Lines file path; in-memory if unset")
def serve(host: str, port: int, store_file: Optional[str]) -> None:
    import uvicorn
    from .leaderboard.api import build_app
    from .leaderboard.store import FileLeaderboardStore, MemoryLeaderboardStore

    store = FileLeaderboardStore(store_file) if store_file else MemoryLeaderboardStore()
    app = build_app(store=store)
    uvicorn.run(app, host=host, port=port)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
