"""Collectable objects and portal-like trigger entities."""

from __future__ import annotations

from pathlib import Path

import pygame

from src.core.constants import (
    BLUE,
    CYAN,
    GREEN,
    INVULNERABILITY_ORB_SPRITE_FILE,
    INVULNERABILITY_ORB_SIZE,
    KEY_SPRITE_FILE,
    KEY_SIZE,
    MEDKIT_SPRITE_FILE,
    MEDKIT_SIZE,
    ORANGE,
    PORTAL_OUTLINE_WIDTH,
    PORTAL_SIZE,
)
from src.core.sprite_cache import SpriteCache
from src.entities.base import Entity


class SpritePickup(Entity):
    def __init__(
        self,
        position: pygame.Vector2,
        size: int,
        color: tuple[int, int, int],
        sprite_file: Path,
    ) -> None:
        super().__init__(position, size, color)
        self._sprite = SpriteCache.get(sprite_file, size)

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        rect = self.rect.move(-camera.x, -camera.y)
        surface.blit(self._sprite, rect)


class Key(SpritePickup):
    def __init__(self, position: pygame.Vector2) -> None:
        super().__init__(position, KEY_SIZE, ORANGE, KEY_SPRITE_FILE)


class Medkit(SpritePickup):
    def __init__(self, position: pygame.Vector2) -> None:
        super().__init__(position, MEDKIT_SIZE, GREEN, MEDKIT_SPRITE_FILE)


class InvulnerabilityOrb(SpritePickup):
    def __init__(self, position: pygame.Vector2) -> None:
        super().__init__(
            position,
            INVULNERABILITY_ORB_SIZE,
            BLUE,
            INVULNERABILITY_ORB_SPRITE_FILE,
        )


class Portal(Entity):
    def __init__(self, position: pygame.Vector2) -> None:
        super().__init__(position, PORTAL_SIZE, CYAN)
        self.unlocked = False

    def unlock(self) -> None:
        self.unlocked = True

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        rect = self.rect.move(-camera.x, -camera.y)
        width = 0 if self.unlocked else PORTAL_OUTLINE_WIDTH
        pygame.draw.ellipse(surface, self.color, rect, width=width)
