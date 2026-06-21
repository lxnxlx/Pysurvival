"""Zombie entity that uses grid pathfinding."""

from __future__ import annotations

from pathlib import Path

import pygame

from src.core.constants import (
    GREEN,
    NORMAL_ENEMY_SPRITE_FILE,
    NORMAL_ZOMBIE_KIND,
    NORMAL_ZOMBIE_SCORE,
    TILE_SIZE,
    ZOMBIE_ATTACK_COOLDOWN,
    ZOMBIE_DAMAGE,
    ZOMBIE_HP,
    ZOMBIE_REPATH_SECONDS,
    ZOMBIE_SIZE,
    ZOMBIE_SPEED,
)
from src.core.sprite_cache import SpriteCache
from src.entities.base import Entity
from src.managers.pathfinder import Pathfinder


class Zombie(Entity):
    def __init__(
        self,
        position: pygame.Vector2,
        color: tuple[int, int, int] = GREEN,
        hp_multiplier: int = 1,
        wave_number: int = 0,
        score_value: int = NORMAL_ZOMBIE_SCORE,
        sprite_file: Path = NORMAL_ENEMY_SPRITE_FILE,
        kind: str = NORMAL_ZOMBIE_KIND,
    ) -> None:
        super().__init__(position, ZOMBIE_SIZE, color, ZOMBIE_HP)
        self.hp *= hp_multiplier
        self.wave_number = wave_number
        self.score_value = score_value
        self.kind = kind
        self._sprite = SpriteCache.get(sprite_file, self.size)
        self.attack_timer = 0.0
        self._path_timer = 0.0
        self._path: list[tuple[int, int]] = []

    def update(
        self,
        dt: float,
        target: pygame.Vector2,
        pathfinder: Pathfinder,
        walls: list[pygame.Rect],
    ) -> None:
        self.attack_timer = max(0.0, self.attack_timer - dt)
        self._path_timer = max(0.0, self._path_timer - dt)
        if self._path_timer == 0:
            self._path = self._build_path(target, pathfinder)
            self._path_timer = ZOMBIE_REPATH_SECONDS

        direction = self._next_direction(target)
        if direction.length_squared() > 0:
            self.position += direction.normalize() * ZOMBIE_SPEED * dt
            self.resolve_walls(walls)

    def can_attack(self) -> bool:
        return self.attack_timer == 0

    def reset_attack(self) -> None:
        self.attack_timer = ZOMBIE_ATTACK_COOLDOWN

    def damage(self) -> int:
        return ZOMBIE_DAMAGE

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        rect = self.rect.move(-camera.x, -camera.y)
        surface.blit(self._sprite, rect)

    def _build_path(
        self,
        target: pygame.Vector2,
        pathfinder: Pathfinder,
    ) -> list[tuple[int, int]]:
        start = (
            int(self.center.x // TILE_SIZE),
            int(self.center.y // TILE_SIZE),
        )
        goal = (int(target.x // TILE_SIZE), int(target.y // TILE_SIZE))
        return pathfinder.find_path(start, goal)

    def _next_direction(self, target: pygame.Vector2) -> pygame.Vector2:
        if len(self._path) > 1:
            tile_x, tile_y = self._path[1]
            next_point = pygame.Vector2(
                tile_x * TILE_SIZE + TILE_SIZE / 2,
                tile_y * TILE_SIZE + TILE_SIZE / 2,
            )
            return next_point - self.center
        return target - self.center

    def resolve_walls(self, walls: list[pygame.Rect]) -> None:
        """Push the zombie outside walls after movement or separation."""
        for wall in walls:
            if self.rect.colliderect(wall):
                delta = (
                    pygame.Vector2(self.center)
                    - pygame.Vector2(wall.center)
                )
                if abs(delta.x) > abs(delta.y):
                    self.position.x = (
                        wall.right if delta.x > 0 else wall.left - self.size
                    )
                else:
                    self.position.y = (
                        wall.bottom if delta.y > 0 else wall.top - self.size
                    )
