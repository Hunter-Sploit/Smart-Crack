from __future__ import annotations

import tempfile
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from smartcrack.config.store import load_config, set_default_wordlist
from smartcrack.crackers.planner import build_plan
from smartcrack.detectors.input_detector import detect_input
from smartcrack.extractors.john_extractors import extract_hash
from smartcrack.identifiers.hash_identifier import identify_hash
from smartcrack.sessions.store import write_session
from smartcrack.utils.subprocess_safe import run_command

app = typer.Typer(help="SmartCrack: intelligent wrapper for hash extraction and cracking workflows")
console = Console()


@app.command()
def identify(target: str):
    """Identify likely hash algorithm for a hash string or file."""
    if Path(target).exists():
        data = Path(target).read_text(errors="ignore")
    else:
        data = target
    lines = [ln for ln in data.splitlines() if ln.strip()] or [data]

    table = Table(title="Identification Results")
    table.add_column("Input")
    table.add_column("Candidate")
    table.add_column("Confidence")
    table.add_column("Hashcat")
    table.add_column("John")

    for ln in lines[:50]:
        cands = identify_hash(ln)
        if not cands:
            table.add_row(ln[:20], "Unknown", "-", "-", "-")
            continue
        top = cands[0]
        table.add_row(ln[:20], top.name, f"{top.confidence:.0%}", str(top.hashcat_mode or "-"), top.john_format or "-")
    console.print(table)


@app.command()
def config(wordlist: str = typer.Option(None, help="Set default wordlist path")):
    cfg = load_config()
    if wordlist:
        set_default_wordlist(wordlist)
        console.print(f"[green]Default wordlist set:[/green] {wordlist}")
        return
    console.print(cfg)


@app.command()
def crack(target: str, wordlist: str = "", backend: str = typer.Option(None), mask: str = typer.Option(None)):
    """Auto detect target, extract/identify hash and run cracking backend."""
    detection = detect_input(target)
    cfg = load_config()
    wl = wordlist or cfg.get("default_wordlist")

    if not wl:
        raise typer.BadParameter("No wordlist configured. Use `smartcrack config --wordlist <path>` or --wordlist.")

    extracted_hashes = []
    hash_value = target

    if detection.input_path and detection.kind in {"pdf", "zip", "rar", "7z", "office", "ssh"}:
        extracted_hashes = extract_hash(detection.input_path, detection.kind)
        if extracted_hashes:
            hash_value = extracted_hashes[0].raw_hash

    candidates = identify_hash(hash_value)
    top = candidates[0] if candidates else None

    tmp_hash_file = None
    hash_input = hash_value
    if "\n" not in hash_value and not Path(hash_value).exists():
        f = tempfile.NamedTemporaryFile("w", delete=False, suffix=".hash")
        f.write(hash_value + "\n")
        f.close()
        tmp_hash_file = f.name
        hash_input = tmp_hash_file

    plan = build_plan(hash_input=hash_input, wordlist=wl, candidate=top, preferred=backend)
    if mask and plan.backend == "hashcat" and plan.command:
        plan.command = ["hashcat", "-a", "3", hash_input, mask]

    console.print({"detection": detection.kind, "confidence": detection.confidence, "reasons": detection.reasons})
    console.print({"plan": plan.command, "rationale": plan.rationale})

    if not plan.command:
        raise typer.Exit(code=2)

    result = run_command(plan.command)
    console.print(result.stdout or result.stderr)

    write_session(
        {
            "target": target,
            "detected_kind": detection.kind,
            "hash_candidates": [c.__dict__ for c in candidates],
            "plan": plan.__dict__,
            "return_code": result.code,
        }
    )

    if tmp_hash_file:
        Path(tmp_hash_file).unlink(missing_ok=True)


if __name__ == "__main__":
    app()
