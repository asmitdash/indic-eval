"""indic-eval v2.1 CLI.

Subcommands:
  evaluate    run the v2.1 benchmark against any model adapter and emit reports
  list        list samples in the seed (or any) dataset
  validate    validate a JSON dataset against the schema
  demo        run golden-mock + broken-mock for quick spec sanity check
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from .adapters import build_adapter
from .dataset import filter_samples, load_from_file, load_seed
from .judge import OpusDevJudge, build_prod_judge
from .pipeline import RunOptions, run_evaluation
from .report import render_markdown, write_reports

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


@click.group()
def cli():
    """indic-eval v2.1 — Indian-context AI benchmark."""


@cli.command("evaluate")
@click.option("--model", "model_spec", required=True,
              help="Adapter spec: bedrock | sarvam | krutrim | openai | openai-compat | mock | golden-mock | broken-mock")
@click.option("--model-id", default=None, help="Override model ID (e.g. sarvam-2, gpt-4-turbo, claude-opus-4-7)")
@click.option("--api-key", default=None, help="API key (for OpenAI-compat vendors). Defaults to OPENAI_API_KEY env.")
@click.option("--base-url", default=None, help="Override base URL for OpenAI-compat vendors")
@click.option("--dataset", "dataset_path", default=None, help="Path to dataset JSON (defaults to v2.1 seed)")
@click.option("--layer", "layers", multiple=True, help="Filter by layer (research/industry/reliability/safety/quality)")
@click.option("--language", "languages", multiple=True, help="Filter by language code (hi, en, mr, ...)")
@click.option("--max-per-layer", type=int, default=None, help="Cap samples per layer (faster runs)")
@click.option("--judge", "judge_spec", default="none", show_default=True,
               type=click.Choice(["none", "dev", "prod", "claude", "gpt", "gemini",
                                   "claude+gpt", "claude+gemini", "gpt+gemini",
                                   "claude+gpt+gemini"]),
               help="Quality-layer judge. 'none' = F1 fallback. 'dev' = Opus 4.7 single. "
                    "'prod' = all three (claude+gpt+gemini). Or pick any combination.")
@click.option("--out-dir", default="reports", show_default=True, help="Where to write JSON/MD/HTML")
@click.option("--basename", default=None, help="Output filename prefix (defaults to model name)")
@click.option("--temperature", default=0.0, type=float, show_default=True)
@click.option("--max-tokens", default=512, type=int, show_default=True)
def evaluate(model_spec, model_id, api_key, base_url, dataset_path, layers, languages,
              max_per_layer, judge_spec, out_dir, basename, temperature, max_tokens):
    """Run the v2.1 benchmark against a model and emit JSON + Markdown + HTML reports."""
    console = Console()

    # Load samples
    if dataset_path:
        samples = load_from_file(dataset_path)
    else:
        samples = load_seed()

    samples = filter_samples(
        samples,
        layers=list(layers) if layers else None,
        languages=list(languages) if languages else None,
        max_per_layer=max_per_layer,
    )
    if not samples:
        console.print("[bold red]No samples after filtering.[/]")
        raise click.Abort()
    console.print(f"[bold]Loaded {len(samples)} samples[/] across "
                  f"{len(set(s.layer.value for s in samples))} layers, "
                  f"{len(set(s.language for s in samples))} languages.")

    # Build adapter
    kwargs = {}
    if model_id is not None:
        if model_spec.lower() == "bedrock":
            kwargs["model_id"] = model_id
        else:
            kwargs["model"] = model_id
    if api_key is not None:
        kwargs["api_key"] = api_key
    if base_url is not None:
        kwargs["base_url"] = base_url
    if model_spec.lower() in ("golden-mock", "broken-mock"):
        kwargs["samples"] = samples

    adapter = build_adapter(model_spec, **kwargs)
    console.print(f"[bold cyan]Adapter:[/] {adapter.name} (vendor={adapter.vendor})")

    # Optional judge — supports 1/2/3 model combinations
    judge_obj = None
    if judge_spec != "none":
        if judge_spec == "dev":
            console.print("[bold]Judge:[/] Opus 4.7 dev-mode single-judge (advisory; not publishable as IES)")
            judge_obj = OpusDevJudge()
        else:
            # Resolve panel selection
            if judge_spec == "prod":
                use_gpt, use_claude, use_gemini = True, True, True
            else:
                parts = set(judge_spec.split("+"))
                use_gpt = "gpt" in parts
                use_claude = "claude" in parts
                use_gemini = "gemini" in parts
            judge_obj = build_prod_judge(
                use_gpt=use_gpt, use_claude=use_claude, use_gemini=use_gemini,
            )
            chosen = []
            if use_claude: chosen.append("Claude")
            if use_gpt:    chosen.append("GPT")
            if use_gemini: chosen.append("Gemini")
            agg = "median" if len(chosen) >= 3 else ("mean" if len(chosen) == 2 else "single")
            console.print(f"[bold]Judge:[/] {' + '.join(chosen)} ({agg}, vendor recusal)")

    # Run
    console.print(f"[bold]Running evaluation...[/]")
    options = RunOptions(temperature=temperature, max_tokens=max_tokens)
    scorecard = run_evaluation(adapter, samples, judge=judge_obj, options=options)

    # Print summary
    console.print()
    console.print("[bold green]── Scorecard ──────────────────────────────────[/]")
    summary = scorecard.summary()
    for k, v in summary.items():
        console.print(f"  {k:14}  {v}")
    console.print("[bold green]───────────────────────────────────────────────[/]")

    # Write reports
    out_dir_path = Path(out_dir)
    base = basename or scorecard.model_name.replace("/", "_").replace(":", "_")
    paths = write_reports(scorecard, out_dir_path, basename=base)
    console.print()
    console.print("[bold]Reports written:[/]")
    for kind, p in paths.items():
        console.print(f"  {kind:10}  {p}")

    # Exit code: non-zero if gate triggered (useful for CI)
    if scorecard.certification_gate_triggered:
        console.print("[bold red]✗ Certification Gate triggered — exit code 1[/]")
        sys.exit(1)


@cli.command("list")
@click.option("--dataset", "dataset_path", default=None)
def list_cmd(dataset_path):
    """List samples in the dataset."""
    samples = load_from_file(dataset_path) if dataset_path else load_seed()
    console = Console()
    t = Table(title=f"v2.1 Dataset ({len(samples)} samples)")
    t.add_column("ID", style="cyan")
    t.add_column("Layer")
    t.add_column("Domain")
    t.add_column("Lang")
    t.add_column("Diff")
    t.add_column("Task")
    t.add_column("Question", overflow="fold", max_width=50)
    for s in samples:
        t.add_row(s.id, s.layer.value, s.domain, s.language, s.difficulty.value,
                  s.task_type.value, s.question[:80])
    console.print(t)


@cli.command("validate")
@click.argument("dataset_path", type=click.Path(exists=True))
def validate(dataset_path):
    """Validate a JSON dataset against the v2.1 schema."""
    console = Console()
    try:
        samples = load_from_file(dataset_path)
    except Exception as e:
        console.print(f"[bold red]✗ Validation failed:[/] {e}")
        sys.exit(2)
    console.print(f"[bold green]✓ {len(samples)} samples valid.[/]")
    by_layer = {}
    for s in samples:
        by_layer[s.layer.value] = by_layer.get(s.layer.value, 0) + 1
    for k, v in sorted(by_layer.items()):
        console.print(f"  {k:14}  {v}")


@cli.command("demo")
@click.option("--out-dir", default="reports", show_default=True)
def demo(out_dir):
    """Run golden-mock + broken-mock for spec sanity check (no API keys needed)."""
    console = Console()
    samples = load_seed()
    console.print(f"[bold]Running demo on {len(samples)} samples (golden + broken mock).[/]")

    for spec in ("golden-mock", "broken-mock"):
        adapter = build_adapter(spec, samples=samples)
        scorecard = run_evaluation(adapter, samples, judge=None)
        paths = write_reports(scorecard, Path(out_dir), basename=spec)
        console.print(f"\n[bold cyan]{spec}[/]: IES={scorecard.overall_score:.1f}  "
                      f"cert={scorecard.certification.value}  "
                      f"gate={scorecard.certification_gate_triggered}")
        for kind, p in paths.items():
            console.print(f"  {kind:10}  {p}")


def main():
    cli()


if __name__ == "__main__":
    main()
