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
from smartcrack.identifiers.hash_identifier import (
    extract_hash_from_credential_string,
    get_identification_table_data,
    identify_hash,
)
from smartcrack.sessions.store import write_session
from smartcrack.utils.subprocess_safe import run_command, which

app = typer.Typer(name="smartcrack", help="SmartCrack: identify hashes and crack with hashcat/john")
console = Console()


@app.command()
def identify(
    target: str = typer.Argument(None, help="Hash string, dump line, or file path to identify"),
    wordlist: str = typer.Option("wordlist.txt", "--wordlist", "-w", help="Wordlist for command examples"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Identify hash type(s) and show ready-to-use hashcat/john commands."""
    if not target:
        target = typer.prompt("Enter hash, dump line, or file path to identify", default="")
        if not target.strip():
            console.print("[yellow]No input provided. Usage: smartcrack identify <hash_or_file>[/yellow]")
            return

    target = target.strip()
    target_path = Path(target)
    if target_path.exists() and target_path.is_file():
        data = target_path.read_text(errors="ignore")
    else:
        data = target

    lines = [
        ln.strip()
        for ln in data.splitlines()
        if ln.strip() and not ln.strip().startswith(("#", "//", ";"))
    ] or [data.strip()]

    all_results: list[dict[str, Any]] = []
    for ln in lines[:50]:
        cands = identify_hash(ln, wordlist)
        if not cands:
            all_results.append({
                "input": ln[:80],
                "candidates": [{
                    "candidate": "Unknown",
                    "confidence": "0%",
                    "hashcat_mode": "-",
                    "john_format": "-",
                    "hashcat_cmd": "-",
                    "john_cmd": "-",
                    "notes": "no matching pattern or heuristic"
                }]
            })
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

    elif detection.kind in {"hash_dump", "hash_list"} and detection.input_path:
        hash_input = str(detection.input_path)
        try:
            lines = [
                ln.strip()
                for ln in detection.input_path.read_text(errors="ignore").splitlines()
                if ln.strip() and not ln.strip().startswith(("#", "//", ";"))
            ]
            first_line = lines[0] if lines else target
            clean_hash, _, _ = extract_hash_from_credential_string(first_line)
            hash_value = clean_hash
        except (OSError, UnicodeDecodeError, IndexError):
            hash_value = target

    elif "\n" not in hash_value and not Path(hash_value).exists():
        clean_h, _, _ = extract_hash_from_credential_string(hash_value)
        fd, tmp_path = tempfile.mkstemp(suffix=".hash", text=True)
        try:
            with open(fd, "w") as f:
                f.write(clean_h + "\n")
            tmp_hash_file = tmp_path
            hash_input = tmp_path
            hash_value = clean_h
        except OSError:
            Path(tmp_path).unlink(missing_ok=True)
            raise

    return hash_input, hash_value, tmp_hash_file


@app.command()
def crack(
    target: str = typer.Argument(None, help="Hash string or file path to crack"),
    toolname: str = typer.Option(None, "--toolname", "-t", help="Cracking tool: hashcat or john (auto-detected if omitted)"),
    hashcat_mode: int = typer.Option(None, "--hashcat-mode", "-m", help="Override auto-detected hashcat mode"),
    john_format: str = typer.Option(None, "--john-format", "-f", help="Override auto-detected john format"),
    wordlist: str = typer.Option(None, "--wordlist", "-w", help="Path to wordlist"),
    mask: str = typer.Option(None, "--mask", help="Hashcat mask for brute-force (implies -a 3)"),
    rules: str = typer.Option(None, "--rules", help="Path to rules file (John)"),
) -> None:
    """Crack hash using specified tool. Auto-detects mode/format and tool unless overridden."""
    if not target:
        target = typer.prompt("Enter hash string or file path to crack", default="")
        if not target.strip():
            console.print("[yellow]No target provided. Usage: smartcrack crack <target>[/yellow]")
            return

    target = target.strip()
    detection = detect_input(target)
    cfg = load_config()
    wl = wordlist or cfg.get("default_wordlist")

    if not wl and not mask:
        # Check standard fallback wordlists
        candidates_wl = [
            Path("wordlist_sample.txt"),
            Path(__file__).parent.parent / "wordlist_sample.txt",
            Path("/usr/share/wordlists/rockyou.txt"),
            Path("/usr/share/john/password.lst"),
        ]
        for c_wl in candidates_wl:
            if c_wl.exists():
                wl = str(c_wl)
                console.print(f"[cyan]Using detected wordlist:[/cyan] {wl}")
                break

    if not wl and not mask:
        wl_prompt = typer.prompt("Enter path to wordlist (or press Enter to cancel)", default="")
        if wl_prompt.strip():
            wl = wl_prompt.strip()
        else:
            console.print(
                "[red]Error: Wordlist required for dictionary cracking.[/red]\n"
                "Tip: Provide --wordlist <path>, or configure default:\n"
                "     smartcrack config --wordlist /path/to/wordlist.txt\n"
                "     or brute-force with --mask (e.g. --mask ?d?d?d?d)"
            )
            raise typer.Exit(code=2)

    hash_input, hash_value, tmp_hash_file = _prepare_hash_input(target, detection)

    candidates = identify_hash(hash_value, wl or "wordlist.txt")
    top = candidates[0] if candidates else None

    # Check available binaries
    has_hashcat = bool(which("hashcat"))
    has_john = bool(which("john"))

    # Auto-detect tool if not explicitly specified
    if not toolname:
        if not has_hashcat and not has_john:
            console.print(
                "[red]Neither 'hashcat' nor 'john' was found in your system PATH.[/red]\n"
                "Please install a cracking tool:\n"
                "  • Ubuntu/Debian: sudo apt-get install hashcat john\n"
                "  • macOS: brew install hashcat john\n"
                "  • Windows: download from hashcat.net or openwall.com/john"
            )
            if tmp_hash_file:
                Path(tmp_hash_file).unlink(missing_ok=True)
            raise typer.Exit(code=2)

        if has_hashcat and top and top.hashcat_mode is not None:
            toolname = "hashcat"
        elif has_john and top and top.john_format is not None:
            toolname = "john"
        elif has_hashcat:
            toolname = "hashcat"
        else:
            toolname = "john"
        console.print(f"[cyan]Auto-detected cracking tool:[/cyan] {toolname}")
    else:
        toolname = toolname.lower()
        if toolname not in {"hashcat", "john"}:
            console.print("[red]Error: toolname must be 'hashcat' or 'john'[/red]")
            if tmp_hash_file:
                Path(tmp_hash_file).unlink(missing_ok=True)
            raise typer.Exit(code=2)

    if toolname == "hashcat":
        if not which("hashcat"):
            console.print("[red]hashcat not found in PATH[/red]")
            if tmp_hash_file:
                Path(tmp_hash_file).unlink(missing_ok=True)
            raise typer.Exit(code=2)
        mode = hashcat_mode if hashcat_mode is not None else (top.hashcat_mode if top else None)
        if mode is None and not mask:
            console.print("[red]No hashcat mode detected. Use --hashcat-mode or --mask.[/red]")
            if tmp_hash_file:
                Path(tmp_hash_file).unlink(missing_ok=True)
            raise typer.Exit(code=2)
        if mask:
            command = ["hashcat", "-a", "3", hash_input, mask]
            if mode is not None:
                command.insert(1, "-m")
                command.insert(2, str(mode))
        else:
            command = ["hashcat", "-m", str(mode), "-a", "0", hash_input, wl]
    else:
        if not which("john"):
            console.print("[red]john not found in PATH[/red]")
            if tmp_hash_file:
                Path(tmp_hash_file).unlink(missing_ok=True)
            raise typer.Exit(code=2)
        fmt = john_format or (top.john_format if top else None)
        command = ["john"]
        if wl:
            command.append(f"--wordlist={wl}")
        if fmt:
            command.append(f"--format={fmt}")
        if rules:
            command.append(f"--rules={rules}")
        command.append(hash_input)

    console.print(f"[bold]Running:[/bold] {' '.join(command)}")

    result = run_command(command, timeout=cfg.get("timeout_seconds", 3600))
    console.print(result.stdout or result.stderr)

    if wl and Path(wl).exists():
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