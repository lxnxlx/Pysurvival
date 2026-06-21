"""Collectable objects and portal-like trigger entities."""

from __future__ import annotations

import pygame

from src.core.constants import (
    CYAN,
    BLUE,
    GREEN,
    INVULNERABILITY_ORB_SIZE,
    KEY_SIZE,
    MEDKIT_SIZE,
    ORANGE,
    PORTAL_SIZE,
    RED,
)
from src.entities.base import Entity


class Key(Entity):
    def __init__(self, position: pygame.Vector2) -> None:
        super().__init__(position, KEY_SIZE, ORANGE)


class Medkit(Entity):
    def __init__(self, position: pygame.Vector2) -> None:
        super().__init__(position, MEDKIT_SIZE, GREEN)

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        rect = self.rect.move(-camera.x, -camera.y)
        pygame.draw.rect(surface, self.color, rect, border_radius=5)
        # The red cross makes medkits readable even on a busy tile map.
        pygame.draw.rect(surface, RED, rect.inflate(-8, -18))
        pygame.draw.rect(surface, RED, rect.inflate(-18, -8))


class InvulnerabilityOrb(Entity):
    def __init__(self, position: pygame.Vector2) -> None:
        super().__init__(position, INVULNERABILITY_ORB_SIZE, BLUE)

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        rect = self.rect.move(-camera.x, -camera.y)
        pygame.draw.ellipse(surface, self.color, rect)
        pygame.draw.ellipse(surface, CYAN, rect, width=3)


class Portal(Entity):
    def __init__(self, position: pygame.Vector2) -> None:
        super().__init__(position, PORTAL_SIZE, CYAN)

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        rect = self.rect.move(-camera.x, -camera.y)
        pygame.draw.ellipse(surface, self.color, rect, width=5)
