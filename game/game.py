"""Main game runtime for Ultimate Collect HD."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
import time

import pygame

from . import config
from .assets import ASSET_ROOT
from .audio import AudioSystem
from .db import GameDatabase, SaveSlot
from .entities import Actor, Enemy, Pickup, Timers, WeaponInventory, WeaponSlot
from .effects import EffectSystem
from .logic import clamp, collided, level_from_score, should_spawn_mega
from .sprites import SpriteLibrary
from .terrain_worker import DecorationData, TerrainWorker


@dataclass
class SpawnTarget:
    pos: pygame.Vector2
    radius: float


@dataclass(frozen=True)
class AchievementDef:
    key: str
    title: str
    description: str


ACHIEVEMENTS = [
    AchievementDef("first_blood", "First Blood", "Eliminate your first zombie."),
    AchievementDef("streak_3", "Chain Reaper", "Reach a 3x elimination streak."),
    AchievementDef("level_5", "Wasteland Veteran", "Reach mission level 5."),
    AchievementDef("score_100", "Scavenger Legend", "Reach 100 score in a run."),
    AchievementDef("last_stand", "Last Stand", "Survive with one life left."),
]


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
        self.in_menu = True
        self.paused = False
        self.game_over = False

        self.score = 0
        self.lives = config.MAX_LIVES
        self.level = 1
        self.mission_unlocked = 1
        self.current_streak = 0
        self.max_streak = 0
        self.total_kills = 0
        self.last_kill_at: float | None = None

        self.status_text = "Welcome to the Wasteland"
        self.event_text = ""
        self.event_expires_at: float | None = None
        self.achievement_toast = ""
        self.achievement_toast_expires_at: float | None = None

        self.anim_time = 0.0
        self.player_facing_left = False
        self.player_is_running = False

        self.player = Actor(self._world_center() + pygame.Vector2(-280, 180), config.PLAYER_RADIUS)
        self.enemy = Enemy(self._world_center() + pygame.Vector2(260, -180), config.ENEMY_RADIUS, config.ENEMY_BASE_SPEED, "zombie")
        self.warlord = Enemy(
            self._world_center() + pygame.Vector2(300, 160),
            config.GORILLA_RADIUS,
            config.ENEMY_BASE_SPEED + config.GORILLA_BONUS_SPEED,
            "warlord",
        )

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

        self.asset_root = ASSET_ROOT
        self.sprites = SpriteLibrary(asset_root=self.asset_root, use_external=True)
        self.effects = EffectSystem()
        self.audio = AudioSystem(self.asset_root)

        self.camera_offset = pygame.Vector2(0, 0)
        self.shake_time_left = 0.0
        self.shake_total_time = 0.0
        self.shake_strength = 0.0
        self.damage_flash_alpha = 0.0
        self.flash_surface = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), pygame.SRCALPHA)

        self.db = GameDatabase(config.SQLITE_DB_PATH)
        self.save_slots: list[SaveSlot] = []
        self.selected_slot_index = 0
        self.menu_selected_mission = 1
        self.active_slot_id: int | None = None
        self.active_slot_name = "-"
        self.unlocked_achievements: set[str] = set()

        self.pause_menu_index = 0

        self.terrain_worker = TerrainWorker(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        self.terrain_worker.request(1)
        self.terrain_worker.request(2)

        self._refresh_save_slots()
        self._reset_world()
        self.audio.start_music()

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(config.TARGET_FPS) / 1000.0
            self._handle_events()

            self.anim_time += dt
            self._update_feedback_effects(dt)
            self.effects.update(dt)
            self._consume_terrain_results()

            if not self.in_menu and not self.paused and not self.game_over:
                self._update_world(dt)

            self._render()

        self.terrain_worker.close()
        self.audio.shutdown()
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.KEYDOWN:
                if self.in_menu:
                    self._handle_menu_key(event.key)
                    continue

                if self.paused:
                    self._handle_pause_key(event.key)
                    continue

                self._handle_game_keydown(event.key)

            if event.type == pygame.KEYUP and not self.in_menu and not self.paused:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.input_state["up"] = False
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.input_state["down"] = False
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    self.input_state["left"] = False
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.input_state["right"] = False

    def _handle_menu_key(self, key: int) -> None:
        if key == pygame.K_n:
            self._create_new_save_and_start()
            return

        if not self.save_slots:
            self.status_text = "No saves yet. Press N to create a new run."
            return

        if key == pygame.K_UP:
            self.selected_slot_index = max(0, self.selected_slot_index - 1)
            self._sync_menu_mission_selection()
            return

        if key == pygame.K_DOWN:
            self.selected_slot_index = min(len(self.save_slots) - 1, self.selected_slot_index + 1)
            self._sync_menu_mission_selection()
            return

        selected = self._selected_slot()
        if selected is None:
            return

        if key == pygame.K_LEFT:
            self.menu_selected_mission = max(1, self.menu_selected_mission - 1)
            return

        if key == pygame.K_RIGHT:
            self.menu_selected_mission = min(selected.mission_unlocked, self.menu_selected_mission + 1)
            return

        if key == pygame.K_RETURN:
            self._start_from_slot(selected, mission=self.menu_selected_mission, continue_mode=False)
            return

        if key == pygame.K_c:
            self._start_from_slot(selected, mission=selected.level, continue_mode=True)
            return

        if key == pygame.K_DELETE:
            self.db.delete_slot(selected.id)
            self._refresh_save_slots()
            return

    def _handle_pause_key(self, key: int) -> None:
        options = self._pause_options()
        if key in (pygame.K_ESCAPE, pygame.K_p):
            self.paused = False
            self.status_text = "Resumed"
            return

        if key == pygame.K_UP:
            self.pause_menu_index = max(0, self.pause_menu_index - 1)
            return

        if key == pygame.K_DOWN:
            self.pause_menu_index = min(len(options) - 1, self.pause_menu_index + 1)
            return

        if key != pygame.K_RETURN:
            return

        choice = self.pause_menu_index
        if choice == 0:
            self.paused = False
            self.status_text = "Resumed"
        elif choice == 1:
            self._save_active_progress()
            self.status_text = "Progress saved"
        elif choice == 2:
            self._save_active_progress()
            self._go_to_menu("Returned to save hub")
        elif choice == 3:
            enabled = self.audio.toggle_music()
            self.status_text = f"Music {'ON' if enabled else 'OFF'}"
        elif choice == 4:
            enabled = self.audio.toggle_sfx()
            self.status_text = f"SFX {'ON' if enabled else 'OFF'}"

    def _handle_game_keydown(self, key: int) -> None:
        if self.game_over:
            if key in (pygame.K_r, pygame.K_SPACE):
                self._restart_current_mission()
            elif key == pygame.K_m:
                self._go_to_menu("Returned to save hub")
            return

        if key in (pygame.K_UP, pygame.K_w):
            self.input_state["up"] = True
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.input_state["down"] = True
        elif key in (pygame.K_LEFT, pygame.K_a):
            self.input_state["left"] = True
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.input_state["right"] = True
        elif key in (pygame.K_ESCAPE, pygame.K_p):
            self.paused = True
            self.pause_menu_index = 0
            self.status_text = "Paused"
        elif key == pygame.K_z:
            self._pickup_weapon()
        elif key == pygame.K_1:
            self._select_weapon(WeaponSlot.ARROW)
        elif key == pygame.K_2:
            self._select_weapon(WeaponSlot.GUN)
        elif key == pygame.K_3:
            self._select_weapon(WeaponSlot.CAPTURE)
        elif key == pygame.K_x:
            self.fire_requested = True
        elif key == pygame.K_m:
            self._go_to_menu("Returned to save hub")

    def _update_world(self, dt: float) -> None:
        self._move_player(dt)

        now = time.time()
        self._tick_event_banner(now)
        self._tick_achievement_banner(now)
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
                self.status_text = "Medical kit recovered"
                self.audio.play_sfx("pickup")
                self._save_active_progress()

        if self.fire_requested:
            self.fire_requested = False
            self._fire_weapon()

        if self._check_enemy_hit():
            self._lose_life("zombie")
            return

        if self._check_hazard_hit():
            self._lose_life("hazard")
            return

    def _render(self) -> None:
        if self.background_surface is None or self.background_level != self.level:
            self._rebuild_background()

        self.screen.fill((0, 0, 0))
        bg_x = int(self.camera_offset.x * 0.35)
        bg_y = int(self.camera_offset.y * 0.35)
        self.screen.blit(self.background_surface, (bg_x, bg_y))

        self._draw_playfield_wall()

        if not self.in_menu:
            self._draw_food()
            self._draw_hazards()
            self._draw_weapon_drops()
            self._draw_player()
            self._draw_enemy(self.enemy)
            if self.level >= 5:
                self._draw_enemy(self.warlord)
            self.effects.draw(self.screen, self.camera_offset)

        self._draw_hud()

        if self.in_menu:
            self._draw_menu_overlay()

        if self.paused and not self.in_menu and not self.game_over:
            self._draw_pause_overlay()

        if self.game_over and not self.in_menu:
            self._draw_center_text("YOU DIED", self.font_h1, config.DANGER_COLOR, y=-24)
            self._draw_center_text("Press R to retry mission or M for save hub", self.font_h3, config.TEXT_COLOR, y=18)

        if self.achievement_toast:
            self._draw_achievement_toast()

        if self.damage_flash_alpha > 0:
            self.flash_surface.fill((*config.HIT_FLASH_COLOR, int(self.damage_flash_alpha)))
            self.screen.blit(self.flash_surface, (0, 0))

        pygame.display.flip()

    def _draw_menu_overlay(self) -> None:
        panel = pygame.Rect(180, 145, config.WINDOW_WIDTH - 360, config.WINDOW_HEIGHT - 220)
        pygame.draw.rect(self.screen, (30, 16, 11), panel, border_radius=12)
        pygame.draw.rect(self.screen, (186, 115, 72), panel, width=3, border_radius=12)

        title = self.font_h1.render("SAVE HUB // APOCALYPSE ARCHIVE", True, (255, 204, 163))
        self.screen.blit(title, title.get_rect(center=(config.WINDOW_WIDTH // 2, 185)))

        subtitle = self.font_sm.render("N: New Run  ENTER: Load Mission  C: Continue  DEL: Delete Save", True, (231, 185, 146))
        self.screen.blit(subtitle, subtitle.get_rect(center=(config.WINDOW_WIDTH // 2, 218)))

        if not self.save_slots:
            msg = self.font_h2.render("No saves found. Press N to create one.", True, (248, 199, 155))
            self.screen.blit(msg, msg.get_rect(center=(config.WINDOW_WIDTH // 2, config.WINDOW_HEIGHT // 2)))
            return

        y = 258
        for index, slot in enumerate(self.save_slots[:8]):
            selected = index == self.selected_slot_index
            item_rect = pygame.Rect(220, y - 12, config.WINDOW_WIDTH - 440, 48)
            fill = (76, 40, 26) if selected else (46, 26, 17)
            border = (255, 163, 102) if selected else (120, 83, 61)
            pygame.draw.rect(self.screen, fill, item_rect, border_radius=8)
            pygame.draw.rect(self.screen, border, item_rect, width=2, border_radius=8)

            mission_pick = self.menu_selected_mission if selected else slot.level
            label = (
                f"{slot.name} | Score {slot.score:03d} | L{slot.level} | "
                f"Unlocked {slot.mission_unlocked} | Best Streak {slot.max_streak} | Mission Pick {mission_pick}"
            )
            text = self.font_sm.render(label, True, (255, 225, 198))
            self.screen.blit(text, (232, y))
            y += 54

    def _draw_pause_overlay(self) -> None:
        overlay = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 145))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(450, 220, 380, 280)
        pygame.draw.rect(self.screen, (40, 22, 14), panel, border_radius=12)
        pygame.draw.rect(self.screen, (195, 121, 78), panel, width=3, border_radius=12)

        title = self.font_h2.render("PAUSE SETTINGS", True, (255, 206, 171))
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 34)))

        y = panel.y + 78
        for idx, option in enumerate(self._pause_options()):
            color = (255, 185, 134) if idx == self.pause_menu_index else (240, 222, 205)
            text = self.font_h3.render(option, True, color)
            self.screen.blit(text, (panel.x + 32, y))
            y += 40

        hint = self.font_sm.render("UP/DOWN + ENTER, ESC/P to resume", True, (220, 193, 172))
        self.screen.blit(hint, (panel.x + 32, panel.bottom - 34))

    def _draw_achievement_toast(self) -> None:
        toast = pygame.Rect(config.WINDOW_WIDTH - 450, 118, 420, 42)
        pygame.draw.rect(self.screen, (62, 35, 19), toast, border_radius=8)
        pygame.draw.rect(self.screen, (255, 178, 90), toast, width=2, border_radius=8)
        text = self.font_sm.render(self.achievement_toast, True, (255, 233, 206))
        self.screen.blit(text, (toast.x + 12, toast.y + 12))

    def _draw_playfield_wall(self) -> None:
        play_rect = pygame.Rect(
            config.PLAYFIELD_MARGIN,
            config.PLAYFIELD_TOP,
            config.WINDOW_WIDTH - config.PLAYFIELD_MARGIN * 2,
            config.WINDOW_HEIGHT - config.PLAYFIELD_TOP - config.PLAYFIELD_MARGIN,
        )
        pygame.draw.rect(self.screen, (124, 68, 49), play_rect, width=4)

        boundary_bar = pygame.Rect(
            config.PLAYFIELD_MARGIN,
            config.PLAYFIELD_TOP - 10,
            config.WINDOW_WIDTH - config.PLAYFIELD_MARGIN * 2,
            10,
        )
        pygame.draw.rect(self.screen, (88, 48, 35), boundary_bar)
        pygame.draw.rect(self.screen, (214, 126, 78), boundary_bar, width=1)

    def _pause_options(self) -> list[str]:
        return [
            "Resume",
            "Save Progress",
            "Return To Save Hub",
            f"Music: {'ON' if self.audio.music_enabled else 'OFF'}",
            f"SFX: {'ON' if self.audio.sfx_enabled else 'OFF'}",
        ]

    def _refresh_save_slots(self) -> None:
        self.save_slots = self.db.list_slots()
        if not self.save_slots:
            self.selected_slot_index = 0
            self.menu_selected_mission = 1
            return
        self.selected_slot_index = int(clamp(self.selected_slot_index, 0, len(self.save_slots) - 1))
        self._sync_menu_mission_selection()

    def _selected_slot(self) -> SaveSlot | None:
        if not self.save_slots:
            return None
        return self.save_slots[self.selected_slot_index]

    def _sync_menu_mission_selection(self) -> None:
        selected = self._selected_slot()
        if selected is None:
            self.menu_selected_mission = 1
            return
        self.menu_selected_mission = int(clamp(self.menu_selected_mission, 1, selected.mission_unlocked))

    def _create_new_save_and_start(self) -> None:
        existing_names = {slot.name for slot in self.save_slots}
        index = len(self.save_slots) + 1
        name = f"Survivor-{index}"
        while name in existing_names:
            index += 1
            name = f"Survivor-{index}"

        slot = self.db.create_slot(name)
        self._refresh_save_slots()
        for i, row in enumerate(self.save_slots):
            if row.id == slot.id:
                self.selected_slot_index = i
                break
        self.menu_selected_mission = 1
        self._start_from_slot(slot, mission=1, continue_mode=False)

    def _start_from_slot(self, slot: SaveSlot, mission: int, continue_mode: bool) -> None:
        self.active_slot_id = slot.id
        self.active_slot_name = slot.name
        self.unlocked_achievements = self.db.load_achievement_keys(slot.id)

        if continue_mode:
            self.score = slot.score
            self.lives = max(1, slot.lives)
            self.level = max(1, slot.level)
        else:
            mission = int(clamp(mission, 1, slot.mission_unlocked))
            self.level = mission
            self.score = (mission - 1) * config.LEVEL_UP_SCORE
            self.lives = config.MAX_LIVES

        self.mission_unlocked = max(slot.mission_unlocked, self.level)
        self.current_streak = 0
        self.last_kill_at = None
        self.max_streak = max(slot.max_streak, self.current_streak)
        self.total_kills = slot.total_kills

        self.in_menu = False
        self.paused = False
        self.game_over = False

        self.event_text = ""
        self.event_expires_at = None
        self.achievement_toast = ""
        self.achievement_toast_expires_at = None

        self.inventory.reset()
        self.timers = Timers()
        self.mega_food.active = False
        self.life_bonus.active = False
        for drop in self.weapon_drops.values():
            drop.active = False

        self._reset_feedback_effects()
        self._reset_world()
        self._rebuild_background()
        self.terrain_worker.request(self.level)
        self.terrain_worker.request(self.level + 1)
        self.status_text = f"Loaded {slot.name} at mission {self.level}"
        self._save_active_progress()

    def _restart_current_mission(self) -> None:
        if self.active_slot_id is None:
            self._go_to_menu("No active save")
            return
        slot = self.db.get_slot(self.active_slot_id)
        if slot is None:
            self._go_to_menu("Save not found")
            return
        self._start_from_slot(slot, mission=self.level, continue_mode=False)

    def _go_to_menu(self, message: str) -> None:
        self._save_active_progress()
        self.in_menu = True
        self.paused = False
        self.game_over = False
        self.status_text = message
        self._refresh_save_slots()

    def _save_active_progress(self) -> None:
        if self.active_slot_id is None:
            return
        self.db.save_progress(
            self.active_slot_id,
            score=self.score,
            lives=self.lives,
            level=self.level,
            mission_unlocked=self.mission_unlocked,
            current_streak=self.current_streak,
            max_streak=self.max_streak,
            total_kills=self.total_kills,
        )
        if self.in_menu:
            self._refresh_save_slots()

    def _world_center(self) -> pygame.Vector2:
        return pygame.Vector2(config.WINDOW_WIDTH * 0.5, config.WINDOW_HEIGHT * 0.5)

    def _bounds(self) -> tuple[float, float, float, float]:
        min_x = config.PLAYFIELD_MARGIN + config.WORLD_PADDING
        max_x = config.WINDOW_WIDTH - config.PLAYFIELD_MARGIN - config.WORLD_PADDING
        min_y = config.PLAYFIELD_TOP + config.WORLD_PADDING
        max_y = config.WINDOW_HEIGHT - config.PLAYFIELD_MARGIN - config.WORLD_PADDING
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
            SpawnTarget(self.warlord.pos, self.warlord.radius),
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

    def _reset_world(self) -> None:
        blockers: list[SpawnTarget] = []
        self.player.pos.update(self._random_position(blockers, config.PLAYER_RADIUS))
        blockers.append(SpawnTarget(self.player.pos, self.player.radius))

        self.enemy.pos.update(self._random_position(blockers, self.enemy.radius))
        blockers.append(SpawnTarget(self.enemy.pos, self.enemy.radius))

        self.warlord.pos.update(self._random_position(blockers, self.warlord.radius))
        blockers.append(SpawnTarget(self.warlord.pos, self.warlord.radius))

        self.food.pos.update(self._random_position(blockers, self.food.radius))
        blockers.append(SpawnTarget(self.food.pos, self.food.radius))

        for hazard in self.hazards.values():
            hazard.pos.update(self._random_position(blockers, hazard.radius))
            blockers.append(SpawnTarget(hazard.pos, hazard.radius))

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

        self.player_is_running = direction.length_squared() > 0
        if self.player_is_running:
            direction = direction.normalize()

        if direction.x > 0.1:
            self.player_facing_left = False
        elif direction.x < -0.1:
            self.player_facing_left = True

        self.player.pos += direction * config.PLAYER_SPEED * dt

        min_x, max_x, min_y, max_y = self._bounds()
        self.player.pos.x = clamp(self.player.pos.x, min_x, max_x)
        self.player.pos.y = clamp(self.player.pos.y, min_y, max_y)

    def _move_enemies(self, dt: float) -> None:
        self._move_enemy_towards(self.enemy, dt)
        if self.level >= 5:
            self._move_enemy_towards(self.warlord, dt)

    def _move_enemy_towards(self, enemy: Enemy, dt: float) -> None:
        direction = self.player.pos - enemy.pos
        if direction.length_squared() > 0.01:
            direction = direction.normalize()
            enemy.pos += direction * enemy.speed * dt

    def _collect_food_if_hit(self) -> bool:
        if not self._is_touching(self.player, self.food):
            return False

        self.score += 1
        self.audio.play_sfx("pickup")
        blockers = self._all_spawn_targets()
        self.food.pos.update(self._random_position(blockers, self.food.radius))
        self._relocate_hazards()

        if should_spawn_mega(self.score, config.MEGA_FOOD_SCORE_STEP):
            blockers = self._all_spawn_targets()
            self.mega_food.pos.update(self._random_position(blockers, self.mega_food.radius))
            self.mega_food.active = True
            self.timers.mega_expires_at = time.time() + config.MEGA_FOOD_DURATION
            self.status_text = f"Rare cache active for {int(config.MEGA_FOOD_DURATION)}s"
        else:
            self.status_text = "Supply crate recovered. Hazards shifted."

        return True

    def _collect_mega_if_hit(self) -> bool:
        if not self.mega_food.active:
            return False
        if not self._is_touching(self.player, self.mega_food):
            return False

        self.mega_food.active = False
        self.timers.mega_expires_at = None
        self.score += 3
        self.status_text = "Rare cache bonus +3"
        self.audio.play_sfx("mega")
        self.effects.spawn_hit(self.mega_food.pos, pygame.Vector2(1, 0))
        return True

    def _after_score_changed(self) -> None:
        new_level = level_from_score(self.score, config.LEVEL_UP_SCORE)
        if new_level != self.level:
            self.level = new_level
            self.mission_unlocked = max(self.mission_unlocked, self.level)
            self.status_text = f"Mission {self.level}: {self._theme_name()}"
            self.audio.play_sfx("level_up")
            self.terrain_worker.request(self.level)
            self.terrain_worker.request(self.level + 1)
            self.background_level = -1

        self._check_achievements()
        self._save_active_progress()

    def _tick_event_banner(self, now: float) -> None:
        if self.event_expires_at is not None and now >= self.event_expires_at:
            self.event_text = ""
            self.event_expires_at = None

    def _tick_achievement_banner(self, now: float) -> None:
        if self.achievement_toast_expires_at is not None and now >= self.achievement_toast_expires_at:
            self.achievement_toast = ""
            self.achievement_toast_expires_at = None

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
                self.audio.play_sfx("weapon_pick")
                picked = True

        if picked:
            self.timers.weapon_respawn_at = None
            self._save_active_progress()

    def _select_weapon(self, slot: WeaponSlot) -> None:
        self.inventory.selected = slot
        if self.inventory.slots[slot.value]:
            self.status_text = f"Selected {self._weapon_label(slot)} READY"
        else:
            self.status_text = f"Selected {self._weapon_label(slot)} EMPTY"

    def _fire_weapon(self) -> None:
        if self.level < config.WEAPON_UNLOCK_LEVEL:
            self.status_text = "Weapons unlock at mission 3"
            self.audio.play_sfx("empty")
            return

        target = self._nearest_enemy_in_range(max_distance=320.0)
        aim_direction = pygame.Vector2(-1 if self.player_facing_left else 1, 0)
        if target is not None:
            delta = target.pos - self.player.pos
            if delta.length_squared() > 0:
                aim_direction = delta.normalize()

        if target is None:
            self.status_text = "No target in range"
            self.audio.play_sfx("empty")
            return

        selected = self.inventory.selected

        if selected is WeaponSlot.ARROW and self.inventory.slots[WeaponSlot.ARROW.value]:
            self.inventory.slots[WeaponSlot.ARROW.value] = False
            self.effects.spawn_muzzle_flash(self.player.pos, aim_direction)
            self.audio.play_sfx("fire")
            self._apply_weapon_kill(target, "Arrow strike", aim_direction)
            return

        if selected is WeaponSlot.GUN and self.inventory.slots[WeaponSlot.GUN.value]:
            if self.inventory.gun_bullets <= 0:
                self.inventory.slots[WeaponSlot.GUN.value] = False
                self.status_text = "Out of bullets"
                self.audio.play_sfx("empty")
                return
            self.inventory.gun_bullets -= 1
            if self.inventory.gun_bullets <= 0:
                self.inventory.slots[WeaponSlot.GUN.value] = False
            self.effects.spawn_muzzle_flash(self.player.pos, aim_direction)
            self.audio.play_sfx("fire")
            self._apply_weapon_kill(target, f"Gun burst ({self.inventory.gun_bullets} left)", aim_direction)
            return

        if selected is WeaponSlot.CAPTURE and self.inventory.slots[WeaponSlot.CAPTURE.value]:
            if target is not self.enemy:
                self.status_text = "Capture beam works only on regular zombie"
                self.audio.play_sfx("empty")
                return
            if self.inventory.capture_charges <= 0:
                self.inventory.slots[WeaponSlot.CAPTURE.value] = False
                self.status_text = "No capture charges"
                self.audio.play_sfx("empty")
                return
            self.inventory.capture_charges -= 1
            if self.inventory.capture_charges <= 0:
                self.inventory.slots[WeaponSlot.CAPTURE.value] = False
            self.effects.spawn_muzzle_flash(self.player.pos, aim_direction)
            self.audio.play_sfx("fire")
            self._apply_weapon_kill(target, "Zombie contained", aim_direction)
            return

        self.status_text = "Selected weapon slot is empty"
        self.audio.play_sfx("empty")

    def _apply_weapon_kill(self, target: Enemy, action_text: str, hit_direction: pygame.Vector2) -> None:
        self.score += config.WEAPON_SCORE_BONUS
        self.total_kills += 1

        hit_position = target.pos.copy()
        self.effects.spawn_hit(hit_position, hit_direction)
        self._trigger_camera_shake(config.CAMERA_SHAKE_DEFAULT_STRENGTH, config.CAMERA_SHAKE_DEFAULT_DURATION)
        self.audio.play_sfx("hit")

        blockers = self._all_spawn_targets()
        target.pos.update(self._random_position(blockers, target.radius))

        now = time.time()
        if self.last_kill_at is not None and (now - self.last_kill_at) <= config.KILL_STREAK_WINDOW:
            self.current_streak += 1
        else:
            self.current_streak = 1
        self.last_kill_at = now
        self.max_streak = max(self.max_streak, self.current_streak)

        streak_note = ""
        if self.current_streak >= 2:
            streak_note = f" | STREAK x{self.current_streak}"

        if target.kind == "warlord":
            streak_note += f" | {self._theme_name()} WARLORD DOWN"

        self.status_text = f"{action_text} +{config.WEAPON_SCORE_BONUS}{streak_note}"
        if streak_note:
            self.event_text = streak_note.replace(" | ", " ").strip()
            self.event_expires_at = now + 1.4

        self._after_score_changed()
        self._check_achievements()
        self.timers.weapon_respawn_at = time.time() + config.DROP_RESPAWN_SECONDS
        self._save_active_progress()

    def _nearest_enemy_in_range(self, max_distance: float) -> Enemy | None:
        enemies: list[Enemy] = [self.enemy]
        if self.level >= 5:
            enemies.append(self.warlord)

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
        if self.level >= 5 and self._is_touching(self.player, self.warlord):
            return True
        return False

    def _check_hazard_hit(self) -> bool:
        return any(h.active and self._is_touching(self.player, h) for h in self.hazards.values())

    def _lose_life(self, reason: str) -> None:
        self.lives -= 1
        self.current_streak = 0
        self.last_kill_at = None

        self.effects.spawn_damage(self.player.pos)
        self._trigger_camera_shake(config.CAMERA_SHAKE_DAMAGE_STRENGTH, config.CAMERA_SHAKE_DAMAGE_DURATION)
        self.damage_flash_alpha = max(self.damage_flash_alpha, config.MAX_DAMAGE_FLASH_ALPHA)
        self.audio.play_sfx("hurt")

        self.life_bonus.active = False
        self.mega_food.active = False
        for drop in self.weapon_drops.values():
            drop.active = False
        self.inventory.reset()

        if self.lives <= 0:
            self.game_over = True
            self.status_text = f"Eliminated by {reason}. R: retry mission, M: save hub"
            self._save_active_progress()
            return

        self.timers.next_life_spawn_at = time.time() + config.LIFE_RESPAWN_DELAY
        self.timers.life_expires_at = None
        self.timers.mega_expires_at = None
        self.timers.weapon_respawn_at = time.time() + config.DROP_RESPAWN_SECONDS

        self._reset_world()
        self.status_text = "Life lost. Medical kit arrives in 10s."
        self._check_achievements()
        self._save_active_progress()

    def _check_achievements(self) -> None:
        if self.active_slot_id is None:
            return

        checks: list[tuple[AchievementDef, bool]] = []
        for ach in ACHIEVEMENTS:
            if ach.key == "first_blood":
                checks.append((ach, self.total_kills >= 1))
            elif ach.key == "streak_3":
                checks.append((ach, self.max_streak >= 3))
            elif ach.key == "level_5":
                checks.append((ach, self.level >= 5))
            elif ach.key == "score_100":
                checks.append((ach, self.score >= 100))
            elif ach.key == "last_stand":
                checks.append((ach, self.lives == 1 and not self.game_over and self.score >= 20))

        for ach, unlocked in checks:
            if not unlocked or ach.key in self.unlocked_achievements:
                continue
            created = self.db.unlock_achievement(self.active_slot_id, ach.key, ach.title, ach.description)
            if created:
                self.unlocked_achievements.add(ach.key)
                self.achievement_toast = f"Achievement Unlocked: {ach.title}"
                self.achievement_toast_expires_at = time.time() + 3.2
                self.audio.play_sfx("level_up")

    def _relocate_hazards(self) -> None:
        for hazard in self.hazards.values():
            blockers = self._all_spawn_targets()
            hazard.pos.update(self._random_position(blockers, hazard.radius))

    def _is_touching(self, a: Actor | Pickup, b: Actor | Pickup, margin: float = 0.0) -> bool:
        return collided(a.pos.x, a.pos.y, a.radius, b.pos.x, b.pos.y, b.radius, margin=margin)

    def _reset_feedback_effects(self) -> None:
        self.camera_offset.update(0, 0)
        self.shake_time_left = 0.0
        self.shake_total_time = 0.0
        self.shake_strength = 0.0
        self.damage_flash_alpha = 0.0
        self.effects.particles.clear()
        self.effects.rings.clear()
        self.effects.slashes.clear()

    def _trigger_camera_shake(self, strength: float, duration: float) -> None:
        if duration <= 0:
            return
        self.shake_strength = max(self.shake_strength, strength)
        self.shake_time_left = max(self.shake_time_left, duration)
        self.shake_total_time = max(self.shake_total_time, duration)

    def _update_feedback_effects(self, dt: float) -> None:
        if self.shake_time_left > 0:
            self.shake_time_left = max(0.0, self.shake_time_left - dt)
            falloff = self.shake_time_left / max(0.001, self.shake_total_time)
            intensity = self.shake_strength * falloff
            self.camera_offset.x = random.uniform(-intensity, intensity)
            self.camera_offset.y = random.uniform(-intensity, intensity)
            if self.shake_time_left <= 0:
                self.shake_strength = 0.0
                self.shake_total_time = 0.0
                self.camera_offset.update(0, 0)

        if self.damage_flash_alpha > 0:
            self.damage_flash_alpha = max(0.0, self.damage_flash_alpha - config.DAMAGE_FLASH_DECAY * dt)

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

        # Horizon haze and ruined skyline blocks for a clean apocalyptic look.
        horizon_y = config.PLAYFIELD_TOP + 70
        haze = pygame.Surface((config.WINDOW_WIDTH, 140), pygame.SRCALPHA)
        for i in range(140):
            alpha = max(0, 120 - i)
            pygame.draw.line(haze, (110, 72, 54, alpha), (0, i), (config.WINDOW_WIDTH, i))
        surface.blit(haze, (0, horizon_y - 80))

        skyline_color = (58, 36, 28)
        x = 0
        while x < config.WINDOW_WIDTH:
            w = random.randint(36, 96)
            h = random.randint(28, 92)
            pygame.draw.rect(surface, skyline_color, pygame.Rect(x, horizon_y - h, w, h))
            x += w + random.randint(6, 18)

        # Subtle dust specks only (no graph lines/circles).
        if self.current_decor.level == self.level:
            for x, y, radius in self.current_decor.stars:
                if y < config.PLAYFIELD_TOP:
                    continue
                dust = (156, 116, 90)
                size = 1 if radius <= 2 else 2
                pygame.draw.rect(surface, dust, pygame.Rect(x, y, size, size))

        # Darken lower ground to increase contrast with icons.
        ground = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT - config.PLAYFIELD_TOP), pygame.SRCALPHA)
        ground.fill((20, 8, 5, 70))
        surface.blit(ground, (0, config.PLAYFIELD_TOP))

        pygame.draw.rect(
            surface,
            theme.accent,
            pygame.Rect(
                config.PLAYFIELD_MARGIN,
                config.PLAYFIELD_TOP,
                config.WINDOW_WIDTH - config.PLAYFIELD_MARGIN * 2,
                config.WINDOW_HEIGHT - config.PLAYFIELD_TOP - config.PLAYFIELD_MARGIN,
            ),
            4,
        )

        self.background_surface = surface
        self.background_level = self.level

    def _draw_food(self) -> None:
        self._blit_center(self.sprites.food_surface, self.food.pos)
        if self.mega_food.active:
            self._blit_center(self.sprites.mega_sprite(self.anim_time), self.mega_food.pos)
        if self.life_bonus.active:
            self._blit_center(self.sprites.heart_surface, self.life_bonus.pos)

    def _draw_hazards(self) -> None:
        fire = self.hazards["fire"]
        pothole = self.hazards["pothole"]
        trap = self.hazards["trap"]

        self._blit_center(self.sprites.fire_sprite(self.anim_time), fire.pos)
        self._blit_center(self.sprites.pothole_surface, pothole.pos)
        self._blit_center(self.sprites.trap_surface, trap.pos)

    def _draw_weapon_drops(self) -> None:
        for slot, drop in self.weapon_drops.items():
            if not drop.active:
                continue
            pulse = 21 + int(abs(math.sin(self.anim_time * 4.0)) * 4)
            pygame.draw.circle(self.screen, (131, 198, 255), self._screen_pos(drop.pos), pulse, width=2)
            self._blit_center(self.sprites.weapon_sprite(slot), drop.pos)

    def _draw_player(self) -> None:
        player_sprite = self.sprites.player_sprite(
            anim_time=self.anim_time,
            moving=self.player_is_running,
            facing_left=self.player_facing_left,
        )
        self._blit_center(player_sprite, self.player.pos)

    def _draw_enemy(self, enemy: Enemy) -> None:
        enemy_sprite = self.sprites.zombie_sprite(self.anim_time, brute=(enemy.kind == "warlord"))
        self._blit_center(enemy_sprite, enemy.pos)

    def _blit_center(self, sprite: pygame.Surface, position: pygame.Vector2) -> None:
        rect = sprite.get_rect(center=self._screen_pos(position))
        self.screen.blit(sprite, rect)

    def _screen_pos(self, position: pygame.Vector2) -> tuple[int, int]:
        return int(position.x + self.camera_offset.x), int(position.y + self.camera_offset.y)

    def _draw_hud(self) -> None:
        hud = pygame.Rect(config.HUD_X, config.HUD_Y, config.WINDOW_WIDTH - config.HUD_X * 2, config.HUD_HEIGHT)
        pygame.draw.rect(self.screen, (35, 18, 12), hud, border_radius=10)
        pygame.draw.rect(self.screen, (204, 123, 76), hud, width=3, border_radius=10)

        score_text = self.font_h2.render(f"Score: {self.score:03d}", True, config.TEXT_COLOR)
        level_text = self.font_h2.render(f"Mission: {self.level}", True, config.TEXT_COLOR)
        lives_text = self.font_h3.render(f"Lives: {self.lives}", True, config.TEXT_COLOR)
        fps_text = self.font_sm.render(f"FPS {self.clock.get_fps():5.1f}", True, (255, 206, 169))
        save_text = self.font_sm.render(f"Save: {self.active_slot_name if self.active_slot_id else '-'}", True, (233, 194, 166))

        weapon_text = self.font_sm.render(self._weapon_display_text(), True, config.TEXT_COLOR)
        status_text = self.font_sm.render(self.status_text[:130], True, (255, 219, 186))

        self.screen.blit(score_text, (32, 24))
        self.screen.blit(level_text, (248, 24))
        self.screen.blit(lives_text, (430, 28))
        self.screen.blit(save_text, (560, 28))
        self.screen.blit(weapon_text, (32, 58))
        self.screen.blit(status_text, (430, 58))
        self.screen.blit(fps_text, (config.WINDOW_WIDTH - 120, 62))

        if self.event_text:
            self._draw_center_text(self.event_text, self.font_h3, config.WARNING_COLOR, y=118)

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

    def _weapon_display_text(self) -> str:
        if self.level < config.WEAPON_UNLOCK_LEVEL:
            return "Weapons: locked until mission 3"

        selected = self.inventory.selected
        selected_name = self._weapon_label(selected)
        return (
            f"Weapons {self.inventory.loaded_count()}/{config.WEAPON_MAX_COUNT}"
            f" | Selected: {selected_name}"
            " | Z pick | 1/2/3 select | X fire"
        )


def main() -> int:
    game = Game()
    game.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
