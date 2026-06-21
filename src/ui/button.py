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
        base_color: tuple[int, int, int] = DARK_GRAY,
        hover_color: tuple[int, int, int] = GRAY,
        border_color: tuple[int, int, int] = WHITE,
        accent_color: tuple[int, int, int] | None = None,
    ) -> None:
        self.rect = rect
        self.label = label
        self.action = action
        self.base_color = base_color
        self.hover_color = hover_color
        self.border_color = border_color
        self.accent_color = accent_color

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.action()

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        mouse_over = self.rect.collidepoint(pygame.mouse.get_pos())
        color = self.hover_color if mouse_over else self.base_color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(
            surface,
            self.border_color,
            self.rect,
            width=2,
            border_radius=8,
        )
        if self.accent_color is not None:
            accent_rect = pygame.Rect(
                self.rect.x,
                self.rect.y,
                6,
                self.rect.height,
            )
            pygame.draw.rect(
                surface,
                self.accent_color,
                accent_rect,
                border_radius=3,
            )
        text = font.render(self.label, True, WHITE)
        surface.blit(text, text.get_rect(center=self.rect.center))
