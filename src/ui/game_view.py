"""Отрисовка игровых состояний и активного уровня."""

from __future__ import annotations

import pygame

from src.core.constants import (
    BLACK,
    BLUE,
    GAME_OVER_STATE,
    GRAY,
    HUD_HEIGHT,
    HUD_MARGIN,
    HUD_TEXT_Y,
    LEVEL_ONE_ID,
    MENU_BUTTON_ACCENT_COLOR,
    MENU_BUTTON_BASE_COLOR,
    MENU_STATE,
    MENU_SUBTITLE_COLOR,
    MENU_TITLE_COLOR,
    ORANGE,
    PAUSE_STATE,
    PLAYING_STATE,
    RED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SCORES_STATE,
    TILE_SIZE,
    VICTORY_STATE,
    WHITE,
    YELLOW,
)
from src.core.level import Level
from src.managers.entity_manager import EntityManager
from src.managers.save_system import ScoreEntry
from src.ui.button import Button
from src.ui.menu_art import MenuArt
from src.ui.tile_set import WallTileSet

MENU_TITLE_POSITION = (55, 42)
MENU_SUBTITLE_POSITION = (78, 116)
MENU_RULE_START = (70, 164)
MENU_RULE_END = (338, 164)
NAME_INPUT_RECT = pygame.Rect(70, 224, 270, 44)
PAUSE_OVERLAY_ALPHA = 150
HUD_SCORE_X = 130
HUD_KEY_X = 310
HUD_BUFF_X = 450
HUD_LEVEL_X = 650
FIRST_LEVEL_HINT_RECT = pygame.Rect(18, HUD_HEIGHT + 12, 520, 76)


class GameView:
    """Отрисовывает экраны, не изменяя состояние игрового процесса."""

    def __init__(
        self,
        screen: pygame.Surface,
        clock: pygame.time.Clock,
        wall_tiles: WallTileSet,
    ) -> None:
        self.screen = screen
        self.clock = clock
        self.wall_tiles = wall_tiles
        self.font = pygame.font.SysFont("arial", 24)
        self.large_font = pygame.font.SysFont("arial", 52, bold=True)
        self.menu_title_font = pygame.font.SysFont("impact", 68)
        self.menu_subtitle_font = pygame.font.SysFont("impact", 34)
        self.menu_art = MenuArt()

    @staticmethod
    def name_input_rect() -> pygame.Rect:
        """Возвращает копию области ввода, защищая общую разметку."""
        return NAME_INPUT_RECT.copy()

    def draw(
        self,
        state: str,
        level: Level | None,
        entities: EntityManager,
        camera: pygame.Vector2,
        menu_buttons: list[Button],
        pause_buttons: list[Button],
        player_name: str,
        name_input_active: bool,
        scores: list[ScoreEntry],
    ) -> None:
        self.screen.fill(BLACK)
        if state == PLAYING_STATE:
            self._draw_game(level, entities, camera)
        elif state == PAUSE_STATE:
            self._draw_game(level, entities, camera)
            self._draw_pause(pause_buttons)
        elif state == SCORES_STATE:
            self._draw_scores(scores)
        elif state in (GAME_OVER_STATE, VICTORY_STATE):
            self._draw_end_screen(state)
        else:
            self._draw_menu(
                menu_buttons,
                player_name,
                name_input_active,
            )
        pygame.display.flip()

    def _draw_game(
        self,
        level: Level | None,
        entities: EntityManager,
        camera: pygame.Vector2,
    ) -> None:
        if level is None or entities.player is None:
            return
        self._draw_level(level, camera)
        entities.draw(self.screen, camera)
        self._draw_hud(level, entities)
        self._draw_first_level_hint(level)

    def _draw_level(self, level: Level, camera: pygame.Vector2) -> None:
        for y_pos, row in enumerate(level.grid):
            for x_pos, tile in enumerate(row):
                rect = pygame.Rect(
                    x_pos * TILE_SIZE - camera.x,
                    y_pos * TILE_SIZE - camera.y,
                    TILE_SIZE,
                    TILE_SIZE,
                )
                if tile == "#":
                    wall_tile = self.wall_tiles.get_tile(x_pos, y_pos)
                    self.screen.blit(wall_tile, rect)
                else:
                    pygame.draw.rect(self.screen, GRAY, rect)
                pygame.draw.rect(self.screen, BLACK, rect, width=1)

    def _draw_hud(self, level: Level, entities: EntityManager) -> None:
        player = entities.player
        if player is None:
            return
        pygame.draw.rect(
            self.screen,
            BLACK,
            pygame.Rect(0, 0, SCREEN_WIDTH, HUD_HEIGHT),
        )
        self._draw_text(f"HP: {player.hp}", HUD_MARGIN, HUD_TEXT_Y, RED)
        self._draw_text(
            f"Score: {player.score}",
            HUD_SCORE_X,
            HUD_TEXT_Y,
            WHITE,
        )
        key_text = "Key: yes" if player.has_key else "Key: no"
        self._draw_text(key_text, HUD_KEY_X, HUD_TEXT_Y, ORANGE)
        buff_text = "Invulnerable" if player.is_invulnerable else ""
        self._draw_text(buff_text, HUD_BUFF_X, HUD_TEXT_Y, BLUE)
        self._draw_text(level.title, HUD_LEVEL_X, HUD_TEXT_Y, WHITE)
        self._draw_fps()

    def _draw_fps(self) -> None:
        surface = self.font.render(
            f"FPS: {self.clock.get_fps():.0f}",
            True,
            WHITE,
        )
        rect = surface.get_rect(
            top=HUD_TEXT_Y,
            right=SCREEN_WIDTH - HUD_MARGIN,
        )
        self.screen.blit(surface, rect)

    def _draw_menu(
        self,
        buttons: list[Button],
        player_name: str,
        name_input_active: bool,
    ) -> None:
        self.menu_art.draw(self.screen)
        self._draw_menu_heading()
        self._draw_name_input(player_name, name_input_active)
        for button in buttons:
            button.draw(self.screen, self.font)

    def _draw_menu_heading(self) -> None:
        title = self.menu_title_font.render(
            "PYSURVIVAL",
            True,
            MENU_TITLE_COLOR,
        )
        subtitle = self.menu_subtitle_font.render(
            "ZOMBIE WAVES",
            True,
            MENU_SUBTITLE_COLOR,
        )
        self.screen.blit(title, MENU_TITLE_POSITION)
        self.screen.blit(subtitle, MENU_SUBTITLE_POSITION)
        pygame.draw.line(
            self.screen,
            MENU_BUTTON_ACCENT_COLOR,
            MENU_RULE_START,
            MENU_RULE_END,
            width=3,
        )

    def _draw_pause(self, buttons: list[Button]) -> None:
        overlay = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA,
        )
        overlay.fill((0, 0, 0, PAUSE_OVERLAY_ALPHA))
        self.screen.blit(overlay, (0, 0))
        self._draw_center_title("Paused", 210)
        for button in buttons:
            button.draw(self.screen, self.font)

    def _draw_scores(self, scores: list[ScoreEntry]) -> None:
        self._draw_center_title("Top Scores", 120)
        if not scores:
            self._draw_text("No scores yet", 420, 230, WHITE)
        for index, entry in enumerate(scores, start=1):
            self._draw_text(
                f"{index}. {entry.player_name} - {entry.score}",
                330,
                200 + index * 42,
                WHITE,
            )
        self._draw_text("Esc - menu", 430, 620, GRAY)

    def _draw_end_screen(self, state: str) -> None:
        title = "Game Over" if state == GAME_OVER_STATE else "Run Complete"
        self._draw_center_title(title, 220)
        self._draw_text("Esc - menu", 440, 330, WHITE)

    def _draw_name_input(
        self,
        player_name: str,
        name_input_active: bool,
    ) -> None:
        rect = self.name_input_rect()
        border_color = YELLOW if name_input_active else GRAY
        pygame.draw.rect(
            self.screen,
            MENU_BUTTON_BASE_COLOR,
            rect,
            border_radius=6,
        )
        pygame.draw.rect(self.screen, border_color, rect, width=2)
        self._draw_text("Player name", rect.x, rect.y - 30, WHITE)
        self._draw_text(player_name, rect.x + 12, rect.y + 10, WHITE)

    def _draw_first_level_hint(self, level: Level) -> None:
        if level.level_id != LEVEL_ONE_ID:
            return
        hint_lines = (
            "WASD - move, Left mouse - shoot",
            "Clear all waves, pick up the key, press E near portal",
        )
        pygame.draw.rect(
            self.screen,
            BLACK,
            FIRST_LEVEL_HINT_RECT,
            border_radius=6,
        )
        pygame.draw.rect(
            self.screen,
            YELLOW,
            FIRST_LEVEL_HINT_RECT,
            width=2,
        )
        for index, line in enumerate(hint_lines):
            y_pos = FIRST_LEVEL_HINT_RECT.y + 10 + index * 28
            self._draw_text(
                line,
                FIRST_LEVEL_HINT_RECT.x + 14,
                y_pos,
                WHITE,
            )

    def _draw_center_title(self, text: str, y_pos: int) -> None:
        surface = self.large_font.render(text, True, WHITE)
        rect = surface.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
        self.screen.blit(surface, rect)

    def _draw_text(
        self,
        text: str,
        x_pos: int,
        y_pos: int,
        color: tuple[int, int, int],
    ) -> None:
        self.screen.blit(self.font.render(text, True, color), (x_pos, y_pos))
