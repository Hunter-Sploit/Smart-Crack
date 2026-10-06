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
def config(
    wordlist: str = typer.Option(None, help="Set default wordlist path"),
    show: bool = typer.Option(False, "--show", help="Display current configuration"),
    reset: bool = typer.Option(False, "--reset", help="Reset configuration to defaults"),
):
    from smartcrack.config.store import reset_config
    cfg = load_config()
    if reset:
        cfg = reset_config()
        console.print("[yellow]Configuration reset to defaults[/yellow]")
        return
    if wordlist:
        set_default_wordlist(wordlist)
        console.print(f"[green]Default wordlist set:[/green] {wordlist}")
        return
    if show or not wordlist:
        console.print(cfg)


@app.command()
def crack(
    target: str,
    wordlist: str = typer.Option("", help="Path to wordlist"),
    backend: str = typer.Option(None, help="Force backend: hashcat or john"),
    mask: str = typer.Option(None, help="Hashcat mask for brute-force (implies -a 3)"),
    hashcat_mode: int = typer.Option(None, help="Override hashcat mode"),
    rules: str = typer.Option(None, help="Path to rules file (John)"),
):
    """Auto detect target, extract/identify hash and run cracking backend."""
    detection = detect_input(target)
    cfg = load_config()
    wl = wordlist or cfg.get("default_wordlist")

    if not wl:
        raise typer.BadParameter("No wordlist configured. Use `smartcrack config --wordlist <path>` or --wordlist.")

    extracted_hashes = []
    hash_value = target
    hash_input = target
    tmp_hash_file = None

    # Handle archive extraction
    if detection.input_path and detection.kind in {"pdf", "zip", "rar", "7z", "office", "ssh"}:
        extracted_hashes = extract_hash(detection.input_path, detection.kind)
        if extracted_hashes:
            # Write extracted hashes to temp file for backend
            fd, tmp_path = tempfile.mkstemp(suffix=".hash", text=True)
            try:
                with open(fd, "w") as f:
                    for eh in extracted_hashes:
                        f.write(eh.raw_hash + "\n")
                hash_input = tmp_path
                tmp_hash_file = tmp_path
                hash_value = extracted_hashes[0].raw_hash  # for identification
            except Exception:
                Path(tmp_path).unlink(missing_ok=True)
                raise

    # Handle hash dump files - pass directly to backend
    elif detection.kind == "hash_dump" and detection.input_path:
        hash_input = str(detection.input_path)
        # Read first hash for identification
        try:
            first_line = detection.input_path.read_text(errors="ignore").splitlines()[0].strip()
            hash_value = first_line if first_line else target
        except Exception:
            hash_value = target

    # Handle raw hash strings - create temp file if needed
    elif "\n" not in hash_value and not Path(hash_value).exists():
        fd, tmp_path = tempfile.mkstemp(suffix=".hash", text=True)
        try:
            with open(fd, "w") as f:
                f.write(hash_value + "\n")
            tmp_hash_file = tmp_path
            hash_input = tmp_path
        except Exception:
            Path(tmp_path).unlink(missing_ok=True)
            raise

    candidates = identify_hash(hash_value)
    top = candidates[0] if candidates else None

    # Override hashcat mode if provided
    if hashcat_mode and top:
        top = top.__class__(
            name=top.name,
            confidence=top.confidence,
            hashcat_mode=hashcat_mode,
            john_format=top.john_format,
            notes=top.notes + " (manual override)",
        )

    plan = build_plan(hash_input=hash_input, wordlist=wl, candidate=top, preferred=backend, mask=mask, rules=rules)

    console.print({"detection": detection.kind, "confidence": detection.confidence, "reasons": detection.reasons})
    console.print({"plan": plan.command, "rationale": plan.rationale})

    if not plan.command:
        console.print("[red]No cracking backend available. Install hashcat or john.[/red]")
        raise typer.Exit(code=2)

    result = run_command(plan.command, timeout=cfg.get("timeout_seconds", 3600))
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
