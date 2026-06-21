# PySurvival: Zombie Waves

Simple top-down shooter inspired by Alien Shooter. The player clears two
laboratory levels and then enters an endless zombie wave mode.

## Run

```bash
python -m pip install -r requirements.txt
python -m src.main
```

## Controls

- `WASD` - move
- Mouse - aim
- Left mouse button - shoot
- `E` - use door or portal
- `Esc` - pause

## Project Structure

Detailed Mermaid diagram: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

- `src/core` - game loop, states, constants, level loading
- `src/entities` - player, zombies, bullets, pickups
- `src/managers` - collisions, pathfinding, saving, waves, entity storage
- `src/ui` - buttons and screen drawing
- `data/levels` - JSON level data
- `data/saves` - save and score files
- `tests` - pure logic tests
