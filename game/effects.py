"""Combat and feedback visual effects (particles, slashes, flashes)."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random

import pygame


Color = tuple[int, int, int]


@dataclass
class Particle:
    pos: pygame.Vector2
    vel: pygame.Vector2
    life: float
    max_life: float
    radius: float
    color: Color


@dataclass
class RingEffect:
    pos: pygame.Vector2
    life: float
    max_life: float
    start_radius: float
    end_radius: float
    color: Color


@dataclass
class SlashEffect:
    pos: pygame.Vector2
    direction: pygame.Vector2
    life: float
    max_life: float


class EffectSystem:
    def __init__(self) -> None:
        self.particles: list[Particle] = []
        self.rings: list[RingEffect] = []
        self.slashes: list[SlashEffect] = []

    def update(self, dt: float) -> None:
        for particle in self.particles:
            particle.life -= dt
            particle.pos += particle.vel * dt
            particle.vel *= 0.96

        for ring in self.rings:
            ring.life -= dt

        for slash in self.slashes:
            slash.life -= dt

        self.particles = [p for p in self.particles if p.life > 0]
        self.rings = [r for r in self.rings if r.life > 0]
        self.slashes = [s for s in self.slashes if s.life > 0]

    def draw(self, screen: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        for ring in self.rings:
            t = 1.0 - (ring.life / ring.max_life)
            radius = int(ring.start_radius + (ring.end_radius - ring.start_radius) * t)
            alpha = int(180 * (ring.life / ring.max_life))
            if radius <= 0 or alpha <= 0:
                continue

            ring_surface = pygame.Surface((radius * 2 + 6, radius * 2 + 6), pygame.SRCALPHA)
            pygame.draw.circle(ring_surface, (*ring.color, alpha), (radius + 3, radius + 3), radius, width=3)
            x = int(ring.pos.x + camera_offset.x - radius - 3)
            y = int(ring.pos.y + camera_offset.y - radius - 3)
            screen.blit(ring_surface, (x, y))

        for slash in self.slashes:
            alpha = int(220 * (slash.life / slash.max_life))
            slash_surface = pygame.Surface((96, 96), pygame.SRCALPHA)
            center = pygame.Vector2(48, 48)
            direction = slash.direction.normalize() if slash.direction.length_squared() > 0 else pygame.Vector2(1, 0)
            normal = pygame.Vector2(-direction.y, direction.x)

            p1 = center - direction * 28 + normal * 7
            p2 = center + direction * 28 + normal * 7
            p3 = center + direction * 28 - normal * 7
            p4 = center - direction * 28 - normal * 7
            points = [(p1.x, p1.y), (p2.x, p2.y), (p3.x, p3.y), (p4.x, p4.y)]
            pygame.draw.polygon(slash_surface, (255, 245, 194, alpha), points)
            pygame.draw.polygon(slash_surface, (255, 140, 92, alpha), points, width=2)

            x = int(slash.pos.x + camera_offset.x - 48)
            y = int(slash.pos.y + camera_offset.y - 48)
            screen.blit(slash_surface, (x, y))

        for particle in self.particles:
            life_ratio = particle.life / particle.max_life
            radius = max(1, int(particle.radius * life_ratio))
            alpha = int(255 * life_ratio)
            dot_surface = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(dot_surface, (*particle.color, alpha), (radius + 1, radius + 1), radius)
            x = int(particle.pos.x + camera_offset.x - radius - 1)
            y = int(particle.pos.y + camera_offset.y - radius - 1)
            screen.blit(dot_surface, (x, y))

    def spawn_muzzle_flash(self, position: pygame.Vector2, direction: pygame.Vector2) -> None:
        direction = direction.normalize() if direction.length_squared() > 0 else pygame.Vector2(1, 0)
        self.rings.append(
            RingEffect(
                pos=position.copy(),
                life=0.13,
                max_life=0.13,
                start_radius=4,
                end_radius=20,
                color=(255, 210, 94),
            )
        )

        for _ in range(8):
            spread = direction.rotate(random.uniform(-22, 22))
            speed = random.uniform(180, 360)
            self.particles.append(
                Particle(
                    pos=position.copy(),
                    vel=spread * speed,
                    life=0.22,
                    max_life=0.22,
                    radius=random.uniform(2.0, 4.5),
                    color=(255, 205, 84),
                )
            )

    def spawn_hit(self, position: pygame.Vector2, direction: pygame.Vector2) -> None:
        self.slashes.append(
            SlashEffect(
                pos=position.copy(),
                direction=direction.copy(),
                life=0.14,
                max_life=0.14,
            )
        )
        self.rings.append(
            RingEffect(
                pos=position.copy(),
                life=0.22,
                max_life=0.22,
                start_radius=8,
                end_radius=38,
                color=(255, 120, 92),
            )
        )

        for _ in range(16):
            angle = random.uniform(0.0, math.tau)
            speed = random.uniform(110, 280)
            self.particles.append(
                Particle(
                    pos=position.copy(),
                    vel=pygame.Vector2(math.cos(angle), math.sin(angle)) * speed,
                    life=0.35,
                    max_life=0.35,
                    radius=random.uniform(2.5, 4.5),
                    color=(255, 108, 86),
                )
            )

    def spawn_damage(self, position: pygame.Vector2) -> None:
        self.rings.append(
            RingEffect(
                pos=position.copy(),
                life=0.32,
                max_life=0.32,
                start_radius=10,
                end_radius=60,
                color=(255, 70, 70),
            )
        )

        for _ in range(24):
            angle = random.uniform(0.0, math.tau)
            speed = random.uniform(80, 240)
            self.particles.append(
                Particle(
                    pos=position.copy(),
                    vel=pygame.Vector2(math.cos(angle), math.sin(angle)) * speed,
                    life=0.45,
                    max_life=0.45,
                    radius=random.uniform(2.0, 5.0),
                    color=(255, 82, 92),
                )
            )
