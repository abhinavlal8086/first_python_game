# Ultimate Collect HD

An arcade-style survival game rebuilt with `pygame` for smoother performance, HD visuals, and cleaner architecture.

## What Changed

- Upgraded from `turtle` to `pygame` for faster rendering and input handling.
- Modularized into a package (`game/`) with separate config, entities, logic, persistence, and terrain worker modules.
- Added background multithreading for terrain decoration precompute.
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
- Kill streak event banner
- Persistent high score (`high_score.json`)
- FPS indicator in HUD

## Project Structure

```text
.
├── .github/workflows/ci.yml
├── game/
│   ├── __init__.py
│   ├── config.py
│   ├── entities.py
│   ├── game.py
│   ├── logic.py
│   ├── storage.py
│   └── terrain_worker.py
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
- High score writes are asynchronous to avoid frame hitching.

## License

This project is licensed under the terms in the [LICENSE](LICENSE) file.
