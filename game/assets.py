"""Asset path and sprite-sheet loading utilities."""

from __future__ import annotations

from pathlib import Path

import pygame


ASSET_ROOT = Path(__file__).resolve().parent.parent / "assets"


class SpriteSheet:
    """Simple horizontal sprite-sheet extractor."""

    def __init__(self, image_path: Path) -> None:
        self.path = image_path
        self.image = pygame.image.load(image_path.as_posix()).convert_alpha()

    def frames(self, frame_size: tuple[int, int], count: int) -> list[pygame.Surface]:
        frame_w, frame_h = frame_size
        results: list[pygame.Surface] = []
        for i in range(count):
            area = pygame.Rect(i * frame_w, 0, frame_w, frame_h)
            frame = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
            frame.blit(self.image, (0, 0), area)
            results.append(frame)
        return results


def try_load_image(path: Path) -> pygame.Surface | None:
    if not path.exists():
        return None
    try:
        return pygame.image.load(path.as_posix()).convert_alpha()
    except pygame.error:
        return None


def try_load_sheet(path: Path, frame_size: tuple[int, int], count: int) -> list[pygame.Surface] | None:
    if not path.exists():
        return None
    try:
        return SpriteSheet(path).frames(frame_size=frame_size, count=count)
    except pygame.error:
        return None
