"""Zombie wave spawning rules."""

from __future__ import annotations

import math

import pygame

from src.core.constants import (
    BLUE,
    BLUE_ENEMY_SPRITE_FILE,
    BLUE_ZOMBIE_HP_MULTIPLIER,
    BLUE_ZOMBIE_SCORE,
    BLUE_ZOMBIE_SPAWN_CHANCE,
    ENDLESS_FIRST_WAVE_SIZE,
    ENDLESS_LEVEL_ID,
    ENDLESS_WAVE_INCREMENT,
    GREEN,
    LEVEL_ONE_ID,
    LEVEL_ONE_WAVES,
    LEVEL_TWO_ID,
    LEVEL_TWO_WAVES,
    RED,
    RED_ENEMY_SPRITE_FILE,
    RED_ZOMBIE_HP_MULTIPLIER,
    RED_ZOMBIE_SCORE,
    RED_ZOMBIE_SPAWN_CHANCE,
    TILE_SIZE,
    WAVE_MIN_NEXT_TRIGGER_KILLS,
    WAVE_NEXT_TRIGGER_RATIO,
)
from src.core.level import Level
from src.entities.zombie import Zombie
from src.managers.random_manager import PseudoRandom

NORMAL_ZOMBIE_KIND = "normal"
RED_ZOMBIE_KIND = "red"
BLUE_ZOMBIE_KIND = "blue"
SPAWN_JITTER = 8


class WaveManager:
    def __init__(self, randomizer: PseudoRandom | None = None) -> None:
        self._randomizer = randomizer or PseudoRandom()
        self.wave_number = 0
        self._kills_after_last_spawn = 0
        self._last_wave_size = 0

    def reset(self) -> None:
        self.wave_number = 0
        self._kills_after_last_spawn = 0
        self._last_wave_size = 0

    def spawn_wave(self, level: Level) -> list[Zombie]:
        amount = self._next_wave_size(level)
        if amount == 0:
            return []

        self.wave_number += 1
        self._last_wave_size = amount
        self._kills_after_last_spawn = 0
        zombies = []
        for index in range(amount):
            zombies.append(self._spawn_zombie(level, index, self.wave_number))
        return zombies

    def register_kill(self, wave_number: int) -> None:
        if wave_number != self.wave_number:
            return
        self._kills_after_last_spawn += 1

    def should_spawn_next_wave(self, level: Level) -> bool:
        if not self._has_next_wave(level) or self._last_wave_size == 0:
            return False
        return self._kills_after_last_spawn >= self._next_wave_threshold()

    def has_spawned_all_waves(self, level: Level) -> bool:
        if level.level_id == ENDLESS_LEVEL_ID:
            return False
        return self.wave_number >= len(self._level_waves(level.level_id))

    def _next_wave_size(self, level: Level) -> int:
        if level.level_id == ENDLESS_LEVEL_ID:
            return ENDLESS_FIRST_WAVE_SIZE + (
                self.wave_number * ENDLESS_WAVE_INCREMENT
            )

        waves = self._level_waves(level.level_id)
        if self.wave_number >= len(waves):
            return 0
        return waves[self.wave_number]

    def _has_next_wave(self, level: Level) -> bool:
        if level.level_id == ENDLESS_LEVEL_ID:
            return True
        return self.wave_number < len(self._level_waves(level.level_id))

    def _next_wave_threshold(self) -> int:
        threshold = self._last_wave_size * WAVE_NEXT_TRIGGER_RATIO
        return max(WAVE_MIN_NEXT_TRIGGER_KILLS, math.ceil(threshold))

    def _spawn_zombie(
        self,
        level: Level,
        index: int,
        wave_number: int,
    ) -> Zombie:
        tile = level.zombie_spawns[index % len(level.zombie_spawns)]
        jitter_x = self._randomizer.randint(-SPAWN_JITTER, SPAWN_JITTER)
        jitter_y = self._randomizer.randint(-SPAWN_JITTER, SPAWN_JITTER)
        position = pygame.Vector2(
            tile[0] * TILE_SIZE + jitter_x,
            tile[1] * TILE_SIZE + jitter_y,
        )
        return self._build_zombie(position, level.level_id, wave_number)

    def _build_zombie(
        self,
        position: pygame.Vector2,
        level_id: int,
        wave_number: int,
    ) -> Zombie:
        if level_id != ENDLESS_LEVEL_ID:
            return Zombie(position, wave_number=wave_number)

        kind = self._randomizer.weighted_choice(
            (
                (BLUE_ZOMBIE_KIND, BLUE_ZOMBIE_SPAWN_CHANCE),
                (RED_ZOMBIE_KIND, RED_ZOMBIE_SPAWN_CHANCE),
                (
                    NORMAL_ZOMBIE_KIND,
                    1.0 - BLUE_ZOMBIE_SPAWN_CHANCE
                    - RED_ZOMBIE_SPAWN_CHANCE,
                ),
            )
        )
        if kind == BLUE_ZOMBIE_KIND:
            return Zombie(
                position,
                color=BLUE,
                hp_multiplier=BLUE_ZOMBIE_HP_MULTIPLIER,
                wave_number=wave_number,
                score_value=BLUE_ZOMBIE_SCORE,
                sprite_file=BLUE_ENEMY_SPRITE_FILE,
            )
        if kind == RED_ZOMBIE_KIND:
            return Zombie(
                position,
                color=RED,
                hp_multiplier=RED_ZOMBIE_HP_MULTIPLIER,
                wave_number=wave_number,
                score_value=RED_ZOMBIE_SCORE,
                sprite_file=RED_ENEMY_SPRITE_FILE,
            )
        return Zombie(position, GREEN, wave_number=wave_number)

    @staticmethod
    def _level_waves(level_id: int) -> tuple[int, ...]:
        if level_id == LEVEL_ONE_ID:
            return LEVEL_ONE_WAVES
        if level_id == LEVEL_TWO_ID:
            return LEVEL_TWO_WAVES
        return ()
