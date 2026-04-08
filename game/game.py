"""Main game runtime for Ultimate Collect HD."""

from __future__ import annotations

import random
import sys
import time
from dataclasses import dataclass

import pygame

from . import config
from .entities import Actor, Enemy, Pickup, Timers, WeaponInventory, WeaponSlot
from .logic import clamp, collided, level_from_score, should_spawn_mega
from .storage import HighScoreWriter, load_high_score
from .terrain_worker import DecorationData, TerrainWorker


@dataclass
class SpawnTarget:
    pos: pygame.Vector2
    radius: float


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Ultimate Collect HD")

        self.screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        self.font_h1 = pygame.font.SysFont("Segoe UI", 32, bold=True)
        self.font_h2 = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.font_h3 = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self.font_sm = pygame.font.SysFont("Consolas", 16)

        self.running = True
        self.paused = False
        self.game_over = False

        self.score = 0
        self.lives = config.MAX_LIVES
        self.level = 1
        self.high_score = load_high_score(config.HIGH_SCORE_PATH)

        self.status_text = "Collect food. Avoid enemies and hazards."
        self.event_text = ""
        self.event_expires_at: float | None = None

        self.kill_streak = 0
        self.last_kill_at: float | None = None

        self.player = Actor(self._world_center() + pygame.Vector2(-280, 180), config.PLAYER_RADIUS)
        self.enemy = Enemy(self._world_center() + pygame.Vector2(260, -180), config.ENEMY_RADIUS, config.ENEMY_BASE_SPEED, "devil")
        self.gorilla = Enemy(self._world_center() + pygame.Vector2(300, 160), config.GORILLA_RADIUS, config.ENEMY_BASE_SPEED + config.GORILLA_BONUS_SPEED, "gorilla")

        self.food = Pickup(self._world_center(), config.FOOD_RADIUS, active=True)
        self.mega_food = Pickup(self._world_center(), config.MEGA_FOOD_RADIUS, active=False)
        self.life_bonus = Pickup(self._world_center(), config.PICKUP_RADIUS, active=False)

        self.hazards: dict[str, Pickup] = {
            "fire": Pickup(self._world_center(), config.HAZARD_RADIUS, active=True),
            "pothole": Pickup(self._world_center(), config.HAZARD_RADIUS, active=True),
            "trap": Pickup(self._world_center(), config.HAZARD_RADIUS, active=True),
        }

        self.weapon_drops: dict[WeaponSlot, Pickup] = {
            WeaponSlot.ARROW: Pickup(self._world_center(), config.PICKUP_RADIUS, active=False),
            WeaponSlot.GUN: Pickup(self._world_center(), config.PICKUP_RADIUS, active=False),
            WeaponSlot.CAPTURE: Pickup(self._world_center(), config.PICKUP_RADIUS, active=False),
        }

        self.inventory = WeaponInventory()
        self.timers = Timers()
        self.fire_requested = False

        self.input_state = {
            "up": False,
            "down": False,
            "left": False,
            "right": False,
        }

        self.background_surface: pygame.Surface | None = None
        self.background_level = -1
        self.current_decor = DecorationData(level=1, stars=[], lines=[], orbs=[])

        self.terrain_worker = TerrainWorker(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        self.terrain_worker.request(1)
        self.terrain_worker.request(2)

        self.score_writer = HighScoreWriter(config.HIGH_SCORE_PATH)

        self._reset_world()

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(config.TARGET_FPS) / 1000.0
            self._handle_events()
            if not self.paused and not self.game_over:
                self._update(dt)
            self._render()

        self.score_writer.close()
        self.terrain_worker.close()
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.input_state["up"] = True
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.input_state["down"] = True
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    self.input_state["left"] = True
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.input_state["right"] = True
                elif event.key == pygame.K_p and not self.game_over:
                    self.paused = not self.paused
                    self.status_text = "Paused" if self.paused else "Resumed"
                elif event.key in (pygame.K_r, pygame.K_SPACE):
                    self.restart()
                elif event.key == pygame.K_z:
                    self._pickup_weapon()
                elif event.key == pygame.K_1:
                    self._select_weapon(WeaponSlot.ARROW)
                elif event.key == pygame.K_2:
                    self._select_weapon(WeaponSlot.GUN)
                elif event.key == pygame.K_3:
                    self._select_weapon(WeaponSlot.CAPTURE)
                elif event.key == pygame.K_x:
                    self.fire_requested = True

            if event.type == pygame.KEYUP:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.input_state["up"] = False
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.input_state["down"] = False
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    self.input_state["left"] = False
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.input_state["right"] = False

    def _update(self, dt: float) -> None:
        self._consume_terrain_results()
        self._move_player(dt)

        now = time.time()
        self._tick_event_banner(now)
        self._tick_life_bonus(now)
        self._tick_mega_food(now)
        self._tick_weapon_respawns(now)

        if self._collect_food_if_hit():
            self._after_score_changed()
        if self._collect_mega_if_hit():
            self._after_score_changed()

        self._move_enemies(dt)

        if self.life_bonus.active and self._is_touching(self.player, self.life_bonus):
            self.life_bonus.active = False
            if self.lives < config.MAX_LIVES:
                self.lives += 1
                self.status_text = "Life regained"

        if self.fire_requested:
            self.fire_requested = False
            self._fire_weapon()

        if self._check_enemy_hit():
            self._lose_life("enemy")
            return

        if self._check_hazard_hit():
            self._lose_life("hazard")
            return

    def _render(self) -> None:
        if self.background_surface is None or self.background_level != self.level:
            self._rebuild_background()

        self.screen.blit(self.background_surface, (0, 0))

        self._draw_food()
        self._draw_hazards()
        self._draw_weapon_drops()
        self._draw_actor(self.player.pos, config.PLAYER_RADIUS, (90, 185, 255), outline=(17, 42, 71))
        self._draw_enemy(self.enemy)
        if self.level >= 5:
            self._draw_enemy(self.gorilla)

        self._draw_hud()
        if self.paused and not self.game_over:
            self._draw_center_text("PAUSED", self.font_h1, config.WARNING_COLOR, y=-10)
        if self.game_over:
            self._draw_center_text("GAME OVER", self.font_h1, config.DANGER_COLOR, y=-24)
            self._draw_center_text("Press R or SPACE to restart", self.font_h3, config.TEXT_COLOR, y=18)

        pygame.display.flip()

    def restart(self) -> None:
        self.score = 0
        self.lives = config.MAX_LIVES
        self.level = 1
        self.paused = False
        self.game_over = False
        self.status_text = "Restarted"
        self.event_text = ""
        self.event_expires_at = None
        self.kill_streak = 0
        self.last_kill_at = None
        self.inventory.reset()
        self.timers = Timers()
        self.mega_food.active = False
        self.life_bonus.active = False
        for drop in self.weapon_drops.values():
            drop.active = False
        self._reset_world()
        self._rebuild_background()
        self.terrain_worker.request(1)
        self.terrain_worker.request(2)

    def _reset_world(self) -> None:
        blockers: list[SpawnTarget] = []
        self.player.pos.update(self._random_position(blockers, config.PLAYER_RADIUS))
        blockers.append(SpawnTarget(self.player.pos, self.player.radius))

        self.enemy.pos.update(self._random_position(blockers, self.enemy.radius))
        blockers.append(SpawnTarget(self.enemy.pos, self.enemy.radius))

        self.gorilla.pos.update(self._random_position(blockers, self.gorilla.radius))
        blockers.append(SpawnTarget(self.gorilla.pos, self.gorilla.radius))

        self.food.pos.update(self._random_position(blockers, self.food.radius))
        blockers.append(SpawnTarget(self.food.pos, self.food.radius))

        for hazard in self.hazards.values():
            hazard.pos.update(self._random_position(blockers, hazard.radius))
            blockers.append(SpawnTarget(hazard.pos, hazard.radius))

    def _world_center(self) -> pygame.Vector2:
        return pygame.Vector2(config.WINDOW_WIDTH * 0.5, config.WINDOW_HEIGHT * 0.5)

    def _bounds(self) -> tuple[float, float, float, float]:
        min_x = config.WORLD_PADDING
        max_x = config.WINDOW_WIDTH - config.WORLD_PADDING
        min_y = config.WORLD_PADDING
        max_y = config.WINDOW_HEIGHT - config.WORLD_PADDING
        return min_x, max_x, min_y, max_y

    def _random_position(self, blockers: list[SpawnTarget], radius: float) -> tuple[float, float]:
        min_x, max_x, min_y, max_y = self._bounds()
        candidate = (min_x + radius, min_y + radius)
        for _ in range(180):
            x = random.uniform(min_x + radius, max_x - radius)
            y = random.uniform(min_y + radius, max_y - radius)
            candidate = (x, y)
            if all(
                not collided(x, y, radius, blocker.pos.x, blocker.pos.y, blocker.radius, margin=config.SPAWN_MIN_DISTANCE)
                for blocker in blockers
            ):
                return candidate
        return candidate

    def _all_spawn_targets(self) -> list[SpawnTarget]:
        targets = [
            SpawnTarget(self.player.pos, self.player.radius),
            SpawnTarget(self.enemy.pos, self.enemy.radius),
            SpawnTarget(self.food.pos, self.food.radius),
            SpawnTarget(self.gorilla.pos, self.gorilla.radius),
        ]
        targets.extend(SpawnTarget(h.pos, h.radius) for h in self.hazards.values() if h.active)
        if self.life_bonus.active:
            targets.append(SpawnTarget(self.life_bonus.pos, self.life_bonus.radius))
        if self.mega_food.active:
            targets.append(SpawnTarget(self.mega_food.pos, self.mega_food.radius))
        for drop in self.weapon_drops.values():
            if drop.active:
                targets.append(SpawnTarget(drop.pos, drop.radius))
        return targets

    def _move_player(self, dt: float) -> None:
        direction = pygame.Vector2(0, 0)
        if self.input_state["up"]:
            direction.y -= 1
        if self.input_state["down"]:
            direction.y += 1
        if self.input_state["left"]:
            direction.x -= 1
        if self.input_state["right"]:
            direction.x += 1

        if direction.length_squared() > 0:
            direction = direction.normalize()

        self.player.pos += direction * config.PLAYER_SPEED * dt

        min_x, max_x, min_y, max_y = self._bounds()
        self.player.pos.x = clamp(self.player.pos.x, min_x, max_x)
        self.player.pos.y = clamp(self.player.pos.y, min_y, max_y)

    def _move_enemies(self, dt: float) -> None:
        self._move_enemy_towards(self.enemy, dt)
        if self.level >= 5:
            self._move_enemy_towards(self.gorilla, dt)

    def _move_enemy_towards(self, enemy: Enemy, dt: float) -> None:
        direction = self.player.pos - enemy.pos
        if direction.length_squared() > 0.01:
            direction = direction.normalize()
            enemy.pos += direction * enemy.speed * dt

    def _collect_food_if_hit(self) -> bool:
        if not self._is_touching(self.player, self.food):
            return False

        self.score += 1
        blockers = self._all_spawn_targets()
        self.food.pos.update(self._random_position(blockers, self.food.radius))
        self._relocate_hazards()

        if should_spawn_mega(self.score, config.MEGA_FOOD_SCORE_STEP):
            blockers = self._all_spawn_targets()
            self.mega_food.pos.update(self._random_position(blockers, self.mega_food.radius))
            self.mega_food.active = True
            self.timers.mega_expires_at = time.time() + config.MEGA_FOOD_DURATION
            self.status_text = f"Mega food active for {int(config.MEGA_FOOD_DURATION)}s"
        else:
            self.status_text = "Food collected. Hazards relocated."
        return True

    def _collect_mega_if_hit(self) -> bool:
        if not self.mega_food.active:
            return False
        if not self._is_touching(self.player, self.mega_food):
            return False

        self.mega_food.active = False
        self.timers.mega_expires_at = None
        self.score += 3
        self.status_text = "Mega food bonus +3"
        return True

    def _after_score_changed(self) -> None:
        if self.score > self.high_score:
            self.high_score = self.score
            self.score_writer.enqueue(self.high_score)

        new_level = level_from_score(self.score, config.LEVEL_UP_SCORE)
        if new_level != self.level:
            self.level = new_level
            self.status_text = f"Level {self.level}: {self._theme_name()}"
            self.terrain_worker.request(self.level)
            self.terrain_worker.request(self.level + 1)
            self.background_level = -1

    def _tick_event_banner(self, now: float) -> None:
        if self.event_expires_at is not None and now >= self.event_expires_at:
            self.event_text = ""
            self.event_expires_at = None

    def _tick_life_bonus(self, now: float) -> None:
        if self.timers.next_life_spawn_at is not None and now >= self.timers.next_life_spawn_at:
            self.timers.next_life_spawn_at = None
            blockers = self._all_spawn_targets()
            self.life_bonus.pos.update(self._random_position(blockers, self.life_bonus.radius))
            self.life_bonus.active = True
            self.timers.life_expires_at = now + config.LIFE_PICKUP_DURATION

        if self.life_bonus.active and self.timers.life_expires_at is not None and now >= self.timers.life_expires_at:
            self.life_bonus.active = False
            self.timers.life_expires_at = None

    def _tick_mega_food(self, now: float) -> None:
        if self.mega_food.active and self.timers.mega_expires_at is not None and now >= self.timers.mega_expires_at:
            self.mega_food.active = False
            self.timers.mega_expires_at = None

    def _tick_weapon_respawns(self, now: float) -> None:
        if self.level < config.WEAPON_UNLOCK_LEVEL:
            return

        if self.inventory.loaded_count() >= config.WEAPON_MAX_COUNT:
            return

        missing = [slot for slot in WeaponSlot if not self.inventory.slots[slot.value] and not self.weapon_drops[slot].active]
        if not missing:
            return

        if self.timers.weapon_respawn_at is None:
            self.timers.weapon_respawn_at = now + config.DROP_RESPAWN_SECONDS
            return

        if now < self.timers.weapon_respawn_at:
            return

        slot = missing[0]
        blockers = self._all_spawn_targets()
        drop = self.weapon_drops[slot]
        drop.pos.update(self._random_position(blockers, drop.radius))
        drop.active = True
        self.timers.weapon_respawn_at = None

    def _pickup_weapon(self) -> None:
        if self.level < config.WEAPON_UNLOCK_LEVEL or self.game_over:
            return

        picked = False
        for slot, drop in self.weapon_drops.items():
            if drop.active and self._is_touching(self.player, drop, margin=8):
                drop.active = False
                self.inventory.slots[slot.value] = True
                if slot is WeaponSlot.GUN:
                    self.inventory.gun_bullets = config.GUN_BULLETS_PER_PICKUP
                if slot is WeaponSlot.CAPTURE:
                    self.inventory.capture_charges = config.CAPTURE_CHARGES_PER_PICKUP
                self.status_text = f"Picked {self._weapon_label(slot)}"
                picked = True

        if picked:
            self.timers.weapon_respawn_at = None

    def _select_weapon(self, slot: WeaponSlot) -> None:
        self.inventory.selected = slot
        if self.inventory.slots[slot.value]:
            self.status_text = f"Selected {self._weapon_label(slot)} READY"
        else:
            self.status_text = f"Selected {self._weapon_label(slot)} EMPTY"

    def _fire_weapon(self) -> None:
        if self.level < config.WEAPON_UNLOCK_LEVEL:
            self.status_text = "Weapons unlock at level 3"
            return

        target = self._nearest_enemy_in_range(max_distance=300.0)
        if target is None:
            self.status_text = "No enemy in range"
            return

        selected = self.inventory.selected

        if selected is WeaponSlot.ARROW and self.inventory.slots[WeaponSlot.ARROW.value]:
            self.inventory.slots[WeaponSlot.ARROW.value] = False
            self._apply_weapon_kill(target, "Arrow hit")
            return

        if selected is WeaponSlot.GUN and self.inventory.slots[WeaponSlot.GUN.value]:
            if self.inventory.gun_bullets <= 0:
                self.inventory.slots[WeaponSlot.GUN.value] = False
                self.status_text = "Out of bullets"
                return
            self.inventory.gun_bullets -= 1
            if self.inventory.gun_bullets <= 0:
                self.inventory.slots[WeaponSlot.GUN.value] = False
            self._apply_weapon_kill(target, f"Gun hit ({self.inventory.gun_bullets} bullets left)")
            return

        if selected is WeaponSlot.CAPTURE and self.inventory.slots[WeaponSlot.CAPTURE.value]:
            if target is not self.enemy:
                self.status_text = "Capture gun works only on devil"
                return
            if self.inventory.capture_charges <= 0:
                self.inventory.slots[WeaponSlot.CAPTURE.value] = False
                self.status_text = "No capture charges"
                return
            self.inventory.capture_charges -= 1
            if self.inventory.capture_charges <= 0:
                self.inventory.slots[WeaponSlot.CAPTURE.value] = False
            self._apply_weapon_kill(target, "Devil captured")
            return

        self.status_text = "Selected weapon slot is empty"

    def _apply_weapon_kill(self, target: Enemy, action_text: str) -> None:
        self.score += config.WEAPON_SCORE_BONUS

        blockers = self._all_spawn_targets()
        target.pos.update(self._random_position(blockers, target.radius))

        now = time.time()
        if self.last_kill_at is not None and (now - self.last_kill_at) <= config.KILL_STREAK_WINDOW:
            self.kill_streak += 1
        else:
            self.kill_streak = 1
        self.last_kill_at = now

        streak_note = ""
        if self.kill_streak >= 2:
            streak_note = " | EPIC STREAK"
            self.kill_streak = 0
            self.last_kill_at = None

        if target.kind == "gorilla":
            streak_note += " | GORILLA ELIMINATED"

        self.status_text = f"{action_text} +{config.WEAPON_SCORE_BONUS}{streak_note}"
        if streak_note:
            self.event_text = streak_note.replace(" | ", " ").strip()
            self.event_expires_at = now + 1.5

        self._after_score_changed()
        self.timers.weapon_respawn_at = time.time() + config.DROP_RESPAWN_SECONDS

    def _nearest_enemy_in_range(self, max_distance: float) -> Enemy | None:
        enemies: list[Enemy] = [self.enemy]
        if self.level >= 5:
            enemies.append(self.gorilla)

        nearest: Enemy | None = None
        nearest_distance_sq = max_distance * max_distance
        for enemy in enemies:
            dx = enemy.pos.x - self.player.pos.x
            dy = enemy.pos.y - self.player.pos.y
            d2 = dx * dx + dy * dy
            if d2 <= nearest_distance_sq:
                nearest = enemy
                nearest_distance_sq = d2
        return nearest

    def _check_enemy_hit(self) -> bool:
        if self._is_touching(self.player, self.enemy):
            return True
        if self.level >= 5 and self._is_touching(self.player, self.gorilla):
            return True
        return False

    def _check_hazard_hit(self) -> bool:
        return any(h.active and self._is_touching(self.player, h) for h in self.hazards.values())

    def _lose_life(self, reason: str) -> None:
        self.lives -= 1
        self.life_bonus.active = False
        self.mega_food.active = False
        for drop in self.weapon_drops.values():
            drop.active = False
        self.inventory.reset()

        self.kill_streak = 0
        self.last_kill_at = None

        if self.lives <= 0:
            self.game_over = True
            self.status_text = f"Defeated by {reason}. Restart with R or SPACE"
            return

        self.timers.next_life_spawn_at = time.time() + config.LIFE_RESPAWN_DELAY
        self.timers.life_expires_at = None
        self.timers.mega_expires_at = None
        self.timers.weapon_respawn_at = time.time() + config.DROP_RESPAWN_SECONDS

        self._reset_world()
        self.status_text = "Life lost. Bonus heart in 10s."

    def _relocate_hazards(self) -> None:
        for hazard in self.hazards.values():
            blockers = self._all_spawn_targets()
            hazard.pos.update(self._random_position(blockers, hazard.radius))

    def _is_touching(self, a: Actor | Pickup, b: Actor | Pickup, margin: float = 0.0) -> bool:
        return collided(a.pos.x, a.pos.y, a.radius, b.pos.x, b.pos.y, b.radius, margin=margin)

    def _consume_terrain_results(self) -> None:
        while True:
            data = self.terrain_worker.poll()
            if data is None:
                break
            if data.level == self.level:
                self.current_decor = data
                self.background_level = -1

    def _theme(self):
        return config.THEMES[(self.level - 1) % len(config.THEMES)]

    def _theme_name(self) -> str:
        return self._theme().name

    def _rebuild_background(self) -> None:
        theme = self._theme()
        surface = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))

        for y in range(config.WINDOW_HEIGHT):
            blend = y / max(1, config.WINDOW_HEIGHT - 1)
            r = int(config.BG_TOP[0] + (config.BG_BOTTOM[0] - config.BG_TOP[0]) * blend)
            g = int(config.BG_TOP[1] + (config.BG_BOTTOM[1] - config.BG_TOP[1]) * blend)
            b = int(config.BG_TOP[2] + (config.BG_BOTTOM[2] - config.BG_TOP[2]) * blend)
            pygame.draw.line(surface, (r, g, b), (0, y), (config.WINDOW_WIDTH, y))

        grid_step = 70 if self.level == 1 else 60
        for x in range(0, config.WINDOW_WIDTH + 1, grid_step):
            pygame.draw.line(surface, config.GRID_COLOR, (x, 0), (x, config.WINDOW_HEIGHT), 1)
        for y in range(0, config.WINDOW_HEIGHT + 1, grid_step):
            pygame.draw.line(surface, config.GRID_COLOR, (0, y), (config.WINDOW_WIDTH, y), 1)

        if self.current_decor.level == self.level:
            for x, y, radius in self.current_decor.stars:
                pygame.draw.circle(surface, (230, 241, 255), (x, y), radius)
            for start, end in self.current_decor.lines:
                pygame.draw.line(surface, theme.accent, start, end, 2)
            for x, y, radius in self.current_decor.orbs:
                pygame.draw.circle(surface, theme.base, (x, y), radius, width=2)

        pygame.draw.rect(surface, theme.accent, pygame.Rect(8, 8, config.WINDOW_WIDTH - 16, config.WINDOW_HEIGHT - 16), 4)

        self.background_surface = surface
        self.background_level = self.level

    def _draw_food(self) -> None:
        pygame.draw.circle(self.screen, (255, 208, 97), self.food.pos, config.FOOD_RADIUS)
        pygame.draw.circle(self.screen, (121, 85, 33), self.food.pos, config.FOOD_RADIUS, width=2)

        if self.mega_food.active:
            pygame.draw.circle(self.screen, (255, 244, 148), self.mega_food.pos, config.MEGA_FOOD_RADIUS)
            pygame.draw.circle(self.screen, (245, 172, 21), self.mega_food.pos, config.MEGA_FOOD_RADIUS, width=3)

        if self.life_bonus.active:
            pygame.draw.circle(self.screen, (255, 97, 133), self.life_bonus.pos, config.PICKUP_RADIUS)
            pygame.draw.circle(self.screen, (255, 229, 236), self.life_bonus.pos, config.PICKUP_RADIUS - 5)

    def _draw_hazards(self) -> None:
        fire = self.hazards["fire"]
        pothole = self.hazards["pothole"]
        trap = self.hazards["trap"]

        pygame.draw.circle(self.screen, (255, 118, 73), fire.pos, fire.radius)
        pygame.draw.circle(self.screen, (131, 20, 18), fire.pos, fire.radius, width=2)

        pygame.draw.circle(self.screen, (30, 32, 38), pothole.pos, pothole.radius)
        pygame.draw.circle(self.screen, (70, 72, 78), pothole.pos, pothole.radius, width=2)

        p = trap.pos
        points = [(p.x, p.y - trap.radius), (p.x - trap.radius, p.y + trap.radius), (p.x + trap.radius, p.y + trap.radius)]
        pygame.draw.polygon(self.screen, (209, 104, 255), points)
        pygame.draw.polygon(self.screen, (93, 23, 126), points, width=2)

    def _draw_weapon_drops(self) -> None:
        for slot, drop in self.weapon_drops.items():
            if not drop.active:
                continue
            color = (215, 222, 230)
            pygame.draw.circle(self.screen, color, drop.pos, drop.radius)
            pygame.draw.circle(self.screen, (90, 100, 113), drop.pos, drop.radius, width=2)
            label = self._weapon_short(slot)
            text = self.font_sm.render(label, True, (42, 54, 68))
            rect = text.get_rect(center=(drop.pos.x, drop.pos.y))
            self.screen.blit(text, rect)

    def _draw_actor(self, pos: pygame.Vector2, radius: int, color: tuple[int, int, int], outline: tuple[int, int, int]) -> None:
        pygame.draw.circle(self.screen, color, pos, radius)
        pygame.draw.circle(self.screen, outline, pos, radius, width=2)

    def _draw_enemy(self, enemy: Enemy) -> None:
        color = (255, 102, 102) if enemy.kind == "devil" else (126, 85, 66)
        outline = (108, 23, 23) if enemy.kind == "devil" else (58, 35, 23)

        p = enemy.pos
        r = enemy.radius
        points = [(p.x, p.y - r), (p.x - r, p.y + r), (p.x + r, p.y + r)]
        pygame.draw.polygon(self.screen, color, points)
        pygame.draw.polygon(self.screen, outline, points, width=2)

    def _draw_hud(self) -> None:
        hud = pygame.Rect(18, 18, config.WINDOW_WIDTH - 36, 82)
        pygame.draw.rect(self.screen, (17, 41, 63), hud, border_radius=10)
        pygame.draw.rect(self.screen, (75, 121, 158), hud, width=2, border_radius=10)

        score_text = self.font_h2.render(f"Score: {self.score:03d}", True, config.TEXT_COLOR)
        level_text = self.font_h2.render(f"Level: {self.level}", True, config.TEXT_COLOR)
        high_text = self.font_h3.render(f"High: {self.high_score:03d}", True, config.WARNING_COLOR)
        lives_text = self.font_h3.render(f"Lives: {self.lives}", True, config.TEXT_COLOR)
        fps_text = self.font_sm.render(f"FPS {self.clock.get_fps():5.1f}", True, (187, 214, 242))

        weapon_text = self.font_sm.render(self._weapon_display_text(), True, config.TEXT_COLOR)
        status_text = self.font_sm.render(self.status_text[:110], True, (202, 229, 252))

        self.screen.blit(score_text, (34, 30))
        self.screen.blit(level_text, (260, 30))
        self.screen.blit(high_text, (430, 34))
        self.screen.blit(lives_text, (560, 36))
        self.screen.blit(weapon_text, (34, 64))
        self.screen.blit(status_text, (350, 66))
        self.screen.blit(fps_text, (config.WINDOW_WIDTH - 110, 70))

        if self.event_text:
            self._draw_center_text(self.event_text, self.font_h2, config.WARNING_COLOR, y=116)

    def _draw_center_text(self, text: str, font: pygame.font.Font, color: tuple[int, int, int], y: int = 0) -> None:
        label = font.render(text, True, color)
        rect = label.get_rect(center=(config.WINDOW_WIDTH * 0.5, config.WINDOW_HEIGHT * 0.5 + y))
        self.screen.blit(label, rect)

    def _weapon_label(self, slot: WeaponSlot) -> str:
        if slot is WeaponSlot.ARROW:
            return "Arrow"
        if slot is WeaponSlot.GUN:
            return f"Gun ({self.inventory.gun_bullets})"
        return f"Capture ({self.inventory.capture_charges})"

    def _weapon_short(self, slot: WeaponSlot) -> str:
        if slot is WeaponSlot.ARROW:
            return "A"
        if slot is WeaponSlot.GUN:
            return "G"
        return "C"

    def _weapon_display_text(self) -> str:
        if self.level < config.WEAPON_UNLOCK_LEVEL:
            return "Weapons: locked until level 3"

        selected = self.inventory.selected
        selected_name = self._weapon_label(selected)
        return (
            f"Weapons {self.inventory.loaded_count()}/{config.WEAPON_MAX_COUNT}"
            f" | Selected: {selected_name}"
            " | Keys: Z pick, 1/2/3 select, X fire"
        )


def main() -> int:
    game = Game()
    game.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
