"""Вспомогательные алгоритмы AABB-столкновений."""

from __future__ import annotations

from typing import Protocol

import pygame


class RectLike(Protocol):
    left: int
    right: int
    top: int
    bottom: int


class MovableRectLike(Protocol):
    position: pygame.Vector2
    size: int
    rect: pygame.Rect


class CollisionManager:
    @staticmethod
    def intersects(left: RectLike, right: RectLike) -> bool:
        """Проверяет пересечение прямоугольников алгоритмом AABB.

        Args:
            left: Первый прямоугольник, выровненный по осям.
            right: Второй прямоугольник, выровненный по осям.

        Returns:
            True, если проекции пересекаются по обеим осям. Соприкосновение
            границ не считается пересечением.
        """
        return (
            left.left < right.right
            and left.right > right.left
            and left.top < right.bottom
            and left.bottom > right.top
        )

    @classmethod
    def separate(
        cls,
        left: MovableRectLike,
        right: MovableRectLike,
    ) -> bool:
        """Разделяет сущности по кратчайшей оси пересечения AABB.

        Args:
            left: Первая перемещаемая квадратная сущность.
            right: Вторая перемещаемая квадратная сущность.

        Returns:
            True, если пересечение найдено и устранено, иначе False.
        """
        left_rect = left.rect
        right_rect = right.rect
        if not cls.intersects(left_rect, right_rect):
            return False

        overlap_x = min(left_rect.right, right_rect.right) - max(
            left_rect.left,
            right_rect.left,
        )
        overlap_y = min(left_rect.bottom, right_rect.bottom) - max(
            left_rect.top,
            right_rect.top,
        )
        if overlap_x <= overlap_y:
            cls._separate_axis(left, right, overlap_x, axis="x")
        else:
            cls._separate_axis(left, right, overlap_y, axis="y")
        return True

    @staticmethod
    def _separate_axis(
        left: MovableRectLike,
        right: MovableRectLike,
        overlap: int,
        axis: str,
    ) -> None:
        """Распределяет глубину проникновения поровну между сущностями.

        Args:
            left: Первая перемещаемая сущность.
            right: Вторая перемещаемая сущность.
            overlap: Глубина пересечения по выбранной оси.
            axis: Изменяемая координата ``x`` или ``y``.

        Returns:
            Ничего.
        """
        # The extra pixel avoids integer Rect rounding leaving an overlap.
        displacement = (overlap + 1) / 2
        left_center = getattr(left.position, axis) + left.size / 2
        right_center = getattr(right.position, axis) + right.size / 2
        direction = -1 if left_center <= right_center else 1
        setattr(
            left.position,
            axis,
            getattr(left.position, axis) + direction * displacement,
        )
        setattr(
            right.position,
            axis,
            getattr(right.position, axis) - direction * displacement,
        )
