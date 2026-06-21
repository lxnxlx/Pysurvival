import pygame

from src.core.constants import PLAYER_MAX_HP
from src.entities.player import Player


def test_player_can_shoot_without_ammunition_state():
    player = Player(pygame.Vector2(0, 0))

    bullet = player.try_shoot(pygame.Vector2(100, 0))

    assert bullet is not None


def test_player_turns_toward_aim_target():
    player = Player(pygame.Vector2(0, 0))

    player.aim_at(player.center + pygame.Vector2(100, 0))

    assert player.facing_angle == -90


def test_player_heal_does_not_exceed_max_hp():
    player = Player(pygame.Vector2(0, 0))
    player.hp = PLAYER_MAX_HP - 5

    player.heal(25)

    assert player.hp == PLAYER_MAX_HP


def test_invulnerable_player_ignores_damage():
    player = Player(pygame.Vector2(0, 0))
    player.activate_invulnerability()

    player.take_damage(50)

    assert player.hp == PLAYER_MAX_HP


def test_player_has_short_protection_after_taking_damage():
    player = Player(pygame.Vector2(0, 0))

    player.take_damage(10)
    player.take_damage(10)

    assert player.hp == PLAYER_MAX_HP - 10

    player.update_timers(0.5)
    player.take_damage(10)

    assert player.hp == PLAYER_MAX_HP - 20
