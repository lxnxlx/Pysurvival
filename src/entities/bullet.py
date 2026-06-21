"""Projectile entity."""

from __future__ import annotations

import pygame

from src.core.constants import (
    BULLET_LIFETIME,
    BULLET_SIZE,
    BULLET_SPEED,
    YELLOW,
)
from src.entities.base import Entity


class Bullet(Entity):
    def __init__(
        self,
        center: pygame.Vector2,
        direction: pygame.Vector2,
    ) -> None:
        position = center - pygame.Vector2(BULLET_SIZE / 2, BULLET_SIZE / 2)
        super().__init__(position, BULLET_SIZE, YELLOW)
        self.direction = direction
        self.lifetime = BULLET_LIFETIME

    def update(self, dt: float) -> None:
        self.position += self.direction * BULLET_SPEED * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        pygame.draw.circle(
            surface,
            self.color,
            self.rect.move(-camera.x, -camera.y).center,
            self.size // 2,
        )
