"""Хранение прогресса и таблицы рекордов в формате JSON."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from src.core.constants import (
    SAVE_FILE,
    SAVE_VERSION,
    SCORES_FILE,
    TOP_SCORES_LIMIT,
)


@dataclass
class ZombieSaveData:
    x_pos: float
    y_pos: float
    hp: int
    wave_number: int
    kind: str


@dataclass
class PickupSaveData:
    x_pos: float
    y_pos: float


@dataclass
class SaveData:
    player_name: str
    level_id: int
    score: int
    hp: int
    has_key: bool
    version: int = SAVE_VERSION
    player_x: float | None = None
    player_y: float | None = None
    wave_number: int = 0
    kills_after_last_spawn: int = 0
    last_wave_size: int = 0
    zombies: list[ZombieSaveData] = field(default_factory=list)
    key_spawned: bool = False
    medkits: list[PickupSaveData] = field(default_factory=list)
    invulnerability_orbs: list[PickupSaveData] = field(
        default_factory=list
    )


@dataclass
class ScoreEntry:
    player_name: str
    score: int


class SaveSystem:
    def __init__(
        self,
        save_file: Path = SAVE_FILE,
        scores_file: Path = SCORES_FILE,
    ) -> None:
        """Настраивает JSON-хранилище и создает необходимые каталоги.

        Args:
            save_file: Путь к снимку состояния текущего прохождения.
            scores_file: Путь к файлу таблицы рекордов.

        Returns:
            Ничего.
        """
        self._save_file = save_file
        self._scores_file = scores_file
        self._save_file.parent.mkdir(parents=True, exist_ok=True)
        self._scores_file.parent.mkdir(parents=True, exist_ok=True)

    def save_game(self, data: SaveData) -> None:
        """Сериализует полный снимок состояния игры в JSON.

        Args:
            data: Сохраняемое состояние игрока, волн, врагов и предметов.

        Returns:
            Ничего.
        """
        with self._save_file.open("w", encoding="utf-8") as file:
            json.dump(asdict(data), file, indent=2)

    def load_game(self) -> SaveData | None:
        """Загружает, проверяет и при необходимости обновляет снимок игры.

        Неизвестные поля игнорируются для совместимости будущих версий.
        Отсутствие версии обозначает старое сохранение, а вложенные сущности
        преобразуются в типизированные объекты. Некорректный JSON считается
        отсутствующим сохранением.

        Returns:
            Проверенные данные сохранения либо None, если файл отсутствует
            или содержит некорректные данные.
        """
        if not self._save_file.exists():
            return None
        try:
            with self._save_file.open("r", encoding="utf-8") as file:
                payload = json.load(file)
            if not isinstance(payload, dict):
                return None
            payload.setdefault("player_name", "Player")
            payload.setdefault("version", 1)
            current_fields = {item.name for item in fields(SaveData)}
            current_payload = {
                key: value
                for key, value in payload.items()
                if key in current_fields
            }
            current_payload["zombies"] = [
                ZombieSaveData(**item)
                for item in current_payload.get("zombies", [])
            ]
            current_payload["medkits"] = [
                PickupSaveData(**item)
                for item in current_payload.get("medkits", [])
            ]
            current_payload["invulnerability_orbs"] = [
                PickupSaveData(**item)
                for item in current_payload.get(
                    "invulnerability_orbs",
                    [],
                )
            ]
            return SaveData(**current_payload)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return None

    def has_save(self) -> bool:
        """Проверяет наличие корректного снимка состояния игры.

        Returns:
            True, если сохранение существует и проходит проверку.
        """
        return self.load_game() is not None

    def clear_save(self) -> None:
        """Удаляет снимок текущего прохождения, если он существует.

        Returns:
            Ничего.
        """
        if self._save_file.exists():
            self._save_file.unlink()

    def add_score(self, player_name: str, score: int) -> None:
        """Добавляет результат, сортирует список и применяет лимит записей.

        Args:
            player_name: Имя игрока для отображения в таблице рекордов.
            score: Итоговое количество очков за прохождение.

        Returns:
            Ничего.
        """
        entries = self.load_scores()
        entries.append(ScoreEntry(player_name=player_name, score=score))
        entries.sort(key=lambda item: item.score, reverse=True)
        with self._scores_file.open("w", encoding="utf-8") as file:
            json.dump(
                [asdict(item) for item in entries[:TOP_SCORES_LIMIT]],
                file,
                indent=2,
            )

    def load_scores(self) -> list[ScoreEntry]:
        """Загружает и проверяет записи таблицы рекордов из JSON.

        Returns:
            Список результатов либо пустой список при отсутствии или
            повреждении данных.
        """
        if not self._scores_file.exists():
            return []
        try:
            with self._scores_file.open("r", encoding="utf-8") as file:
                payload = json.load(file)
            if not isinstance(payload, list):
                return []
            return [self._score_from_payload(item) for item in payload]
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return []

    @staticmethod
    def _score_from_payload(payload: object) -> ScoreEntry:
        """Преобразует значение JSON в совместимую запись результата.

        Args:
            payload: Исходное значение из массива таблицы рекордов.

        Returns:
            Типизированную запись. Старые записи получают стандартное имя.

        Raises:
            TypeError: Если запись не является объектом JSON.
        """
        if not isinstance(payload, dict):
            raise TypeError("Score entry must be a JSON object")
        return ScoreEntry(
            player_name=payload.get("player_name", "Player"),
            score=int(payload["score"]),
        )
