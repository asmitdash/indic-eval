"""Thin observability SDK. Drop into your app, log every LLM call, run detectors.

Design:
- `Tracer.log_call(...)` is the only call site — non-blocking, no I/O on hot path
  if a non-file store is used.
- Storage is pluggable (memory for tests, file for hobby, Postgres for prod).
- Detectors run offline against a window of logs, not on the hot path.
"""
from __future__ import annotations
import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Protocol
from uuid import uuid4

from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deployment: str = Field(description="App / service name calling the LLM")
    model_id: str
    provider: str = ""
    language_hint: Optional[str] = Field(default=None, description="ISO code if known (hi, ta, hi-en, ...)")
    prompt: str
    output: str
    latency_ms: int = 0
    cost_usd: Optional[float] = None
    user_id_hash: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LogStore(Protocol):
    def append(self, entry: LogEntry) -> None: ...
    def recent(self, deployment: str, n: int = 100) -> list[LogEntry]: ...
    def all(self, deployment: Optional[str] = None) -> list[LogEntry]: ...


class MemoryLogStore:
    """In-memory store with a hard cap. For tests + hobby."""

    def __init__(self, max_entries: int = 100_000):
        self._lock = threading.Lock()
        self._entries: list[LogEntry] = []
        self._max = max_entries

    def append(self, entry: LogEntry) -> None:
        with self._lock:
            self._entries.append(entry)
            if len(self._entries) > self._max:
                self._entries = self._entries[-self._max:]

    def recent(self, deployment: str, n: int = 100) -> list[LogEntry]:
        with self._lock:
            matched = [e for e in self._entries if e.deployment == deployment]
        return matched[-n:]

    def all(self, deployment: Optional[str] = None) -> list[LogEntry]:
        with self._lock:
            entries = list(self._entries)
        if deployment:
            entries = [e for e in entries if e.deployment == deployment]
        return entries


class FileLogStore:
    """JSON-Lines file store. One file per deployment. Append-only.

    Production-ready up to mid-volume — replace with Postgres or S3 for scale.
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _path(self, deployment: str) -> Path:
        # Keep filenames safe: alphanumerics, dash, underscore.
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in deployment)
        return self.root / f"{safe}.jsonl"

    def append(self, entry: LogEntry) -> None:
        line = entry.model_dump_json() + "\n"
        with self._lock:
            with self._path(entry.deployment).open("a", encoding="utf-8") as f:
                f.write(line)

    def _read_all(self, p: Path) -> list[LogEntry]:
        if not p.exists():
            return []
        out: list[LogEntry] = []
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(LogEntry.model_validate_json(line))
                except Exception:
                    continue
        return out

    def recent(self, deployment: str, n: int = 100) -> list[LogEntry]:
        return self._read_all(self._path(deployment))[-n:]

    def all(self, deployment: Optional[str] = None) -> list[LogEntry]:
        if deployment:
            return self._read_all(self._path(deployment))
        # Concat all jsonl files
        out: list[LogEntry] = []
        for p in sorted(self.root.glob("*.jsonl")):
            out.extend(self._read_all(p))
        return out


class Tracer:
    """Drop into your app. Wrap LLM calls with `tracer.log_call(...)`.

    Usage:
        tracer = Tracer(deployment="customer-bot", model_id="claude-opus-4-7", store=...)
        with tracer.span(prompt) as span:
            response = client.messages.create(...).content[0].text
            span.set_output(response)
        # span auto-records latency, appends to store on exit
    """

    def __init__(self, deployment: str, model_id: str, store: LogStore,
                 provider: str = "", language_hint: Optional[str] = None):
        self.deployment = deployment
        self.model_id = model_id
        self.store = store
        self.provider = provider
        self.language_hint = language_hint

    def log_call(self, prompt: str, output: str, *, latency_ms: int = 0,
                  cost_usd: Optional[float] = None, language_hint: Optional[str] = None,
                  metadata: Optional[dict] = None) -> LogEntry:
        entry = LogEntry(
            deployment=self.deployment, model_id=self.model_id, provider=self.provider,
            language_hint=language_hint or self.language_hint,
            prompt=prompt, output=output, latency_ms=latency_ms, cost_usd=cost_usd,
            metadata=metadata or {},
        )
        self.store.append(entry)
        return entry

    def span(self, prompt: str, *, language_hint: Optional[str] = None,
              metadata: Optional[dict] = None) -> "_Span":
        return _Span(self, prompt, language_hint=language_hint, metadata=metadata)


class _Span:
    def __init__(self, tracer: Tracer, prompt: str, *, language_hint: Optional[str] = None,
                  metadata: Optional[dict] = None):
        self._tracer = tracer
        self._prompt = prompt
        self._lang = language_hint
        self._metadata = dict(metadata or {})
        self._output = ""
        self._cost: Optional[float] = None
        self._t0 = 0.0

    def __enter__(self) -> "_Span":
        self._t0 = time.monotonic()
        return self

    def set_output(self, text: str) -> None:
        self._output = text

    def set_cost(self, cost_usd: float) -> None:
        self._cost = cost_usd

    def set_metadata(self, **kw: Any) -> None:
        self._metadata.update(kw)

    def __exit__(self, exc_type, exc, tb) -> None:
        latency_ms = int((time.monotonic() - self._t0) * 1000)
        if exc_type is not None:
            self._metadata["error"] = f"{exc_type.__name__}: {exc}"
        self._tracer.log_call(
            self._prompt, self._output, latency_ms=latency_ms,
            cost_usd=self._cost, language_hint=self._lang, metadata=self._metadata,
        )
        # Don't suppress exceptions
        return None
