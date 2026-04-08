"""Persistence helpers for score and settings."""

from __future__ import annotations

import json
from pathlib import Path
from queue import Empty, Queue
from threading import Event, Thread


def load_high_score(path: str) -> int:
    p = Path(path)
    if not p.exists():
        return 0
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return 0
    score = data.get("high_score", 0)
    return int(score) if isinstance(score, int | float) else 0


class HighScoreWriter:
    """Background writer for non-blocking high score saves."""

    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._queue: Queue[int] = Queue()
        self._stop_event = Event()
        self._worker = Thread(target=self._run, name="high-score-writer", daemon=True)
        self._worker.start()

    def enqueue(self, score: int) -> None:
        self._queue.put(max(0, int(score)))

    def close(self) -> None:
        self._stop_event.set()
        self._worker.join(timeout=1.0)

    def _run(self) -> None:
        latest = None
        while not self._stop_event.is_set():
            try:
                latest = self._queue.get(timeout=0.2)
            except Empty:
                continue

            while True:
                try:
                    latest = self._queue.get_nowait()
                except Empty:
                    break

            if latest is not None:
                self._write(latest)

    def _write(self, score: int) -> None:
        payload = {"high_score": int(score)}
        try:
            self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError:
            return
