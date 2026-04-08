"""Background level-decoration precompute to keep frame times stable."""

from __future__ import annotations

from dataclasses import dataclass
import random
from queue import Empty, Queue
from threading import Event, Thread


@dataclass
class DecorationData:
    level: int
    stars: list[tuple[int, int, int]]
    lines: list[tuple[tuple[int, int], tuple[int, int]]]
    orbs: list[tuple[int, int, int]]


class TerrainWorker:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self._requests: Queue[int] = Queue()
        self._results: Queue[DecorationData] = Queue()
        self._stop_event = Event()
        self._thread = Thread(target=self._run, name="terrain-worker", daemon=True)
        self._thread.start()

    def request(self, level: int) -> None:
        self._requests.put(level)

    def poll(self) -> DecorationData | None:
        try:
            return self._results.get_nowait()
        except Empty:
            return None

    def close(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=1.0)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                level = self._requests.get(timeout=0.2)
            except Empty:
                continue
            self._results.put(self._build(level))

    def _build(self, level: int) -> DecorationData:
        rng = random.Random(level * 991)
        stars = [
            (rng.randint(0, self.width), rng.randint(0, self.height), rng.randint(1, 3))
            for _ in range(120)
        ]
        lines = [
            (
                (rng.randint(0, self.width), rng.randint(0, self.height)),
                (rng.randint(0, self.width), rng.randint(0, self.height)),
            )
            for _ in range(12)
        ]
        orbs = [
            (rng.randint(50, self.width - 50), rng.randint(80, self.height - 80), rng.randint(20, 70))
            for _ in range(8)
        ]
        return DecorationData(level=level, stars=stars, lines=lines, orbs=orbs)
