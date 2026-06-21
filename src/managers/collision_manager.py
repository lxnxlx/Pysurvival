"""AABB collision helpers used by game code and tests."""

from __future__ import annotations

from typing import Protocol


class RectLike(Protocol):
    left: int
    right: int
    top: int
    bottom: int


class CollisionManager:
    @staticmethod
    def intersects(left: RectLike, right: RectLike) -> bool:
        return (
            left.left < right.right
            and left.right > right.left
            and left.top < right.bottom
            and left.bottom > right.top
        )

    @staticmethod
    def pairs(
        left_items: list[RectLike],
        right_items: list[RectLike],
    ) -> list[tuple[RectLike, RectLike]]:
        pairs = []
        for left in left_items:
            for right in right_items:
                if CollisionManager.intersects(left, right):
                    pairs.append((left, right))
        return pairs
