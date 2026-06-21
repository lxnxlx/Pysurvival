import pygame

from src.entities.pickup import Portal


def test_portal_can_be_unlocked():
    portal = Portal(pygame.Vector2(0, 0))

    portal.unlock()

    assert portal.unlocked
