"""Правила создания и переключения волн противников."""

from __future__ import annotations

import math

import pygame

from src.core.constants import (
    BLUE,
    BLUE_ENEMY_SPRITE_FILE,
    BLUE_ZOMBIE_KIND,
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
    NORMAL_ZOMBIE_KIND,
    RED,
    RED_ENEMY_SPRITE_FILE,
    RED_ZOMBIE_KIND,
    RED_ZOMBIE_HP_MULTIPLIER,
    RED_ZOMBIE_SCORE,
    RED_ZOMBIE_SPAWN_CHANCE,
    TILE_SIZE,
    WAVE_MIN_NEXT_TRIGGER_KILLS,
    WAVE_NEXT_TRIGGER_RATIO,
    ZOMBIE_SIZE,
)
from src.core.level import Level
from src.entities.zombie import Zombie
from src.managers.random_manager import PseudoRandom

SPAWN_JITTER = 6


class WaveManager:
    def __init__(self, randomizer: PseudoRandom | None = None) -> None:
        """Инициализирует прогресс волн с передаваемым генератором случайности.

        Args:
            randomizer: Общий генератор псевдослучайных игровых событий.

        Returns:
            Ничего.
        """
        self._randomizer = randomizer or PseudoRandom()
        self.wave_number = 0
        self._kills_after_last_spawn = 0
        self._last_wave_size = 0

    def reset(self) -> None:
        """Сбрасывает счетчики волн для нового уровня.

        Returns:
            Ничего.
        """
        self.wave_number = 0
        self._kills_after_last_spawn = 0
        self._last_wave_size = 0

    def restore(
        self,
        wave_number: int,
        kills_after_last_spawn: int,
        last_wave_size: int,
    ) -> None:
        """Восстанавливает проверенные счетчики волн из сохранения.

        Args:
            wave_number: Номер последней созданной волны.
            kills_after_last_spawn: Убийства текущей волны для расчета порога.
            last_wave_size: Количество противников в последней волне.

        Returns:
            Ничего.
        """
        self.wave_number = max(0, wave_number)
        self._kills_after_last_spawn = max(0, kills_after_last_spawn)
        self._last_wave_size = max(0, last_wave_size)

    def snapshot(self) -> tuple[int, int, int]:
        """Возвращает состояние волн, необходимое для продолжения игры.

        Returns:
            Номер волны, убийства текущей волны и размер последней волны.
        """
        return (
            self.wave_number,
            self._kills_after_last_spawn,
            self._last_wave_size,
        )

    def spawn_wave(self, level: Level) -> list[Zombie]:
        """Создает следующую волну и сбрасывает ее счетчик убийств.

        Args:
            level: Активный уровень с правилами волн и точками появления.

        Returns:
            Список созданных врагов либо пустой список после последней волны.
        """
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
        """Засчитывает убийство, только если враг относится к текущей волне.

        Args:
            wave_number: Номер волны, сохраненный в побежденном противнике.

        Returns:
            Ничего.
        """
        if wave_number != self.wave_number:
            return
        self._kills_after_last_spawn += 1

    def should_spawn_next_wave(self, level: Level) -> bool:
        """Проверяет, достигнут ли порог убийств для следующей волны.

        Args:
            level: Активный уровень, определяющий наличие следующей волны.

        Returns:
            True после достижения процентного и минимального порогов убийств.
        """
        if not self._has_next_wave(level) or self._last_wave_size == 0:
            return False
        return self._kills_after_last_spawn >= self._next_wave_threshold()

    def has_spawned_all_waves(self, level: Level) -> bool:
        """Проверяет, созданы ли все волны конечного уровня.

        Args:
            level: Активный уровень, прогресс которого проверяется.

        Returns:
            True только для завершенного конечного уровня. Для бесконечного
            режима всегда возвращается False.
        """
        if level.level_id == ENDLESS_LEVEL_ID:
            return False
        return self.wave_number >= len(self._level_waves(level.level_id))

    def _next_wave_size(self, level: Level) -> int:
        """Вычисляет количество врагов следующей волны.

        Args:
            level: Активный уровень с фиксированными или растущими волнами.

        Returns:
            Количество врагов либо ноль после последней конечной волны.
        """
        if level.level_id == ENDLESS_LEVEL_ID:
            return ENDLESS_FIRST_WAVE_SIZE + (
                self.wave_number * ENDLESS_WAVE_INCREMENT
            )

        waves = self._level_waves(level.level_id)
        if self.wave_number >= len(waves):
            return 0
        return waves[self.wave_number]

    def _has_next_wave(self, level: Level) -> bool:
        """Проверяет наличие следующей волны на уровне.

        Args:
            level: Активный уровень с проверяемой последовательностью волн.

        Returns:
            True для бесконечного режима или до последней конечной волны.
        """
        if level.level_id == ENDLESS_LEVEL_ID:
            return True
        return self.wave_number < len(self._level_waves(level.level_id))

    def _next_wave_threshold(self) -> int:
        """Вычисляет порог убийств по доле волны и абсолютному минимуму.

        Returns:
            Округленный вверх порог, который не может быть ниже минимума.
        """
        threshold = self._last_wave_size * WAVE_NEXT_TRIGGER_RATIO
        return max(WAVE_MIN_NEXT_TRIGGER_KILLS, math.ceil(threshold))

    def _spawn_zombie(
        self,
        level: Level,
        index: int,
        wave_number: int,
    ) -> Zombie:
        """Создает врага около центра выбранного тайла появления.

        Args:
            level: Активный уровень с доступными точками появления.
            index: Индекс врага для циклического выбора точки появления.
            wave_number: Номер волны, назначаемый противнику.

        Returns:
            Обычного врага либо случайный вариант бесконечного режима.
        """
        tile = level.zombie_spawns[index % len(level.zombie_spawns)]
        jitter_x = self._randomizer.randint(-SPAWN_JITTER, SPAWN_JITTER)
        jitter_y = self._randomizer.randint(-SPAWN_JITTER, SPAWN_JITTER)
        tile_padding = (TILE_SIZE - ZOMBIE_SIZE) / 2
        position = pygame.Vector2(
            tile[0] * TILE_SIZE + tile_padding + jitter_x,
            tile[1] * TILE_SIZE + tile_padding + jitter_y,
        )
        kind = NORMAL_ZOMBIE_KIND
        if level.level_id == ENDLESS_LEVEL_ID:
            kind = self._choose_endless_kind()
        return self.create_zombie(position, wave_number, kind)

    def create_zombie(
        self,
        position: pygame.Vector2,
        wave_number: int,
        kind: str = NORMAL_ZOMBIE_KIND,
    ) -> Zombie:
        """Создает вариант врага по его постоянному идентификатору.

        Args:
            position: Позиция левого верхнего угла врага в мире.
            wave_number: Номер волны для учета убийств.
            kind: Тип обычного, красного или синего противника.

        Returns:
            Настроенного врага с соответствующими здоровьем, спрайтом и очками.
        """
        if kind == BLUE_ZOMBIE_KIND:
            return Zombie(
                position,
                color=BLUE,
                hp_multiplier=BLUE_ZOMBIE_HP_MULTIPLIER,
                wave_number=wave_number,
                score_value=BLUE_ZOMBIE_SCORE,
                sprite_file=BLUE_ENEMY_SPRITE_FILE,
                kind=kind,
            )
        if kind == RED_ZOMBIE_KIND:
            return Zombie(
                position,
                color=RED,
                hp_multiplier=RED_ZOMBIE_HP_MULTIPLIER,
                wave_number=wave_number,
                score_value=RED_ZOMBIE_SCORE,
                sprite_file=RED_ENEMY_SPRITE_FILE,
                kind=kind,
            )
        return Zombie(position, GREEN, wave_number=wave_number, kind=kind)

    def _choose_endless_kind(self) -> str:
        """Выбирает тип врага бесконечного режима по заданным весам.

        Returns:
            Идентификатор обычного, красного или синего врага.
        """
        return self._randomizer.weighted_choice(
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

    @staticmethod
    def _level_waves(level_id: int) -> tuple[int, ...]:
        """Возвращает последовательность размеров волн конечного уровня.

        Args:
            level_id: Числовой идентификатор уровня.

        Returns:
            Настроенные размеры волн либо пустой кортеж для бесконечного
            режима.
        """
        if level_id == LEVEL_ONE_ID:
            return LEVEL_ONE_WAVES
        if level_id == LEVEL_TWO_ID:
            return LEVEL_TWO_WAVES
        return ()
