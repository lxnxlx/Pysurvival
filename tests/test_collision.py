from dataclasses import dataclass

import pygame

from src.entities.zombie import Zombie
from src.managers.collision_manager import CollisionManager


@dataclass
class RectStub:
    left: int
    top: int
    width: int
    height: int

    @property
    def right(self):
        return self.left + self.width

    @property
    def bottom(self):
        return self.top + self.height


def test_intersects_detects_aabb_overlap():
    left = RectStub(0, 0, 10, 10)
    right = RectStub(5, 5, 10, 10)

    assert CollisionManager.intersects(left, right)


def test_intersects_ignores_touching_edges():
    left = RectStub(0, 0, 10, 10)
    right = RectStub(10, 0, 10, 10)

    assert not CollisionManager.intersects(left, right)


def test_separate_removes_entity_overlap():
    left = Zombie(pygame.Vector2(100, 100))
    right = Zombie(pygame.Vector2(110, 100))

    CollisionManager.separate(left, right)

    assert not left.rect.colliderect(right.rect)
