# Ultimate Collect HD

An arcade-style survival game rebuilt with `pygame` for smoother performance, HD visuals, and cleaner architecture.

## What Changed

- Upgraded from `turtle` to `pygame` for faster rendering and input handling.
- Modularized into a package (`game/`) with separate config, entities, logic, persistence, and terrain worker modules.
- Added background multithreading for terrain decoration precompute.
- Added PNG sprite-sheet asset loading with procedural fallback.
- Added combat feedback: hit slashes, muzzle flashes, and particle bursts.
- Added camera shake and damage flash for impact readability.
- Added sound effects and looping background music.
- Added non-blocking high score persistence with a writer thread.
- Added unit tests and CI checks.

## Features

- HD window rendering (`1280x720`) with themed backgrounds and cached grid visuals
- Real-time movement (`WASD` or arrows)
- Enemy chase behavior and level-based difficulty ramp
- Hazards (fire, pothole, trap)
- Life system with delayed timed heart pickup
- Mega food bonus every 15 points (limited lifetime)
- Weapon system (unlock at level 3):
  - Arrow (single use)
  - Gun (15 bullets)
  - Capture gun (works on devil)
- PNG sprite-sheet character/hazard icon pipeline (`assets/sprites`)
- Hit animations: slash, muzzle flash, impact particles
- Camera shake + damage flash on combat/damage events
- Sound FX + background loop music (`assets/audio`)
- Kill streak event banner
- Persistent high score (`high_score.json`)
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

## Regenerate Art/Audio Asset Pack

If you want to refresh the bundled starter assets:

```bash
python tools/generate_starter_assets.py
```

The game auto-loads PNG/WAV assets if present and falls back to built-in procedural visuals when any asset is missing.

## Controls

- `WASD` / `Arrow keys`: move
- `P`: pause/resume
- `R` or `Space`: restart
- `Z`: pick up nearby weapon drop
- `1` / `2` / `3`: select Arrow/Gun/Capture weapon
- `X`: fire selected weapon

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
- Particle and flash systems are short-lived and capped to maintain stable FPS.
- High score writes are asynchronous to avoid frame hitching.

## License

This project is licensed under the terms in the [LICENSE](LICENSE) file.
