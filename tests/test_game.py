import os

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from src.core.constants import LEVEL_ONE_ID, LEVEL_TWO_ID, PAUSE_STATE
from src.core.game import Game
from src.managers.save_system import SaveData, SaveSystem


@pytest.fixture
def game(tmp_path):
    instance = Game()
    instance.save_system = SaveSystem(
        save_file=tmp_path / "save.json",
        scores_file=tmp_path / "scores.json",
    )
    yield instance
    pygame.quit()


def test_continue_restores_active_wave_and_entities(game):
    game.start_new_game()
    for _ in range(3):
        game.wave_manager.register_kill(1)
    game._spawn_next_wave_if_ready()
    player = game.entities.player
    assert player is not None
    player.position.update(150, 200)
    player.hp = 43
    player.score = 270
    game.entities.zombies[0].hp = 12
    expected_wave_state = game.wave_manager.snapshot()
    expected_zombie_count = len(game.entities.zombies)

    game.save_current_game()
    game.continue_game()

    restored_player = game.entities.player
    assert restored_player is not None
    assert restored_player.position == pygame.Vector2(150, 200)
    assert restored_player.hp == 43
    assert restored_player.score == 270
    assert game.wave_manager.snapshot() == expected_wave_state
    assert len(game.entities.zombies) == expected_zombie_count
    assert game.entities.zombies[0].hp == 12


def test_exit_key_is_ignored_while_paused(game):
    game.start_new_game()
    player = game.entities.player
    portal = game.entities.portal
    assert player is not None
    assert portal is not None
    player.position.update(portal.position)
    player.has_key = True
    game.state_manager.set_state(PAUSE_STATE)
    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)

    game._handle_keydown(event)

    assert game.level is not None
    assert game.level.level_id == LEVEL_ONE_ID


def test_start_new_game_clears_previous_save(game):
    game.save_system.save_game(
        SaveData(
            player_name="Old",
            level_id=LEVEL_TWO_ID,
            score=500,
            hp=10,
            has_key=True,
        )
    )

    game.start_new_game()

    assert not game.save_system.has_save()


def test_level_transition_preserves_hp_and_score(game):
    game.start_new_game()
    player = game.entities.player
    assert player is not None
    player.hp = 43
    player.score = 270

    game._complete_level(LEVEL_TWO_ID)

    next_player = game.entities.player
    assert next_player is not None
    assert next_player.hp == 43
    assert next_player.score == 270


def test_dense_zombie_group_is_separated(game):
    game.start_new_game()
    for zombie in game.entities.zombies:
        zombie.position.update(300, 300)

    game._separate_zombies()

    zombies = game.entities.zombies
    assert not any(
        left.rect.colliderect(right.rect)
        for index, left in enumerate(zombies)
        for right in zombies[index + 1:]
    )
