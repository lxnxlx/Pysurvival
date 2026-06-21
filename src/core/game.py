"""Main pygame application and high-level game orchestration."""

from __future__ import annotations

import pygame

from src.core.constants import (
    BLACK,
    BLUE,
    BULLET_DAMAGE,
    ENDLESS_LEVEL_ID,
    FPS,
    GAME_OVER_STATE,
    GRAY,
    HUD_HEIGHT,
    HUD_MARGIN,
    HUD_TEXT_Y,
    LEVEL_ONE_ID,
    LEVEL_TWO_ID,
    INVULNERABILITY_ORB_DROP_CHANCE,
    MEDKIT_DROP_CHANCE,
    MEDKIT_HEAL,
    MENU_BUTTON_ACCENT_COLOR,
    MENU_BUTTON_BASE_COLOR,
    MENU_BUTTON_BORDER_COLOR,
    MENU_BUTTON_HOVER_COLOR,
    MENU_STATE,
    MENU_SUBTITLE_COLOR,
    MENU_TITLE_COLOR,
    ORANGE,
    PAUSE_STATE,
    PLAYING_STATE,
    PLAYER_DEFAULT_NAME,
    PLAYER_NAME_MAX_LENGTH,
    RED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SCORES_STATE,
    TILE_SIZE,
    VICTORY_STATE,
    WALL_TILE_ATLAS_FILE,
    WALL_TILE_COLUMNS,
    WHITE,
    YELLOW,
)
from src.core.level import Level, LevelLoader
from src.core.state_manager import StateManager
from src.entities.pickup import InvulnerabilityOrb, Key, Medkit, Portal
from src.entities.player import Player
from src.managers.entity_manager import EntityManager
from src.managers.pathfinder import Pathfinder
from src.managers.random_manager import PseudoRandom
from src.managers.save_system import SaveData, SaveSystem
from src.managers.sound_manager import SoundManager
from src.managers.wave_manager import WaveManager
from src.ui.button import Button
from src.ui.menu_art import MenuArt
from src.ui.tile_set import WallTileSet


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("PySurvival: Zombie Waves")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 24)
        self.large_font = pygame.font.SysFont("arial", 52, bold=True)
        self.menu_title_font = pygame.font.SysFont("impact", 68)
        self.menu_subtitle_font = pygame.font.SysFont("impact", 34)
        self.menu_art = MenuArt()
        self.wall_tiles = WallTileSet(
            WALL_TILE_ATLAS_FILE,
            TILE_SIZE,
            WALL_TILE_COLUMNS,
        )

        self.running = True
        self.state_manager = StateManager()
        self.level_loader = LevelLoader()
        self.save_system = SaveSystem()
        self.sound_manager = SoundManager()
        self.sound_manager.play_menu_music()
        self.entities = EntityManager()
        self.randomizer = PseudoRandom()
        self.wave_manager = WaveManager(self.randomizer)
        self.level: Level | None = None
        self.pathfinder: Pathfinder | None = None
        self.walls: list[pygame.Rect] = []
        self.camera = pygame.Vector2()
        self.player_name = PLAYER_DEFAULT_NAME
        self.name_input_active = False
        self.menu_buttons = self._build_menu_buttons()
        self.pause_buttons = self._build_pause_buttons()

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            self._handle_events()
            if self.state_manager.is_state(PLAYING_STATE):
                self._update(dt)
            self._draw()
        pygame.quit()

    def _build_menu_buttons(self) -> list[Button]:
        actions = [
            ("Start", self.start_new_game),
            ("Continue", self.continue_game),
            ("Scores", self.show_scores),
            ("Quit", self.stop),
        ]
        return [
            Button(
                pygame.Rect(70, 300 + index * 58, 270, 46),
                label,
                action,
                base_color=MENU_BUTTON_BASE_COLOR,
                hover_color=MENU_BUTTON_HOVER_COLOR,
                border_color=MENU_BUTTON_BORDER_COLOR,
                accent_color=MENU_BUTTON_ACCENT_COLOR,
            )
            for index, (label, action) in enumerate(actions)
        ]

    def _build_pause_buttons(self) -> list[Button]:
        return [
            Button(
                pygame.Rect(392, 300, 240, 48),
                "Resume",
                self.resume_game,
            ),
            Button(
                pygame.Rect(392, 360, 240, 48),
                "Save",
                self.save_current_game,
            ),
            Button(pygame.Rect(392, 420, 240, 48), "Menu", self.show_menu),
        ]

    def start_new_game(self) -> None:
        self.player_name = self._normalized_player_name()
        self.wave_manager.reset()
        self._load_level(LEVEL_ONE_ID)
        self.state_manager.set_state(PLAYING_STATE)

    def continue_game(self) -> None:
        save_data = self.save_system.load_game()
        if save_data is None:
            return
        self._load_level(save_data.level_id)
        player = self.entities.player
        if player is None:
            return
        self.player_name = save_data.player_name
        player.score = save_data.score
        player.hp = save_data.hp
        player.has_key = save_data.has_key
        if player.has_key and self.entities.portal is not None:
            self.entities.portal.unlock()
        self.state_manager.set_state(PLAYING_STATE)

    def save_current_game(self) -> None:
        if self.level is None or self.entities.player is None:
            return
        player = self.entities.player
        self.save_system.save_game(
            SaveData(
                player_name=self._normalized_player_name(),
                level_id=self.level.level_id,
                score=player.score,
                hp=player.hp,
                has_key=player.has_key,
            )
        )

    def show_scores(self) -> None:
        self.state_manager.set_state(SCORES_STATE)

    def show_menu(self) -> None:
        self.sound_manager.play_menu_music()
        self.state_manager.set_state(MENU_STATE)

    def resume_game(self) -> None:
        self.state_manager.set_state(PLAYING_STATE)

    def stop(self) -> None:
        self.running = False

    def _load_level(self, level_id: int, score: int = 0) -> None:
        self.level = self.level_loader.load(level_id)
        self.sound_manager.play_level_music(level_id)
        self.pathfinder = Pathfinder(self.level.grid)
        self.walls = [pygame.Rect(item) for item in self.level.wall_rects()]
        self.wave_manager.reset()
        self.entities.clear()
        self.entities.player = Player(
            self._tile_to_pixel(self.level.player_spawn)
        )
        self.entities.player.score = score
        self.entities.zombies = self.wave_manager.spawn_wave(self.level)

        self.entities.portal = Portal(
            self._tile_to_pixel(self.level.exit_position)
        )

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.stop()
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)

            if self.state_manager.is_state(MENU_STATE):
                self._handle_name_input(event)
                self._handle_buttons(event, self.menu_buttons)
            elif self.state_manager.is_state(PAUSE_STATE):
                self._handle_buttons(event, self.pause_buttons)

    def _handle_keydown(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_ESCAPE:
            if self.state_manager.is_state(PLAYING_STATE):
                self.state_manager.set_state(PAUSE_STATE)
            elif self.state_manager.is_state(PAUSE_STATE):
                self.resume_game()
            elif not self.state_manager.is_state(MENU_STATE):
                self.show_menu()
        if event.key == pygame.K_e:
            self._try_use_exit()

    def _handle_name_input(self, event: pygame.event.Event) -> None:
        input_rect = self._name_input_rect()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.name_input_active = input_rect.collidepoint(event.pos)
            return
        if event.type != pygame.KEYDOWN or not self.name_input_active:
            return

        if event.key == pygame.K_BACKSPACE:
            self.player_name = self.player_name[:-1]
        elif event.key == pygame.K_RETURN:
            self.name_input_active = False
        elif event.unicode and event.unicode.isprintable():
            self._append_player_name_char(event.unicode)

    def _append_player_name_char(self, char: str) -> None:
        if len(self.player_name) >= PLAYER_NAME_MAX_LENGTH:
            return
        self.player_name += char

    @staticmethod
    def _handle_buttons(
        event: pygame.event.Event,
        buttons: list[Button],
    ) -> None:
        for button in buttons:
            button.handle_event(event)

    def _update(self, dt: float) -> None:
        missing_gameplay_data = (
            self.entities.player is None
            or self.level is None
            or self.pathfinder is None
        )
        if missing_gameplay_data:
            return

        player = self.entities.player
        player.update_timers(dt)
        player.move(
            self._movement_input(),
            dt,
            self.walls,
            self._level_bounds(),
        )
        self._shoot_from_mouse()

        for bullet in self.entities.bullets:
            bullet.update(dt)
        for zombie in self.entities.zombies:
            zombie.update(dt, player.center, self.pathfinder, self.walls)

        self._handle_collisions()
        self.entities.cleanup()
        self._spawn_next_wave_if_ready()
        self._spawn_key_if_level_clear()
        self._update_camera()

    def _movement_input(self) -> pygame.Vector2:
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2()
        direction.x = keys[pygame.K_d] - keys[pygame.K_a]
        direction.y = keys[pygame.K_s] - keys[pygame.K_w]
        return direction

    def _shoot_from_mouse(self) -> None:
        player = self.entities.player
        if player is None:
            return
        target = pygame.Vector2(pygame.mouse.get_pos()) + self.camera
        player.aim_at(target)
        if not pygame.mouse.get_pressed(num_buttons=3)[0]:
            return
        bullet = player.try_shoot(target)
        if bullet is not None:
            self.entities.bullets.append(bullet)
            self.sound_manager.play_shot()

    def _handle_collisions(self) -> None:
        player = self.entities.player
        if player is None:
            return
        self._handle_bullet_hits(player)
        self._handle_zombie_attacks(player)
        self._handle_pickups(player)

        if player.hp <= 0:
            self._finish_run(GAME_OVER_STATE)

    def _handle_bullet_hits(self, player: Player) -> None:
        for bullet in self.entities.bullets:
            if any(bullet.rect.colliderect(wall) for wall in self.walls):
                bullet.alive = False
                continue
            for zombie in self.entities.zombies:
                bullet_hit_zombie = (
                    bullet.alive
                    and zombie.alive
                    and bullet.rect.colliderect(zombie.rect)
                )
                if bullet_hit_zombie:
                    bullet.alive = False
                    zombie.take_damage(BULLET_DAMAGE)
                    if not zombie.alive:
                        player.score += zombie.score_value
                        self.wave_manager.register_kill(zombie.wave_number)
                        self.sound_manager.play_monster_death()
                        self._try_drop_loot(zombie.center)

    def _handle_zombie_attacks(self, player: Player) -> None:
        for zombie in self.entities.zombies:
            if zombie.rect.colliderect(player.rect) and zombie.can_attack():
                player.take_damage(zombie.damage())
                zombie.reset_attack()

    def _handle_pickups(self, player: Player) -> None:
        key = self.entities.key
        if key is not None and key.rect.colliderect(player.rect):
            key.alive = False
            player.has_key = True
            if self.entities.portal is not None:
                self.entities.portal.unlock()
            self.sound_manager.play_key_pickup()
        for medkit in self.entities.medkits:
            if medkit.rect.colliderect(player.rect):
                medkit.alive = False
                player.heal(MEDKIT_HEAL)
                self.sound_manager.play_health_pickup()
        for orb in self.entities.invulnerability_orbs:
            if orb.rect.colliderect(player.rect):
                orb.alive = False
                player.activate_invulnerability()
                self.sound_manager.play_buff_pickup()

    def _try_drop_loot(self, center: pygame.Vector2) -> None:
        if self.randomizer.chance(MEDKIT_DROP_CHANCE):
            self.entities.medkits.append(self._build_pickup(Medkit, center))
        if self.randomizer.chance(INVULNERABILITY_ORB_DROP_CHANCE):
            self.entities.invulnerability_orbs.append(
                self._build_pickup(InvulnerabilityOrb, center)
            )

    @staticmethod
    def _build_pickup(
        pickup_type: type[Medkit] | type[InvulnerabilityOrb],
        center: pygame.Vector2,
    ) -> Medkit | InvulnerabilityOrb:
        pickup = pickup_type(pygame.Vector2(center))
        pickup.position.x -= pickup.size / 2
        pickup.position.y -= pickup.size / 2
        return pickup

    def _try_use_exit(self) -> None:
        player = self.entities.player
        portal = self.entities.portal
        if player is None or portal is None or self.level is None:
            return
        if not player.rect.colliderect(portal.rect.inflate(18, 18)):
            return
        if self.level.level_id < ENDLESS_LEVEL_ID and not player.has_key:
            return

        if self.level.level_id == LEVEL_ONE_ID:
            self._complete_level(LEVEL_TWO_ID)
        elif self.level.level_id == LEVEL_TWO_ID:
            self._complete_level(ENDLESS_LEVEL_ID)
        else:
            self._finish_run(VICTORY_STATE)

    def _complete_level(self, next_level_id: int) -> None:
        player = self.entities.player
        if player is None:
            return
        score = player.score
        self._load_level(next_level_id, score)
        # Save after transition so Continue starts at the new checkpoint.
        self.save_current_game()

    def _spawn_next_wave_if_ready(self) -> None:
        if self.level is None:
            return
        if self.wave_manager.should_spawn_next_wave(self.level):
            self.entities.zombies.extend(
                self.wave_manager.spawn_wave(self.level)
            )

    def _spawn_key_if_level_clear(self) -> None:
        if self.level is None or self.entities.player is None:
            return
        key_can_spawn = (
            self.level.key_position is not None
            and self.entities.key is None
            and not self.entities.player.has_key
            and not self.entities.zombies
            and self.wave_manager.has_spawned_all_waves(self.level)
        )
        if key_can_spawn:
            self.entities.key = Key(
                self._tile_to_pixel(self.level.key_position)
            )

    def _finish_run(self, state: str) -> None:
        if self.entities.player is not None:
            self.save_system.add_score(
                self._normalized_player_name(),
                self.entities.player.score,
            )
        self.save_system.clear_save()
        self.state_manager.set_state(state)

    def _draw(self) -> None:
        self.screen.fill(BLACK)
        state = self.state_manager.state
        if state == PLAYING_STATE:
            self._draw_game()
        elif state == PAUSE_STATE:
            self._draw_game()
            self._draw_pause()
        elif state == SCORES_STATE:
            self._draw_scores()
        elif state in (GAME_OVER_STATE, VICTORY_STATE):
            self._draw_end_screen(state)
        else:
            self._draw_menu()
        pygame.display.flip()

    def _draw_game(self) -> None:
        if self.level is None or self.entities.player is None:
            return
        self._draw_level()
        self.entities.draw(self.screen, self.camera)
        self._draw_hud()
        self._draw_first_level_hint()

    def _draw_level(self) -> None:
        if self.level is None:
            return
        for y_pos, row in enumerate(self.level.grid):
            for x_pos, tile in enumerate(row):
                rect = pygame.Rect(
                    x_pos * TILE_SIZE - self.camera.x,
                    y_pos * TILE_SIZE - self.camera.y,
                    TILE_SIZE,
                    TILE_SIZE,
                )
                if tile == "#":
                    wall_tile = self.wall_tiles.get_tile(x_pos, y_pos)
                    self.screen.blit(wall_tile, rect)
                else:
                    pygame.draw.rect(self.screen, GRAY, rect)
                pygame.draw.rect(self.screen, BLACK, rect, width=1)

    def _draw_hud(self) -> None:
        player = self.entities.player
        if player is None or self.level is None:
            return
        hud_rect = pygame.Rect(0, 0, SCREEN_WIDTH, HUD_HEIGHT)
        pygame.draw.rect(self.screen, BLACK, hud_rect)
        hp_text = f"HP: {player.hp}"
        score_text = f"Score: {player.score}"
        level_text = f"{self.level.title}"
        key_text = "Key: yes" if player.has_key else "Key: no"
        buff_text = "Invulnerable" if player.is_invulnerable else ""
        self._draw_text(hp_text, HUD_MARGIN, HUD_TEXT_Y, RED)
        self._draw_text(score_text, 130, HUD_TEXT_Y, WHITE)
        self._draw_text(key_text, 310, HUD_TEXT_Y, ORANGE)
        self._draw_text(buff_text, 450, HUD_TEXT_Y, BLUE)
        self._draw_text(level_text, 650, HUD_TEXT_Y, WHITE)
        self._draw_fps()

    def _draw_fps(self) -> None:
        fps_text = f"FPS: {self.clock.get_fps():.0f}"
        surface = self.font.render(fps_text, True, WHITE)
        rect = surface.get_rect(
            top=HUD_TEXT_Y,
            right=SCREEN_WIDTH - HUD_MARGIN,
        )
        self.screen.blit(surface, rect)

    def _draw_menu(self) -> None:
        self.menu_art.draw(self.screen)
        self._draw_menu_heading()
        self._draw_name_input()
        for button in self.menu_buttons:
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
        self.screen.blit(title, (55, 42))
        self.screen.blit(subtitle, (78, 116))
        pygame.draw.line(
            self.screen,
            MENU_BUTTON_ACCENT_COLOR,
            (70, 164),
            (338, 164),
            width=3,
        )

    def _draw_pause(self) -> None:
        overlay = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA,
        )
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        self._draw_center_title("Paused", 210)
        for button in self.pause_buttons:
            button.draw(self.screen, self.font)

    def _draw_scores(self) -> None:
        self._draw_center_title("Top Scores", 120)
        scores = self.save_system.load_scores()
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

    def _draw_name_input(self) -> None:
        rect = self._name_input_rect()
        border_color = YELLOW if self.name_input_active else GRAY
        pygame.draw.rect(
            self.screen,
            MENU_BUTTON_BASE_COLOR,
            rect,
            border_radius=6,
        )
        pygame.draw.rect(self.screen, border_color, rect, width=2)
        self._draw_text("Player name", rect.x, rect.y - 30, WHITE)
        self._draw_text(self.player_name, rect.x + 12, rect.y + 10, WHITE)

    def _draw_first_level_hint(self) -> None:
        if self.level is None or self.level.level_id != LEVEL_ONE_ID:
            return
        hint_lines = [
            "WASD - move, Left mouse - shoot",
            "Clear all waves, pick up the key, press E near portal",
        ]
        panel = pygame.Rect(18, HUD_HEIGHT + 12, 520, 76)
        pygame.draw.rect(self.screen, BLACK, panel, border_radius=6)
        pygame.draw.rect(self.screen, YELLOW, panel, width=2)
        for index, line in enumerate(hint_lines):
            y_pos = panel.y + 10 + index * 28
            self._draw_text(line, panel.x + 14, y_pos, WHITE)

    @staticmethod
    def _name_input_rect() -> pygame.Rect:
        return pygame.Rect(70, 224, 270, 44)

    def _normalized_player_name(self) -> str:
        name = self.player_name.strip()
        return name or PLAYER_DEFAULT_NAME

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

    def _update_camera(self) -> None:
        player = self.entities.player
        if player is None or self.level is None:
            return
        level_width, level_height = self.level.pixel_size
        self.camera.x = max(
            0,
            min(
                player.center.x - SCREEN_WIDTH / 2,
                level_width - SCREEN_WIDTH,
            ),
        )
        self.camera.y = max(
            0,
            min(
                player.center.y - SCREEN_HEIGHT / 2,
                level_height - SCREEN_HEIGHT,
            ),
        )

    def _level_bounds(self) -> pygame.Rect:
        if self.level is None:
            return pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        width, height = self.level.pixel_size
        return pygame.Rect(0, HUD_HEIGHT, width, height - HUD_HEIGHT)

    @staticmethod
    def _tile_to_pixel(tile: tuple[int, int]) -> pygame.Vector2:
        return pygame.Vector2(tile[0] * TILE_SIZE, tile[1] * TILE_SIZE)
