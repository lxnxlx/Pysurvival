"""Единый источник псевдослучайных значений для игровых событий."""

from __future__ import annotations

import random
from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")


class PseudoRandom:
    def __init__(self, seed: int | None = None) -> None:
        """Создает воспроизводимый источник случайности для игры.

        Args:
            seed: Необязательное начальное значение генератора. Одинаковые
                значения создают одинаковые последовательности.

        Returns:
            Ничего.
        """
        self._random = random.Random(seed)

    def chance(self, probability: float) -> bool:
        """Определяет наступление события по заданной вероятности.

        Args:
            probability: Вероятность события в диапазоне от 0.0 до 1.0.

        Returns:
            True, если сгенерированное значение меньше вероятности.
        """
        return self._random.random() < probability

    def randint(self, min_value: int, max_value: int) -> int:
        """Генерирует целое число во включающем границы диапазоне.

        Args:
            min_value: Минимально возможный результат.
            max_value: Максимально возможный результат.

        Returns:
            Псевдослучайное целое число между указанными границами.
        """
        return self._random.randint(min_value, max_value)

    def weighted_choice(
        self,
        weighted_items: Sequence[tuple[T, float]],
    ) -> T:
        """Выбирает элемент с помощью накопленных весовых интервалов.

        Args:
            weighted_items: Последовательность значений и их вероятностей.

        Returns:
            Значение, в накопительный интервал которого попало случайное
            число. Последнее значение служит защитой от ошибок округления.
        """
        roll = self._random.random()
        current = 0.0
        for item, weight in weighted_items:
            current += weight
            if roll < current:
                return item
        return weighted_items[-1][0]
