"""Базовые классы сущностей для игровых объектов."""

from __future__ import annotations

from dataclasses import dataclass

import pygame


@dataclass
class Entity:
    position: pygame.Vector2
    size: int
    color: tuple[int, int, int]
    hp: int = 1
    alive: bool = True

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.position.x),
            int(self.position.y),
            self.size,
            self.size,
        )

    @property
    def center(self) -> pygame.Vector2:
        return pygame.Vector2(self.rect.center)

    def take_damage(self, amount: int) -> None:
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        draw_rect = self.rect.move(-camera.x, -camera.y)
        pygame.draw.rect(surface, self.color, draw_rect, border_radius=6)
