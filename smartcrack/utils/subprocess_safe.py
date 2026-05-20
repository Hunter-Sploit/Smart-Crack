from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


@dataclass
class CommandResult:
    code: int
    stdout: str
    stderr: str


def which(binary: str) -> str | None:
    return shutil.which(binary)


def run_command(command: list[str]) -> CommandResult:
    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    return CommandResult(code=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)
