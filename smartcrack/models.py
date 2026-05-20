from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DetectionResult:
    input_path: Path | None
    kind: str
    confidence: float
    reasons: list[str] = field(default_factory=list)


@dataclass
class ExtractedHash:
    source: str
    raw_hash: str
    hashcat_mode: int | None = None
    john_format: str | None = None


@dataclass
class HashCandidate:
    name: str
    confidence: float
    hashcat_mode: int | None = None
    john_format: str | None = None
    notes: str = ""


@dataclass
class CrackPlan:
    backend: str
    attack_mode: str
    command: list[str]
    rationale: list[str]
    meta: dict[str, Any] = field(default_factory=dict)
