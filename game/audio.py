"""Audio system for SFX and background music."""

from __future__ import annotations

from pathlib import Path

import pygame


class AudioSystem:
    def __init__(self, asset_root: Path) -> None:
        self.enabled = False
        self.sfx: dict[str, pygame.mixer.Sound] = {}
        self.music_path: Path | None = None

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.enabled = True
        except pygame.error:
            self.enabled = False
            return

        audio_dir = asset_root / "audio"
        self._load_sfx(audio_dir)
        music_candidate = audio_dir / "bgm_loop.wav"
        if music_candidate.exists():
            self.music_path = music_candidate

    def _load_sfx(self, audio_dir: Path) -> None:
        files = {
            "pickup": "pickup.wav",
            "mega": "mega.wav",
            "weapon_pick": "weapon_pick.wav",
            "fire": "fire.wav",
            "hit": "hit.wav",
            "hurt": "hurt.wav",
            "level_up": "level_up.wav",
            "empty": "empty.wav",
        }
        for key, name in files.items():
            path = audio_dir / name
            if not path.exists():
                continue
            try:
                sound = pygame.mixer.Sound(path.as_posix())
                sound.set_volume(0.42)
                self.sfx[key] = sound
            except pygame.error:
                continue

    def start_music(self) -> None:
        if not self.enabled or self.music_path is None:
            return
        try:
            pygame.mixer.music.load(self.music_path.as_posix())
            pygame.mixer.music.set_volume(0.35)
            pygame.mixer.music.play(-1)
        except pygame.error:
            return

    def stop_music(self) -> None:
        if not self.enabled:
            return
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            return

    def play_sfx(self, key: str) -> None:
        if not self.enabled:
            return
        sound = self.sfx.get(key)
        if sound is None:
            return
        try:
            sound.play()
        except pygame.error:
            return

    def shutdown(self) -> None:
        self.stop_music()
