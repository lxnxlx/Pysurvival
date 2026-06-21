"""Поиск пути A* по прямоугольной сетке тайлов."""

from __future__ import annotations

import heapq
from collections.abc import Iterable


GridPosition = tuple[int, int]


class Pathfinder:
    def __init__(self, grid: list[str]) -> None:
        """Сохраняет карту тайлов, используемую алгоритмом A*.

        Args:
            grid: Прямоугольная карта, где ``#`` обозначает стену.

        Returns:
            Ничего.
        """
        self._grid = grid
        self._height = len(grid)
        self._width = len(grid[0]) if grid else 0

    def find_path(
        self,
        start: GridPosition,
        goal: GridPosition,
    ) -> list[GridPosition]:
        """Находит кратчайший путь по четырем направлениям алгоритмом A*.

        Очередь с приоритетом сортирует тайлы по сумме стоимости пройденного
        пути и Манхэттенского расстояния до цели. Повторный обход тайла
        выполняется только при обнаружении более короткого маршрута.

        Args:
            start: Координаты начального тайла в формате ``(x, y)``.
            goal: Координаты конечного тайла в формате ``(x, y)``.

        Returns:
            Путь, включающий начальный и конечный тайлы. Возвращает пустой
            список, если путь не существует или одна из точек заблокирована.
        """
        if not self._is_walkable(start) or not self._is_walkable(goal):
            return []

        frontier: list[tuple[int, GridPosition]] = [(0, start)]
        came_from: dict[GridPosition, GridPosition | None] = {start: None}
        cost_so_far: dict[GridPosition, int] = {start: 0}

        while frontier:
            _, current = heapq.heappop(frontier)
            if current == goal:
                break

            for next_pos in self._neighbors(current):
                new_cost = cost_so_far[current] + 1
                is_better_path = (
                    next_pos not in cost_so_far
                    or new_cost < cost_so_far[next_pos]
                )
                if is_better_path:
                    cost_so_far[next_pos] = new_cost
                    priority = new_cost + self._heuristic(next_pos, goal)
                    heapq.heappush(frontier, (priority, next_pos))
                    came_from[next_pos] = current

        if goal not in came_from:
            return []
        return self._restore_path(came_from, goal)

    def _neighbors(self, position: GridPosition) -> Iterable[GridPosition]:
        """Возвращает проходимых ортогональных соседей тайла.

        Args:
            position: Координаты проверяемого тайла.

        Returns:
            Ленивый итерируемый объект с координатами доступных соседей.
        """
        x_pos, y_pos = position
        candidates = (
            (x_pos + 1, y_pos),
            (x_pos - 1, y_pos),
            (x_pos, y_pos + 1),
            (x_pos, y_pos - 1),
        )
        return (
            candidate
            for candidate in candidates
            if self._is_walkable(candidate)
        )

    def _is_walkable(self, position: GridPosition) -> bool:
        """Проверяет, находится ли тайл внутри карты и не является ли стеной.

        Args:
            position: Координаты проверяемого тайла.

        Returns:
            True для тайла пола внутри сетки, иначе False.
        """
        x_pos, y_pos = position
        outside_grid = (
            x_pos < 0
            or y_pos < 0
            or y_pos >= self._height
            or x_pos >= self._width
        )
        if outside_grid:
            return False
        return self._grid[y_pos][x_pos] != "#"

    @staticmethod
    def _heuristic(left: GridPosition, right: GridPosition) -> int:
        """Вычисляет Манхэттенское расстояние для движения по четырем осям.

        Args:
            left: Координаты первого тайла.
            right: Координаты второго тайла.

        Returns:
            Минимальное количество ортогональных шагов без учета препятствий.
        """
        return abs(left[0] - right[0]) + abs(left[1] - right[1])

    @staticmethod
    def _restore_path(
        came_from: dict[GridPosition, GridPosition | None],
        goal: GridPosition,
    ) -> list[GridPosition]:
        """Восстанавливает прямой путь по таблице предшественников A*.

        Args:
            came_from: Соответствие посещенных тайлов их предшественникам.
            goal: Конечный тайл требуемого пути.

        Returns:
            Упорядоченные координаты от начального тайла до конечного.
        """
        current: GridPosition | None = goal
        path = []
        while current is not None:
            path.append(current)
            current = came_from[current]
        path.reverse()
        return path
