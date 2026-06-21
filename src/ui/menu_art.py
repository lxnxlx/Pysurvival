"""Background and character composition for the main menu."""

from __future__ import annotations

import pygame

from src.core.constants import (
    BLUE_ENEMY_SPRITE_FILE,
    MENU_BACKGROUND_FILE,
    NORMAL_ENEMY_SPRITE_FILE,
    PLAYER_SPRITE_FILE,
    RED_ENEMY_SPRITE_FILE,
)
from src.core.sprite_cache import SpriteCache


class MenuArt:
    def __init__(self) -> None:
        self._background = pygame.image.load(
            str(MENU_BACKGROUND_FILE)
        ).convert()
        self._player = SpriteCache.get(PLAYER_SPRITE_FILE, 480)
        self._enemy_normal = SpriteCache.get(
            NORMAL_ENEMY_SPRITE_FILE,
            78,
        )
        self._enemy_red = SpriteCache.get(RED_ENEMY_SPRITE_FILE, 90)
        self._enemy_blue = SpriteCache.get(BLUE_ENEMY_SPRITE_FILE, 72)

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self._background, (0, 0))
        self._draw_enemy_horde(surface)
        surface.blit(self._player, (545, 175))

    def _draw_enemy_horde(self, surface: pygame.Surface) -> None:
        back_row = [
            (self._enemy_normal, (25, 610)),
            (self._enemy_blue, (102, 620)),
            (self._enemy_normal, (175, 605)),
            (self._enemy_red, (250, 607)),
            (self._enemy_normal, (340, 612)),
            (self._enemy_blue, (415, 620)),
        ]
        front_row = [
            (self._enemy_red, (65, 668)),
            (self._enemy_normal, (160, 680)),
            (self._enemy_blue, (245, 684)),
            (self._enemy_red, (330, 670)),
            (self._enemy_normal, (425, 682)),
        ]
        for sprite, position in back_row + front_row:
            surface.blit(sprite, position)
