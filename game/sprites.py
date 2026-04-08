"""Procedural sprite library for character and hazard icon rendering."""

from __future__ import annotations

import math

import pygame

from .entities import WeaponSlot


def _surface(size: int) -> pygame.Surface:
    return pygame.Surface((size, size), pygame.SRCALPHA)


def _draw_shadow(surface: pygame.Surface, color: tuple[int, int, int, int]) -> None:
    w, h = surface.get_size()
    pygame.draw.ellipse(surface, color, pygame.Rect(w * 0.20, h * 0.75, w * 0.60, h * 0.18))


class SpriteLibrary:
    """Pre-renders all gameplay icons to keep frame rendering lightweight."""

    def __init__(self) -> None:
        self.runner_frames = [self._build_runner_sprite(phase) for phase in (-1.0, -0.2, 1.0, 0.2)]
        self.zombie_frames = [self._build_zombie_sprite(phase, brute=False) for phase in (-1.0, -0.3, 1.0, 0.3)]
        self.brute_frames = [self._build_zombie_sprite(phase, brute=True) for phase in (-1.0, -0.3, 1.0, 0.3)]

        self.fire_frames = [self._build_fire_hazard(frame) for frame in range(4)]
        self.trap_surface = self._build_spike_trap_hazard()
        self.pothole_surface = self._build_pothole_hazard()

        self.food_surface = self._build_food_pickup()
        self.heart_surface = self._build_heart_pickup()
        self.mega_frames = [self._build_mega_pickup(frame) for frame in range(6)]

        self.weapon_icons = {
            WeaponSlot.ARROW: self._build_weapon_arrow(),
            WeaponSlot.GUN: self._build_weapon_gun(),
            WeaponSlot.CAPTURE: self._build_weapon_capture(),
        }

    def player_sprite(self, anim_time: float, moving: bool, facing_left: bool) -> pygame.Surface:
        index = int(anim_time * 9.0) % len(self.runner_frames) if moving else 1
        sprite = self.runner_frames[index]
        return pygame.transform.flip(sprite, True, False) if facing_left else sprite

    def zombie_sprite(self, anim_time: float, brute: bool = False) -> pygame.Surface:
        frames = self.brute_frames if brute else self.zombie_frames
        index = int(anim_time * 7.5) % len(frames)
        return frames[index]

    def fire_sprite(self, anim_time: float) -> pygame.Surface:
        index = int(anim_time * 14.0) % len(self.fire_frames)
        return self.fire_frames[index]

    def mega_sprite(self, anim_time: float) -> pygame.Surface:
        index = int(anim_time * 12.0) % len(self.mega_frames)
        return self.mega_frames[index]

    def weapon_sprite(self, slot: WeaponSlot) -> pygame.Surface:
        return self.weapon_icons[slot]

    def _build_runner_sprite(self, phase: float) -> pygame.Surface:
        s = _surface(72)
        _draw_shadow(s, (0, 0, 0, 80))

        # Legs
        left_hip = (34, 43)
        right_hip = (40, 43)
        left_knee = (30 - 8 * phase, 52)
        right_knee = (44 + 8 * phase, 52)
        left_foot = (26 - 10 * phase, 63)
        right_foot = (48 + 10 * phase, 63)

        pygame.draw.line(s, (33, 52, 90), left_hip, left_knee, 5)
        pygame.draw.line(s, (33, 52, 90), left_knee, left_foot, 5)
        pygame.draw.line(s, (33, 52, 90), right_hip, right_knee, 5)
        pygame.draw.line(s, (33, 52, 90), right_knee, right_foot, 5)

        pygame.draw.ellipse(s, (235, 236, 240), pygame.Rect(left_foot[0] - 5, left_foot[1] - 2, 12, 6))
        pygame.draw.ellipse(s, (235, 236, 240), pygame.Rect(right_foot[0] - 5, right_foot[1] - 2, 12, 6))

        # Body
        pygame.draw.rect(s, (62, 159, 236), pygame.Rect(25, 24, 24, 22), border_radius=8)
        pygame.draw.rect(s, (29, 94, 153), pygame.Rect(25, 24, 24, 22), width=2, border_radius=8)

        # Arms
        left_shoulder = (27, 28)
        right_shoulder = (47, 28)
        left_hand = (19 + 8 * phase, 39)
        right_hand = (55 - 8 * phase, 39)
        pygame.draw.line(s, (245, 196, 166), left_shoulder, left_hand, 4)
        pygame.draw.line(s, (245, 196, 166), right_shoulder, right_hand, 4)

        # Head + face
        pygame.draw.circle(s, (246, 207, 180), (36, 17), 10)
        pygame.draw.circle(s, (31, 53, 92), (36, 17), 10, width=2)
        pygame.draw.circle(s, (44, 44, 50), (33, 15), 1)
        pygame.draw.circle(s, (44, 44, 50), (39, 15), 1)
        pygame.draw.arc(s, (44, 44, 50), pygame.Rect(32, 18, 8, 5), math.pi * 0.05, math.pi * 0.95, 1)

        # Headband accent
        pygame.draw.line(s, (255, 74, 74), (27, 13), (45, 13), 2)
        return s

    def _build_zombie_sprite(self, phase: float, brute: bool) -> pygame.Surface:
        size = 78 if brute else 72
        s = _surface(size)
        _draw_shadow(s, (0, 0, 0, 90))

        center_x = size // 2
        torso_color = (94, 68, 89) if brute else (88, 84, 132)
        skin_color = (114, 166, 104) if brute else (136, 184, 115)

        body_rect = pygame.Rect(center_x - 14, 25, 28, 25)
        if brute:
            body_rect = pygame.Rect(center_x - 16, 23, 32, 29)

        # Torso
        pygame.draw.rect(s, torso_color, body_rect, border_radius=8)
        pygame.draw.rect(s, (42, 32, 46), body_rect, width=2, border_radius=8)

        # Arms reaching forward
        arm_y = body_rect.y + 8
        arm_offset = 10 + int(4 * phase)
        pygame.draw.line(s, skin_color, (body_rect.left + 2, arm_y), (body_rect.left - arm_offset, arm_y + 6), 5)
        pygame.draw.line(s, skin_color, (body_rect.right - 2, arm_y), (body_rect.right + arm_offset, arm_y + 6), 5)

        # Legs
        left_foot = (body_rect.left + 7 - int(7 * phase), size - 10)
        right_foot = (body_rect.right - 7 + int(7 * phase), size - 10)
        pygame.draw.line(s, (58, 67, 85), (body_rect.left + 9, body_rect.bottom - 1), left_foot, 5)
        pygame.draw.line(s, (58, 67, 85), (body_rect.right - 9, body_rect.bottom - 1), right_foot, 5)

        # Head
        head_center = (center_x, 17)
        head_radius = 12 if brute else 11
        pygame.draw.circle(s, skin_color, head_center, head_radius)
        pygame.draw.circle(s, (47, 72, 46), head_center, head_radius, width=2)

        # Eyes and mouth
        pygame.draw.circle(s, (255, 44, 44), (head_center[0] - 4, head_center[1] - 1), 2)
        pygame.draw.circle(s, (255, 44, 44), (head_center[0] + 4, head_center[1] - 1), 2)
        pygame.draw.rect(s, (54, 23, 23), pygame.Rect(head_center[0] - 5, head_center[1] + 5, 10, 3), border_radius=2)

        # Scar details
        pygame.draw.line(s, (66, 40, 40), (head_center[0] - 8, head_center[1] - 8), (head_center[0] - 2, head_center[1] - 2), 2)
        if brute:
            pygame.draw.line(s, (66, 40, 40), (head_center[0] + 7, head_center[1] - 7), (head_center[0] + 1, head_center[1] - 1), 2)

        return s

    def _build_fire_hazard(self, frame: int) -> pygame.Surface:
        s = _surface(66)
        _draw_shadow(s, (0, 0, 0, 70))

        wobble = (frame % 2) * 2
        outer = [(33, 18 - wobble), (22, 36), (28, 56), (33, 50), (38, 56), (44, 36)]
        inner = [(33, 26 - wobble), (27, 38), (30, 49), (33, 44), (36, 49), (39, 38)]

        pygame.draw.polygon(s, (255, 124, 56), outer)
        pygame.draw.polygon(s, (255, 212, 92), inner)
        pygame.draw.circle(s, (255, 68, 33), (33, 52), 8, width=2)
        return s

    def _build_spike_trap_hazard(self) -> pygame.Surface:
        s = _surface(68)
        _draw_shadow(s, (0, 0, 0, 90))

        pygame.draw.rect(s, (67, 58, 73), pygame.Rect(12, 42, 44, 13), border_radius=4)
        pygame.draw.rect(s, (31, 25, 36), pygame.Rect(12, 42, 44, 13), width=2, border_radius=4)

        for i in range(5):
            x = 16 + i * 10
            points = [(x, 42), (x + 4, 26), (x + 8, 42)]
            pygame.draw.polygon(s, (206, 189, 227), points)
            pygame.draw.polygon(s, (95, 78, 118), points, width=1)

        # Warning mark
        pygame.draw.circle(s, (255, 208, 64), (34, 16), 8)
        pygame.draw.circle(s, (72, 52, 19), (34, 16), 8, width=2)
        pygame.draw.line(s, (72, 52, 19), (34, 12), (34, 17), 2)
        pygame.draw.circle(s, (72, 52, 19), (34, 20), 1)
        return s

    def _build_pothole_hazard(self) -> pygame.Surface:
        s = _surface(70)
        _draw_shadow(s, (0, 0, 0, 90))

        pygame.draw.circle(s, (49, 54, 64), (35, 38), 18)
        pygame.draw.circle(s, (18, 20, 24), (35, 38), 14)

        # Caution stripes
        pygame.draw.rect(s, (228, 192, 72), pygame.Rect(16, 17, 38, 8), border_radius=2)
        for x in range(16, 55, 8):
            pygame.draw.line(s, (81, 56, 18), (x, 17), (x + 4, 25), 2)

        # Crack lines
        pygame.draw.line(s, (93, 103, 117), (35, 38), (46, 33), 2)
        pygame.draw.line(s, (93, 103, 117), (35, 38), (27, 47), 2)
        return s

    def _build_food_pickup(self) -> pygame.Surface:
        s = _surface(56)
        _draw_shadow(s, (0, 0, 0, 60))

        # Ration pack icon
        pygame.draw.rect(s, (250, 205, 105), pygame.Rect(14, 14, 28, 28), border_radius=6)
        pygame.draw.rect(s, (113, 73, 33), pygame.Rect(14, 14, 28, 28), width=2, border_radius=6)
        pygame.draw.circle(s, (123, 82, 34), (22, 22), 2)
        pygame.draw.circle(s, (123, 82, 34), (31, 24), 2)
        pygame.draw.circle(s, (123, 82, 34), (35, 31), 2)

        # Bite detail
        pygame.draw.circle(s, (0, 0, 0, 0), (41, 17), 6)
        return s

    def _build_heart_pickup(self) -> pygame.Surface:
        s = _surface(58)
        _draw_shadow(s, (0, 0, 0, 60))

        points = [
            (29, 48),
            (12, 29),
            (12, 20),
            (20, 13),
            (29, 20),
            (38, 13),
            (46, 20),
            (46, 29),
        ]
        pygame.draw.polygon(s, (255, 89, 122), points)
        pygame.draw.polygon(s, (150, 27, 58), points, width=2)
        return s

    def _build_mega_pickup(self, frame: int) -> pygame.Surface:
        s = _surface(64)
        _draw_shadow(s, (0, 0, 0, 60))

        pulse = 18 + (frame % 3)
        pygame.draw.circle(s, (255, 232, 115, 120), (32, 32), pulse)

        star = [(32, 13), (37, 26), (51, 26), (40, 35), (45, 49), (32, 40), (19, 49), (24, 35), (13, 26), (27, 26)]
        pygame.draw.polygon(s, (255, 245, 171), star)
        pygame.draw.polygon(s, (196, 151, 40), star, width=2)
        return s

    def _build_weapon_arrow(self) -> pygame.Surface:
        s = _surface(54)
        pygame.draw.circle(s, (210, 223, 244), (27, 27), 22)
        pygame.draw.circle(s, (75, 98, 140), (27, 27), 22, width=2)

        pygame.draw.line(s, (48, 52, 62), (16, 36), (36, 16), 3)
        pygame.draw.polygon(s, (160, 166, 177), [(34, 14), (41, 14), (36, 20)])
        pygame.draw.polygon(s, (212, 86, 86), [(14, 34), (19, 39), (14, 40)])
        return s

    def _build_weapon_gun(self) -> pygame.Surface:
        s = _surface(54)
        pygame.draw.circle(s, (210, 223, 244), (27, 27), 22)
        pygame.draw.circle(s, (75, 98, 140), (27, 27), 22, width=2)

        pygame.draw.rect(s, (82, 92, 111), pygame.Rect(18, 18, 18, 8), border_radius=3)
        pygame.draw.rect(s, (49, 55, 67), pygame.Rect(33, 19, 8, 5), border_radius=2)
        pygame.draw.polygon(s, (79, 88, 102), [(24, 26), (31, 26), (30, 38), (22, 38)])
        return s

    def _build_weapon_capture(self) -> pygame.Surface:
        s = _surface(54)
        pygame.draw.circle(s, (210, 223, 244), (27, 27), 22)
        pygame.draw.circle(s, (75, 98, 140), (27, 27), 22, width=2)

        pygame.draw.circle(s, (121, 220, 237), (27, 27), 12)
        pygame.draw.circle(s, (48, 116, 128), (27, 27), 12, width=2)
        pygame.draw.circle(s, (220, 255, 255), (27, 27), 4)
        return s
