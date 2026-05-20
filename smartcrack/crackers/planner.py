from __future__ import annotations

from smartcrack.models import CrackPlan, HashCandidate
from smartcrack.utils.subprocess_safe import which


def choose_backend(candidate: HashCandidate | None, preferred: str | None = None) -> str:
    if preferred:
        return preferred
    hashcat = which("hashcat")
    john = which("john")
    if candidate and candidate.hashcat_mode is not None and hashcat:
        return "hashcat"
    if john:
        return "john"
    return "unknown"


def build_plan(hash_input: str, wordlist: str, candidate: HashCandidate | None, preferred: str | None = None) -> CrackPlan:
    backend = choose_backend(candidate, preferred=preferred)
    rationale = []
    if candidate:
        rationale.append(f"Detected {candidate.name} ({candidate.confidence:.0%})")
    rationale.append(f"Selected backend: {backend}")

    if backend == "hashcat" and candidate and candidate.hashcat_mode is not None:
        command = ["hashcat", "-m", str(candidate.hashcat_mode), "-a", "0", hash_input, wordlist]
    elif backend == "john":
        command = ["john", f"--wordlist={wordlist}", hash_input]
        if candidate and candidate.john_format:
            command.insert(1, f"--format={candidate.john_format}")
    else:
        command = []
        rationale.append("No cracking backend detected in PATH")

    return CrackPlan(backend=backend, attack_mode="dictionary", command=command, rationale=rationale)
