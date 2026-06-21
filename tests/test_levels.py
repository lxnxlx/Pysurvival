import json
from pathlib import Path


def test_level_special_positions_are_walkable():
    for path in Path("data/levels").glob("level_*.json"):
        level = json.loads(path.read_text(encoding="utf-8"))
        positions = [
            level["player_spawn"],
            level["exit_position"],
            *level["zombie_spawns"],
        ]
        if level["key_position"] is not None:
            positions.append(level["key_position"])

        for x_pos, y_pos in positions:
            assert level["grid"][y_pos][x_pos] != "#", (
                f"{path} has blocked special position {(x_pos, y_pos)}"
            )
