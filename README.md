# Ultimate Collect Game

A lightweight arcade-style Python game built with `turtle`. Move quickly, collect food, avoid hazards, and survive as the difficulty ramps up with levels and terrain changes.

## Features

- Real-time player movement using arrow keys
- Enemy chase behavior that scales with level
- Obstacle hazards (fire, pothole, trap)
- Lives system with delayed bonus-heart recovery
- Level progression every 10 points
- Terrain theme updates as levels increase
- Mega food bonus every 15 points (available for 5 seconds)
- Pause and restart controls

## Tech Stack

- Python 3.11+
- Standard library only (`turtle`, `random`, `time`, `math`)

## Project Structure

```
.
├── main.py
├── README.md
└── LICENSE
```

## Getting Started

1. Clone the repository:

```bash
git clone https://github.com/abhinavlal8086/first_python_game.git
cd first_python_game
```

2. Run the game:

```bash
python main.py
```

## Controls

- `Up` / `Down` / `Left` / `Right`: Move player
- `P`: Pause / Resume
- `R`: Restart game

## Gameplay Rules

- Collect regular food to increase score.
- Avoid the monster and obstacle icons; collisions cost one life.
- Bonus heart appears after life loss (timed pickup) to regain life.
- Every 10 points, you enter a new level with increased speed and a different terrain style.
- Every 15 points, mega food spawns for 5 seconds and gives bonus score.

## Future Improvements

- High score persistence
- Sound effects and music
- Additional enemy types and level-specific mechanics
- Start menu and difficulty selection

## License

This project is licensed under the terms in the [LICENSE](LICENSE) file.
