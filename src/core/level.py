"""Level model and JSON loading."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.core.constants import LEVEL_DIR, TILE_SIZE


@dataclass(frozen=True)
class Level:
    level_id: int
    title: str
    grid: list[str]
    player_spawn: tuple[int, int]
    zombie_spawns: list[tuple[int, int]]
    key_position: tuple[int, int] | None
    exit_position: tuple[int, int]
    wave_size: int

    @property
    def pixel_size(self) -> tuple[int, int]:
        return len(self.grid[0]) * TILE_SIZE, len(self.grid) * TILE_SIZE

    def is_wall_tile(self, tile_x: int, tile_y: int) -> bool:
        if tile_y < 0 or tile_y >= len(self.grid):
            return True
        if tile_x < 0 or tile_x >= len(self.grid[tile_y]):
            return True
        return self.grid[tile_y][tile_x] == "#"

    def wall_rects(self) -> list[tuple[int, int, int, int]]:
        rects = []
        for y_pos, row in enumerate(self.grid):
            for x_pos, tile in enumerate(row):
                if tile == "#":
                    rects.append(
                        (
                            x_pos * TILE_SIZE,
                            y_pos * TILE_SIZE,
                            TILE_SIZE,
                            TILE_SIZE,
                        )
                    )
        return rects


class LevelLoader:
    def __init__(self, level_dir: Path = LEVEL_DIR) -> None:
        self._level_dir = level_dir

    def load(self, level_id: int) -> Level:
        path = self._level_dir / f"level_{level_id}.json"
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        return Level(
            level_id=int(payload["id"]),
            title=payload["title"],
            grid=payload["grid"],
            player_spawn=tuple(payload["player_spawn"]),
            zombie_spawns=[tuple(item) for item in payload["zombie_spawns"]],
            key_position=(
                tuple(payload["key_position"])
                if payload.get("key_position") is not None
                else None
            ),
            exit_position=tuple(payload["exit_position"]),
            wave_size=int(payload["wave_size"]),
        )
