import pygame

from src.core.constants import PLAYER_AMMO, PLAYER_MAX_HP
from src.entities.player import Player


def test_player_infinite_ammo_does_not_spend_bullets():
    player = Player(pygame.Vector2(0, 0))

    bullet = player.try_shoot(pygame.Vector2(100, 0))

    assert bullet is not None
    assert player.ammo == PLAYER_AMMO


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
