from dataclasses import dataclass, field


@dataclass(frozen=True)
class Offer:
    id: str
    title: str
    clipped: bool = False
    eligible: bool = True


@dataclass
class RunResult:
    store: str
    dry_run: bool
    started_at: str
    found: int = 0
    previously_clipped: int = 0
    newly_clipped: int = 0
    skipped: int = 0
    failed: int = 0
    duration_seconds: float = 0
    errors: list[str] = field(default_factory=list)
