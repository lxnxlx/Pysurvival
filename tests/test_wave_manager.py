import pygame

from src.core.constants import (
    BLUE,
    BLUE_ZOMBIE_HP_MULTIPLIER,
    BLUE_ZOMBIE_SCORE,
    ENDLESS_FIRST_WAVE_SIZE,
    LEVEL_ONE_WAVES,
    NORMAL_ZOMBIE_SCORE,
    RED_ZOMBIE_SCORE,
    ZOMBIE_HP,
)
from src.core.level import Level
from src.managers.wave_manager import WaveManager


class PredictableRandom:
    def randint(self, min_value, max_value):
        return 0

    def weighted_choice(self, weighted_items):
        return weighted_items[0][0]


class RedZombieRandom(PredictableRandom):
    def weighted_choice(self, weighted_items):
        return weighted_items[1][0]


class MinimumJitterRandom(PredictableRandom):
    def randint(self, min_value, max_value):
        return min_value


def build_level(level_id):
    return Level(
        level_id=level_id,
        title="test",
        grid=["...", "...", "..."],
        player_spawn=(1, 1),
        zombie_spawns=[(1, 1)],
        key_position=None,
        exit_position=(2, 2),
    )


def test_level_one_uses_configured_wave_sizes():
    manager = WaveManager(PredictableRandom())
    level = build_level(1)

    first_wave = manager.spawn_wave(level)

    assert len(first_wave) == LEVEL_ONE_WAVES[0]
    assert first_wave[0].score_value == NORMAL_ZOMBIE_SCORE


def test_wave_manager_spawns_next_after_thirty_percent_kills():
    manager = WaveManager(PredictableRandom())
    level = build_level(1)
    manager.spawn_wave(level)

    manager.register_kill(1)
    manager.register_kill(1)

    assert not manager.should_spawn_next_wave(level)

    manager.register_kill(1)

    assert manager.should_spawn_next_wave(level)


def test_wave_manager_ignores_kills_from_previous_wave():
    manager = WaveManager(PredictableRandom())
    level = build_level(1)
    manager.spawn_wave(level)

    for _ in range(3):
        manager.register_kill(1)
    manager.spawn_wave(level)

    for _ in range(5):
        manager.register_kill(1)

    assert not manager.should_spawn_next_wave(level)


def test_wave_manager_knows_when_finite_level_waves_are_spawned():
    manager = WaveManager(PredictableRandom())
    level = build_level(1)

    for _ in LEVEL_ONE_WAVES:
        manager.spawn_wave(level)

    assert manager.has_spawned_all_waves(level)


def test_endless_first_wave_has_blue_tank_zombies_when_roll_matches():
    manager = WaveManager(PredictableRandom())
    level = build_level(3)

    wave = manager.spawn_wave(level)

    assert len(wave) == ENDLESS_FIRST_WAVE_SIZE
    assert wave[0].color == BLUE
    assert wave[0].hp == ZOMBIE_HP * BLUE_ZOMBIE_HP_MULTIPLIER
    assert wave[0].score_value == BLUE_ZOMBIE_SCORE


def test_red_zombie_has_its_own_score_value():
    manager = WaveManager(RedZombieRandom())
    level = build_level(3)

    wave = manager.spawn_wave(level)

    assert wave[0].score_value == RED_ZOMBIE_SCORE


def test_spawned_zombies_do_not_overlap_walls():
    manager = WaveManager(MinimumJitterRandom())
    level = Level(
        level_id=1,
        title="spawn test",
        grid=["###", "#.#", "###"],
        player_spawn=(1, 1),
        zombie_spawns=[(1, 1)],
        key_position=None,
        exit_position=(1, 1),
    )
    walls = [pygame.Rect(item) for item in level.wall_rects()]

    zombies = manager.spawn_wave(level)

    assert not any(
        zombie.rect.colliderect(wall)
        for zombie in zombies
        for wall in walls
    )
