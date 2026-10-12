from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from smartcrack.config.settings import load_config, reset_config, set_default_wordlist
from smartcrack.detectors.input_detector import DetectionResult, detect_input
from smartcrack.extractors.john_extractors import extract_hash
from smartcrack.identifiers.hash_identifier import get_identification_table_data, identify_hash
from smartcrack.sessions.store import write_session
from smartcrack.utils.subprocess_safe import run_command, which

app = typer.Typer(name="smartcrack", help="SmartCrack: identify hashes and crack with hashcat/john")
console = Console()


@app.command()
def identify(
    target: str,
    wordlist: str = typer.Option("wordlist.txt", "--wordlist", "-w", help="Wordlist for command examples"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Identify hash type(s) and show ready-to-use hashcat/john commands."""
    if Path(target).exists():
        data = Path(target).read_text(errors="ignore")
    else:
        data = target
    lines = [ln.strip() for ln in data.splitlines() if ln.strip() and not ln.strip().startswith("#")] or [data]

    all_results: list[dict[str, Any]] = []
    for ln in lines[:50]:
        cands = identify_hash(ln, wordlist)
        if not cands:
            all_results.append({"input": ln[:80], "candidates": [{"candidate": "Unknown", "confidence": "0%", "hashcat_mode": "-", "john_format": "-", "hashcat_cmd": "-", "john_cmd": "-", "notes": "no match"}]})
            continue
        all_results.append({"input": ln[:80], "candidates": get_identification_table_data(cands)})

    if json_output:
        import json
        console.print_json(json.dumps(all_results))
        return

    for result in all_results:
        if len(all_results) > 1:
            console.print(f"\n[bold]Input:[/bold] {result['input']}")
        table = Table(title="Identification Results" if len(all_results) == 1 else None)
        table.add_column("Candidate")
        table.add_column("Conf.")
        table.add_column("Hashcat Mode")
        table.add_column("John Format")
        table.add_column("Hashcat Command")
        table.add_column("John Command")
        table.add_column("Notes")

        for c in result["candidates"]:  # type: ignore[index]
            table.add_row(
                c["candidate"],
                c["confidence"],
                c["hashcat_mode"],
                c["john_format"],
                c["hashcat_cmd"],
                c["john_cmd"],
                c["notes"]
            )
        console.print(table)


@app.command()
def config(
    wordlist: str = typer.Option(None, help="Set default wordlist path"),
    show: bool = typer.Option(False, "--show", help="Display current configuration"),
    reset: bool = typer.Option(False, "--reset", help="Reset configuration to defaults"),
) -> None:
    """Manage configuration."""
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


def _prepare_hash_input(target: str, detection: DetectionResult) -> tuple[str, str, str | None]:
    """Prepare hash input for cracking backend. Returns (hash_input_path, hash_value, temp_file_to_cleanup)."""
    extracted_hashes = []
    hash_value = target
    hash_input = target
    tmp_hash_file = None

    if detection.input_path and detection.kind in {"pdf", "zip", "rar", "7z", "office", "ssh"}:
        extracted_hashes = extract_hash(detection.input_path, detection.kind)
        if extracted_hashes:
            fd, tmp_path = tempfile.mkstemp(suffix=".hash", text=True)
            try:
                with open(fd, "w") as f:
                    f.writelines(eh.raw_hash + "\n" for eh in extracted_hashes)
                hash_input = tmp_path
                tmp_hash_file = tmp_path
                hash_value = extracted_hashes[0].raw_hash
            except OSError:
                Path(tmp_path).unlink(missing_ok=True)
                raise

    elif detection.kind == "hash_dump" and detection.input_path:
        hash_input = str(detection.input_path)
        try:
            first_line = detection.input_path.read_text(errors="ignore").splitlines()[0].strip()
            hash_value = first_line if first_line else target
        except (OSError, UnicodeDecodeError):
            hash_value = target

    elif "\n" not in hash_value and not Path(hash_value).exists():
        fd, tmp_path = tempfile.mkstemp(suffix=".hash", text=True)
        try:
            with open(fd, "w") as f:
                f.write(hash_value + "\n")
            tmp_hash_file = tmp_path
            hash_input = tmp_path
        except OSError:
            Path(tmp_path).unlink(missing_ok=True)
            raise

    return hash_input, hash_value, tmp_hash_file


@app.command()
def crack(
    target: str,
    toolname: str = typer.Option(..., "--toolname", "-t", help="Cracking tool: hashcat or john"),
    hashcat_mode: int = typer.Option(None, "--hashcat-mode", "-m", help="Override auto-detected hashcat mode"),
    john_format: str = typer.Option(None, "--john-format", "-f", help="Override auto-detected john format"),
    wordlist: str = typer.Option(None, "--wordlist", "-w", help="Path to wordlist"),
    mask: str = typer.Option(None, "--mask", help="Hashcat mask for brute-force (implies -a 3)"),
    rules: str = typer.Option(None, "--rules", help="Path to rules file (John)"),
) -> None:
    """Crack hash using specified tool. Auto-detects mode/format unless overridden."""
    toolname = toolname.lower()
    if toolname not in {"hashcat", "john"}:
        raise typer.BadParameter("toolname must be 'hashcat' or 'john'")

    detection = detect_input(target)
    cfg = load_config()
    wl = wordlist or cfg.get("default_wordlist")

    if not wl and not mask:
        raise typer.BadParameter("No wordlist configured. Use `smartcrack config --wordlist <path>` or --wordlist.")

    assert wl is not None  # for mypy

    hash_input, hash_value, tmp_hash_file = _prepare_hash_input(target, detection)

    candidates = identify_hash(hash_value, wl or "wordlist.txt")
    top = candidates[0] if candidates else None

    if toolname == "hashcat":
        if not which("hashcat"):
            console.print("[red]hashcat not found in PATH[/red]")
            raise typer.Exit(code=2)
        mode = hashcat_mode or (top.hashcat_mode if top else None)
        if mode is None and not mask:
            console.print("[red]No hashcat mode detected. Use --hashcat-mode or --mask.[/red]")
            raise typer.Exit(code=2)
        if mask:
            command = ["hashcat", "-a", "3", hash_input, mask]
        else:
            command = ["hashcat", "-m", str(mode), "-a", "0", hash_input, wl]
    else:
        if not which("john"):
            console.print("[red]john not found in PATH[/red]")
            raise typer.Exit(code=2)
        fmt = john_format or (top.john_format if top else None)
        command = ["john", f"--wordlist={wl}", hash_input]
        if fmt:
            command.insert(1, f"--format={fmt}")
        if rules:
            command.append(f"--rules={rules}")

    console.print(f"[bold]Running:[/bold] {' '.join(command)}")

    result = run_command(command, timeout=cfg.get("timeout_seconds", 3600))
    console.print(result.stdout or result.stderr)

    if wl:
        set_default_wordlist(wl)

    write_session(
        {
            "target": target,
            "tool": toolname,
            "detected_kind": detection.kind,
            "hash_candidates": [c.__dict__ for c in candidates],
            "command": command,
            "return_code": result.code,
        }
    )

    if tmp_hash_file:
        Path(tmp_hash_file).unlink(missing_ok=True)


if __name__ == "__main__":
    app()