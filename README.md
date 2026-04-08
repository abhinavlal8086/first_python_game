# Ultimate Collect HD

An apocalyptic arcade survival game built with `pygame`, featuring SQLite save slots, mission replay, achievements, animated combat feedback, and HD visuals.

## What Changed

- Upgraded from `turtle` to `pygame` for faster rendering and richer visuals.
- Added a SQLite save hub with multiple local save slots.
- Added mission replay from any unlocked mission.
- Added per-save achievement tracking persisted in SQLite.
- Added pause/settings menu with runtime music and SFX toggles.
- Added hard HUD boundary so gameplay cannot enter behind scoreboard.
- Added apocalyptic visual direction and themed missions.
- Added PNG sprite-sheet asset loading with procedural fallback.
- Added combat feedback: muzzle flash, slash impact, particles, camera shake, and damage flash.
- Added sound effects and looping background music.

## Features

- HD window rendering (`1280x720`) with an apocalyptic theme
- Real-time movement (`WASD` or arrows)
- Zombie chase enemy + themed warlord enemy on higher missions
- Hazards (fire, pothole, trap)
- Life system with delayed medical-kit recovery pickup
- Mega cache bonus every 15 points (timed pickup)
- Weapon system (unlock at mission 3):
  - Arrow (single use)
  - Gun (15 bullets)
  - Capture gun (works on regular zombie)
- Save hub menu:
  - Create new run
  - Continue saved checkpoint
  - Replay any unlocked mission
  - Delete save slot
- SQLite data persistence for score, lives, level, mission unlocks, streaks, kills, and achievements
- FPS indicator in HUD

## Project Structure

```text
.
├── .github/workflows/ci.yml
├── game/
│   ├── __init__.py
│   ├── assets.py
│   ├── audio.py
│   ├── config.py
│   ├── db.py
│   ├── entities.py
│   ├── effects.py
│   ├── game.py
│   ├── logic.py
│   ├── sprites.py
│   ├── storage.py
│   └── terrain_worker.py
├── assets/
│   ├── audio/
│   └── sprites/
├── tools/
│   └── generate_starter_assets.py
├── tests/
│   └── test_logic.py
├── .gitignore
├── LICENSE
├── main.py
├── pyproject.toml
├── README.md
└── requirements.txt
```

## Requirements

- Python 3.11+
- `pygame` (installed from `requirements.txt`)

## Setup

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Controls

### Gameplay
- `WASD` / `Arrow keys`: move
- `P` / `Esc`: open pause/settings menu
- `M`: return to save hub
- `R` or `Space`: retry mission after death
- `Z`: pick up nearby weapon drop
- `1` / `2` / `3`: select Arrow/Gun/Capture weapon
- `X`: fire selected weapon

### Save Hub
- `N`: create new save and start mission 1
- `Up` / `Down`: select save slot
- `Left` / `Right`: choose mission replay (within unlocked range)
- `Enter`: start selected mission replay
- `C`: continue from saved checkpoint
- `Delete`: remove selected save slot

## Regenerate Art/Audio Asset Pack

```bash
python tools/generate_starter_assets.py
```

The game auto-loads PNG/WAV assets if present and falls back to procedural icons/effects when assets are missing.

## Data Storage

- SQLite database file: `apocalypse_saves.db`
- Stores save slots, score, lives, level, mission unlocks, streak stats, kill stats, and unlocked achievements

## Testing

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Lint and Format Checks

```bash
ruff check .
black --check .
```

## Notes on Performance

- Cached background surfaces reduce per-frame drawing overhead.
- Collision checks use squared distance math to avoid unnecessary square roots.
- Terrain decoration data is generated on a worker thread so level transitions remain smooth.
- Sprite-sheet extraction is done once on startup, then reused per frame.
- Particle and flash systems are short-lived and bounded.
- SQLite writes are lightweight and triggered on meaningful progress events.

## License

This project is licensed under the terms in the [LICENSE](LICENSE) file.
