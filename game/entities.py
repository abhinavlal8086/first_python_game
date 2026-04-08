"""Data models for entities and runtime state."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import pygame


class WeaponSlot(Enum):
    ARROW = 0
    GUN = 1
    CAPTURE = 2


@dataclass
class Actor:
    pos: pygame.Vector2
    radius: float


@dataclass
class Enemy(Actor):
    speed: float
    kind: str


@dataclass
class Pickup:
    pos: pygame.Vector2
    radius: float
    active: bool = False


@dataclass
class WeaponInventory:
    slots: list[bool] = field(default_factory=lambda: [False, False, False])
    selected: WeaponSlot = WeaponSlot.ARROW
    gun_bullets: int = 0
    capture_charges: int = 0

    def loaded_count(self) -> int:
        return sum(1 for slot in self.slots if slot)

    def reset(self) -> None:
        self.slots = [False, False, False]
        self.selected = WeaponSlot.ARROW
        self.gun_bullets = 0
        self.capture_charges = 0


@dataclass
class Timers:
    next_life_spawn_at: float | None = None
    life_expires_at: float | None = None
    mega_expires_at: float | None = None
    weapon_respawn_at: float | None = None
    event_expires_at: float | None = None
