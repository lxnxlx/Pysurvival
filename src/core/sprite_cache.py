"""Shared loading and tinting cache for entity sprites."""

from __future__ import annotations

from pathlib import Path

import pygame

Color = tuple[int, int, int]
SpriteKey = tuple[Path, int, Color | None]


class SpriteCache:
    _sprites: dict[SpriteKey, pygame.Surface] = {}

    @classmethod
    def get(
        cls,
        sprite_file: Path,
        size: int,
        tint: Color | None = None,
    ) -> pygame.Surface:
        key = (sprite_file, size, tint)
        if key not in cls._sprites:
            image = pygame.image.load(str(sprite_file))
            if pygame.display.get_surface() is not None:
                image = image.convert_alpha()
            sprite = pygame.transform.scale(image, (size, size))
            if tint is not None:
                sprite.fill(
                    (*tint, 255),
                    special_flags=pygame.BLEND_RGBA_MULT,
                )
            cls._sprites[key] = sprite
        return cls._sprites[key]
