"""Generate starter PNG sprite sheets and WAV audio assets."""

from __future__ import annotations

from pathlib import Path
import math
import struct
import wave

import pygame

from game.sprites import SpriteLibrary


ROOT = Path(__file__).resolve().parents[1]
SPRITES_DIR = ROOT / "assets" / "sprites"
AUDIO_DIR = ROOT / "assets" / "audio"


def _save_sheet(path: Path, frames: list[pygame.Surface]) -> None:
    if not frames:
        return
    w, h = frames[0].get_size()
    sheet = pygame.Surface((w * len(frames), h), pygame.SRCALPHA)
    for index, frame in enumerate(frames):
        sheet.blit(frame, (index * w, 0))
    pygame.image.save(sheet, path.as_posix())


def _save_single(path: Path, surface: pygame.Surface) -> None:
    pygame.image.save(surface, path.as_posix())


def _tone_samples(freq: float, seconds: float, volume: float = 0.45, sample_rate: int = 44100) -> bytes:
    frames = int(sample_rate * seconds)
    out = bytearray()
    for i in range(frames):
        t = i / sample_rate
        env = min(1.0, i / max(1, int(sample_rate * 0.015)))
        env *= max(0.0, 1.0 - (i / max(1, frames)) * 0.35)
        sample = math.sin(2.0 * math.pi * freq * t) * volume * env
        value = int(sample * 32767)
        out.extend(struct.pack("<h", value))
    return bytes(out)


def _write_wav(path: Path, pieces: list[bytes], sample_rate: int = 44100) -> None:
    data = b"".join(pieces)
    with wave.open(path.as_posix(), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(data)


def _build_sfx() -> None:
    _write_wav(AUDIO_DIR / "pickup.wav", [_tone_samples(720, 0.07), _tone_samples(980, 0.08)])
    _write_wav(AUDIO_DIR / "mega.wav", [_tone_samples(620, 0.10), _tone_samples(930, 0.14), _tone_samples(1240, 0.10)])
    _write_wav(AUDIO_DIR / "weapon_pick.wav", [_tone_samples(460, 0.08), _tone_samples(740, 0.08)])
    _write_wav(AUDIO_DIR / "fire.wav", [_tone_samples(180, 0.05), _tone_samples(120, 0.08)])
    _write_wav(AUDIO_DIR / "hit.wav", [_tone_samples(250, 0.04), _tone_samples(150, 0.06)])
    _write_wav(AUDIO_DIR / "hurt.wav", [_tone_samples(130, 0.14)])
    _write_wav(AUDIO_DIR / "level_up.wav", [_tone_samples(530, 0.06), _tone_samples(690, 0.08), _tone_samples(890, 0.10)])
    _write_wav(AUDIO_DIR / "empty.wav", [_tone_samples(90, 0.05)])


def _build_music_loop() -> None:
    sequence = [261.63, 329.63, 392.0, 329.63, 293.66, 349.23, 440.0, 349.23]
    pieces: list[bytes] = []
    for _ in range(8):
        for note in sequence:
            pieces.append(_tone_samples(note, 0.16, volume=0.20))
    _write_wav(AUDIO_DIR / "bgm_loop.wav", pieces)


def main() -> None:
    SPRITES_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    pygame.init()
    pygame.display.set_mode((1, 1))

    sprites = SpriteLibrary(use_external=False)

    _save_sheet(SPRITES_DIR / "player_runner_sheet.png", sprites.runner_frames)
    _save_sheet(SPRITES_DIR / "zombie_sheet.png", sprites.zombie_frames)
    _save_sheet(SPRITES_DIR / "brute_sheet.png", sprites.brute_frames)
    _save_sheet(SPRITES_DIR / "fire_sheet.png", sprites.fire_frames)
    _save_sheet(SPRITES_DIR / "mega_sheet.png", sprites.mega_frames)

    _save_single(SPRITES_DIR / "hazard_trap.png", sprites.trap_surface)
    _save_single(SPRITES_DIR / "hazard_pothole.png", sprites.pothole_surface)
    _save_single(SPRITES_DIR / "pickup_food.png", sprites.food_surface)
    _save_single(SPRITES_DIR / "pickup_heart.png", sprites.heart_surface)
    _save_single(SPRITES_DIR / "weapon_arrow.png", sprites.weapon_icons[sprites.weapon_icons.keys().__iter__().__next__()])
    _save_single(SPRITES_DIR / "weapon_gun.png", sprites.weapon_icons[list(sprites.weapon_icons.keys())[1]])
    _save_single(SPRITES_DIR / "weapon_capture.png", sprites.weapon_icons[list(sprites.weapon_icons.keys())[2]])

    _build_sfx()
    _build_music_loop()

    pygame.quit()
    print("Starter assets generated in assets/sprites and assets/audio")


if __name__ == "__main__":
    main()
