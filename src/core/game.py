"""Главное приложение pygame и управление игровыми подсистемами."""

from __future__ import annotations

from collections.abc import Iterator

import pygame

from src.core.constants import (
    BULLET_DAMAGE,
    ENDLESS_LEVEL_ID,
    FPS,
    GAME_OVER_STATE,
    HUD_HEIGHT,
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
    PAUSE_STATE,
    PLAYING_STATE,
    PLAYER_DEFAULT_NAME,
    PLAYER_NAME_MAX_LENGTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SAVE_VERSION,
    SCORES_STATE,
    TILE_SIZE,
    WALL_TILE_ATLAS_FILE,
    WALL_TILE_COLUMNS,
    VICTORY_STATE,
    ZOMBIE_SIZE,
    ZOMBIE_SEPARATION_MAX_PASSES,
)
from src.core.level import Level, LevelLoader
from src.core.state_manager import StateManager
from src.entities.pickup import InvulnerabilityOrb, Key, Medkit, Portal
from src.entities.player import Player
from src.entities.zombie import Zombie
from src.managers.collision_manager import CollisionManager
from src.managers.entity_manager import EntityManager
from src.managers.pathfinder import Pathfinder
from src.managers.random_manager import PseudoRandom
from src.managers.save_system import (
    PickupSaveData,
    SaveData,
    SaveSystem,
    ZombieSaveData,
)
from src.managers.sound_manager import SoundManager
from src.managers.wave_manager import WaveManager
from src.ui.button import Button
from src.ui.game_view import GameView
from src.ui.tile_set import WallTileSet


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("PySurvival: Zombie Waves")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.wall_tiles = WallTileSet(
            WALL_TILE_ATLAS_FILE,
            TILE_SIZE,
            WALL_TILE_COLUMNS,
        )
        self.view = GameView(self.screen, self.clock, self.wall_tiles)

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
        self.save_system.clear_save()
        self.wave_manager.reset()
        self._load_level(LEVEL_ONE_ID)
        self.state_manager.set_state(PLAYING_STATE)

    def continue_game(self) -> None:
        save_data = self.save_system.load_game()
        if save_data is None:
            return
        if save_data.version < SAVE_VERSION:
            self._load_legacy_save(save_data)
        else:
            self._restore_game(save_data)
        self.state_manager.set_state(PLAYING_STATE)

    def _load_legacy_save(self, save_data: SaveData) -> None:
        self._load_level(
            save_data.level_id,
            score=save_data.score,
            hp=save_data.hp,
        )
        player = self.entities.player
        if player is None:
            return
        self.player_name = save_data.player_name
        player.has_key = save_data.has_key
        if player.has_key and self.entities.portal is not None:
            self.entities.portal.unlock()

    def _restore_game(self, save_data: SaveData) -> None:
        self._load_level(
            save_data.level_id,
            score=save_data.score,
            hp=save_data.hp,
            spawn_wave=False,
        )
        player = self.entities.player
        if player is None:
            return
        self.player_name = save_data.player_name
        if save_data.player_x is not None and save_data.player_y is not None:
            player.position.update(save_data.player_x, save_data.player_y)
        player.has_key = save_data.has_key
        self.wave_manager.restore(
            save_data.wave_number,
            save_data.kills_after_last_spawn,
            save_data.last_wave_size,
        )
        self.entities.zombies = [
            self._restore_zombie(item) for item in save_data.zombies
        ]
        self.entities.medkits = [
            Medkit(pygame.Vector2(item.x_pos, item.y_pos))
            for item in save_data.medkits
        ]
        self.entities.invulnerability_orbs = [
            InvulnerabilityOrb(pygame.Vector2(item.x_pos, item.y_pos))
            for item in save_data.invulnerability_orbs
        ]
        if (
            save_data.key_spawned
            and not player.has_key
            and self.level is not None
            and self.level.key_position is not None
        ):
            self.entities.key = Key(
                self._tile_to_pixel(self.level.key_position)
            )
        if player.has_key and self.entities.portal is not None:
            self.entities.portal.unlock()
        self._spawn_key_if_level_clear()

    def _restore_zombie(self, data: ZombieSaveData) -> Zombie:
        zombie = self.wave_manager.create_zombie(
            pygame.Vector2(data.x_pos, data.y_pos),
            data.wave_number,
            data.kind,
        )
        zombie.hp = data.hp
        return zombie

    def save_current_game(self) -> None:
        if self.level is None or self.entities.player is None:
            return
        player = self.entities.player
        wave_number, kills, last_wave_size = self.wave_manager.snapshot()
        self.save_system.save_game(
            SaveData(
                player_name=self._normalized_player_name(),
                level_id=self.level.level_id,
                score=player.score,
                hp=player.hp,
                has_key=player.has_key,
                player_x=float(player.position.x),
                player_y=float(player.position.y),
                wave_number=wave_number,
                kills_after_last_spawn=kills,
                last_wave_size=last_wave_size,
                zombies=[
                    ZombieSaveData(
                        x_pos=float(zombie.position.x),
                        y_pos=float(zombie.position.y),
                        hp=zombie.hp,
                        wave_number=zombie.wave_number,
                        kind=zombie.kind,
                    )
                    for zombie in self.entities.zombies
                    if zombie.alive
                ],
                key_spawned=self.entities.key is not None,
                medkits=[
                    PickupSaveData(
                        x_pos=float(medkit.position.x),
                        y_pos=float(medkit.position.y),
                    )
                    for medkit in self.entities.medkits
                    if medkit.alive
                ],
                invulnerability_orbs=[
                    PickupSaveData(
                        x_pos=float(orb.position.x),
                        y_pos=float(orb.position.y),
                    )
                    for orb in self.entities.invulnerability_orbs
                    if orb.alive
                ],
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

    def _load_level(
        self,
        level_id: int,
        score: int = 0,
        hp: int | None = None,
        spawn_wave: bool = True,
    ) -> None:
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
        if hp is not None:
            self.entities.player.hp = hp
        if spawn_wave:
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
        if (
            event.key == pygame.K_e
            and self.state_manager.is_state(PLAYING_STATE)
        ):
            self._try_use_exit()

    def _handle_name_input(self, event: pygame.event.Event) -> None:
        input_rect = self.view.name_input_rect()
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
        self._separate_zombies()

        self._handle_collisions()
        self.entities.cleanup()
        self._spawn_next_wave_if_ready()
        self._spawn_key_if_level_clear()
        self._update_camera()

    def _separate_zombies(self) -> None:
        """Устраняет пересечения врагов ограниченным итеративным решателем.

        Фиксированный лимит проходов предотвращает просадки FPS на больших
        бесконечных волнах. Каждый проход использует пространственную сетку.

        Returns:
            Ничего.
        """
        zombies = self.entities.zombies
        for _ in range(ZOMBIE_SEPARATION_MAX_PASSES):
            had_overlap = False
            for zombie, other in self._nearby_zombie_pairs():
                if CollisionManager.separate(zombie, other):
                    had_overlap = True
                    zombie.resolve_walls(self.walls)
                    other.resolve_walls(self.walls)
            if not had_overlap:
                break

    def _nearby_zombie_pairs(self) -> Iterator[tuple[Zombie, Zombie]]:
        """Создает пары для проверки столкновений с помощью сетки.

        Враги распределяются по ячейкам размером с их хитбокс. Пересекающийся
        квадрат может находиться только в текущей или восьми соседних ячейках.

        Returns:
            Уникальные пары соседних врагов для точной проверки AABB.
        """
        zombies = self.entities.zombies
        buckets: dict[tuple[int, int], list[int]] = {}
        for index, zombie in enumerate(zombies):
            cell = (
                int(zombie.center.x // ZOMBIE_SIZE),
                int(zombie.center.y // ZOMBIE_SIZE),
            )
            buckets.setdefault(cell, []).append(index)

        for index, zombie in enumerate(zombies):
            cell_x = int(zombie.center.x // ZOMBIE_SIZE)
            cell_y = int(zombie.center.y // ZOMBIE_SIZE)
            for offset_y in (-1, 0, 1):
                for offset_x in (-1, 0, 1):
                    nearby = buckets.get(
                        (cell_x + offset_x, cell_y + offset_y),
                        (),
                    )
                    for other_index in nearby:
                        if other_index > index:
                            yield zombie, zombies[other_index]

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
            if any(
                CollisionManager.intersects(bullet.rect, wall)
                for wall in self.walls
            ):
                bullet.alive = False
                continue
            for zombie in self.entities.zombies:
                bullet_hit_zombie = (
                    bullet.alive
                    and zombie.alive
                    and CollisionManager.intersects(
                        bullet.rect,
                        zombie.rect,
                    )
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
            zombie_touches_player = CollisionManager.intersects(
                zombie.rect,
                player.rect,
            )
            if zombie_touches_player and zombie.can_attack():
                player.take_damage(zombie.damage())
                zombie.reset_attack()

    def _handle_pickups(self, player: Player) -> None:
        key = self.entities.key
        if (
            key is not None
            and CollisionManager.intersects(key.rect, player.rect)
        ):
            key.alive = False
            player.has_key = True
            if self.entities.portal is not None:
                self.entities.portal.unlock()
            self.sound_manager.play_key_pickup()
        for medkit in self.entities.medkits:
            if CollisionManager.intersects(medkit.rect, player.rect):
                medkit.alive = False
                player.heal(MEDKIT_HEAL)
                self.sound_manager.play_health_pickup()
        for orb in self.entities.invulnerability_orbs:
            if CollisionManager.intersects(orb.rect, player.rect):
                orb.alive = False
                player.activate_invulnerability()
                self.sound_manager.play_buff_pickup()

    def _try_drop_loot(self, center: pygame.Vector2) -> None:
        """Проверяет независимые псевдослучайные шансы выпадения предметов.

        Args:
            center: Положение центра побежденного врага в мире.

        Returns:
            Ничего.
        """
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
        portal_trigger = portal.rect.inflate(18, 18)
        if not CollisionManager.intersects(player.rect, portal_trigger):
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
        hp = player.hp
        self._load_level(next_level_id, score, hp)
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
        state = self.state_manager.state
        scores = (
            self.save_system.load_scores()
            if state == SCORES_STATE
            else []
        )
        self.view.draw(
            state,
            self.level,
            self.entities,
            self.camera,
            self.menu_buttons,
            self.pause_buttons,
            self.player_name,
            self.name_input_active,
            scores,
        )

    def _normalized_player_name(self) -> str:
        name = self.player_name.strip()
        return name or PLAYER_DEFAULT_NAME

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
