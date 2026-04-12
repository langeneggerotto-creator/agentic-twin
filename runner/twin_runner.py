"""
Twin Runner — CLI entry point for the Digital Twin.

Usage:
  python runner/twin_runner.py "What is the speed of light and derive its significance?"
  python runner/twin_runner.py --mode science "Derive the Schrödinger equation"
  python runner/twin_runner.py --mode image "A human heart showing all four chambers"
  python runner/twin_runner.py --mode architect "Design a real-time chat system for 1M users"
  python runner/twin_runner.py --validate "Existing AI output to validate..."
  python runner/twin_runner.py --server  # Start the REST API server
"""

import argparse
import asyncio
import json
import os
import sys


def _check_api_key():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        print("Export it with: export ANTHROPIC_API_KEY=your_key_here")
        sys.exit(1)


def _banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║           DIGITAL TWIN — AI VALIDATION LAYER v1.0           ║
║  Truth • Accuracy • Scientific Rigour • Correction          ║
╚══════════════════════════════════════════════════════════════╝
""")


def _print_response(response) -> None:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box

    console = Console()

    # Confidence bar
    score = response.overall_confidence
    bar_len = 40
    filled = int(score * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)
    colour = "green" if score >= 0.85 else "yellow" if score >= 0.65 else "red"

    console.print(f"\n[bold]Confidence:[/bold] [{colour}]{bar}[/{colour}] {score:.1%}")
    console.print(f"[bold]Truth Score:[/bold] {response.truth_score:.1%}  "
                  f"[bold]Accuracy:[/bold] {response.accuracy_score:.1%}  "
                  f"[bold]Mode:[/bold] {response.mode_used}  "
                  f"[bold]Rounds:[/bold] {response.processing_rounds}  "
                  f"[bold]Latency:[/bold] {response.latency_ms:.0f}ms")

    # Layer scores table
    if response.layer_scores:
        table = Table(title="Validation Layers", box=box.ROUNDED)
        table.add_column("Layer", style="cyan")
        table.add_column("Score", justify="right")
        table.add_column("Status")
        for ls in response.layer_scores:
            status = "[green]✓ PASS[/green]" if ls.passed else "[red]✗ FAIL[/red]"
            table.add_row(ls.layer, f"{ls.score:.1%}", status)
        console.print(table)

    # Corrections
    if response.corrections_made:
        console.print("\n[bold yellow]Corrections Made:[/bold yellow]")
        for c in response.corrections_made:
            console.print(f"  [yellow]⟳[/yellow] {c}")

    # Warnings
    if response.warnings:
        console.print("\n[bold red]Warnings:[/bold red]")
        for w in response.warnings[:5]:
            console.print(f"  [red]⚠[/red] {w}")

    # Scientific basis
    if response.scientific_basis:
        console.print(Panel(response.scientific_basis, title="Scientific Basis", border_style="blue"))

    # Derived formulas
    if response.derived_formulas:
        console.print("\n[bold blue]Derived Formulas:[/bold blue]")
        for f in response.derived_formulas:
            console.print(f"  [blue]∫[/blue] {f}")

    # Image prompts
    if response.image_prompts:
        console.print("\n[bold magenta]Image Generation Prompts:[/bold magenta]")
        for i, p in enumerate(response.image_prompts, 1):
            console.print(Panel(p, title=f"Prompt {i}", border_style="magenta"))

    # Main output
    console.print(Panel(response.final_output, title="[bold green]Validated Output[/bold green]",
                        border_style="green"))


async def _run_twin(args):
    from core.digital_twin import DigitalTwin, TwinRequest

    twin = DigitalTwin()
    request = TwinRequest(
        query=args.query,
        mode=args.mode,
        target_ai_output=args.validate or None,
        include_scientific_basis=not args.no_science,
        include_image_prompts=args.mode == "image",
        confidence_threshold=args.threshold,
    )

    print(f"Processing in [{args.mode}] mode...")
    response = await twin.aprocess(request)
    return response


def main():
    _check_api_key()
    _banner()

    parser = argparse.ArgumentParser(description="Digital Twin — AI Validation Layer")
    parser.add_argument("query", nargs="?", default="", help="Query or task")
    parser.add_argument("--mode", default="auto",
                        choices=["auto", "validate", "research", "science",
                                 "image", "architect", "code"],
                        help="Processing mode")
    parser.add_argument("--validate", metavar="OUTPUT",
                        help="Validate this existing AI output")
    parser.add_argument("--threshold", type=float, default=0.85,
                        help="Minimum confidence threshold (default: 0.85)")
    parser.add_argument("--no-science", action="store_true",
                        help="Skip scientific basis derivation")
    parser.add_argument("--json", action="store_true",
                        help="Output raw JSON instead of formatted output")
    parser.add_argument("--server", action="store_true",
                        help="Start the REST API server")
    args = parser.parse_args()

    if args.server:
        import uvicorn
        uvicorn.run("api.server:app", host="0.0.0.0", port=8080, reload=True)
        return

    if not args.query and not args.validate:
        parser.print_help()
        sys.exit(1)

    if not args.query:
        args.query = "Validate the provided AI output"

    response = asyncio.run(_run_twin(args))

    if args.json:
        print(json.dumps(response.model_dump(), indent=2))
    else:
        try:
            _print_response(response)
        except ImportError:
            # Fallback if rich not installed
            print(f"\nConfidence: {response.overall_confidence:.1%}")
            print(f"Truth Score: {response.truth_score:.1%}")
            print(f"\nOutput:\n{response.final_output}")
            if response.corrections_made:
                print(f"\nCorrections: {response.corrections_made}")


if __name__ == "__main__":
    main()
