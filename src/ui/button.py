"""Minimal button widget for pygame menus."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from src.core.constants import DARK_GRAY, GRAY, WHITE


class Button:
    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        action: Callable[[], None],
    ) -> None:
        self.rect = rect
        self.label = label
        self.action = action

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.action()

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        mouse_over = self.rect.collidepoint(pygame.mouse.get_pos())
        color = GRAY if mouse_over else DARK_GRAY
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, WHITE, self.rect, width=2, border_radius=8)
        text = font.render(self.label, True, WHITE)
        surface.blit(text, text.get_rect(center=self.rect.center))
