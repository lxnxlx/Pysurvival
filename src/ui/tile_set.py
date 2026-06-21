"""Загрузка и детерминированный выбор спрайтов стен."""

from __future__ import annotations

from pathlib import Path

import pygame


class WallTileSet:
    def __init__(
        self,
        atlas_file: Path,
        tile_size: int,
        columns: int,
    ) -> None:
        atlas = pygame.image.load(str(atlas_file)).convert()
        rows = atlas.get_height() // tile_size
        self._columns = columns
        self._tiles = [
            atlas.subsurface(
                column * tile_size,
                row * tile_size,
                tile_size,
                tile_size,
            ).copy()
            for row in range(rows)
            for column in range(columns)
        ]

    def get_tile(self, x_pos: int, y_pos: int) -> pygame.Surface:
        # Coordinate-based selection keeps the map stable between frames.
        index = (x_pos + y_pos * self._columns) % len(self._tiles)
        return self._tiles[index]
