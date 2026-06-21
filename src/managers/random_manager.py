"""Single pseudo-random source for gameplay events."""

from __future__ import annotations

import random
from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")


class PseudoRandom:
    def __init__(self, seed: int | None = None) -> None:
        # One Random instance keeps all random gameplay events reproducible.
        self._random = random.Random(seed)

    def chance(self, probability: float) -> bool:
        return self._random.random() < probability

    def randint(self, min_value: int, max_value: int) -> int:
        return self._random.randint(min_value, max_value)

    def weighted_choice(
        self,
        weighted_items: Sequence[tuple[T, float]],
    ) -> T:
        roll = self._random.random()
        current = 0.0
        for item, weight in weighted_items:
            current += weight
            if roll < current:
                return item
        return weighted_items[-1][0]
