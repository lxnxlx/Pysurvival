"""JSON persistence for progress and leaderboard data."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from src.core.constants import SAVE_FILE, SCORES_FILE, TOP_SCORES_LIMIT


@dataclass
class SaveData:
    player_name: str
    level_id: int
    score: int
    hp: int
    ammo: int
    reserve_ammo: int
    has_key: bool


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
        self._save_file = save_file
        self._scores_file = scores_file
        self._save_file.parent.mkdir(parents=True, exist_ok=True)

    def save_game(self, data: SaveData) -> None:
        with self._save_file.open("w", encoding="utf-8") as file:
            json.dump(asdict(data), file, indent=2)

    def load_game(self) -> SaveData | None:
        if not self._save_file.exists():
            return None
        try:
            with self._save_file.open("r", encoding="utf-8") as file:
                payload = json.load(file)
            payload.setdefault("player_name", "Player")
            return SaveData(**payload)
        except (json.JSONDecodeError, TypeError):
            return None

    def has_save(self) -> bool:
        return self.load_game() is not None

    def clear_save(self) -> None:
        if self._save_file.exists():
            self._save_file.unlink()

    def add_score(self, player_name: str, score: int) -> None:
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
        if not self._scores_file.exists():
            return []
        try:
            with self._scores_file.open("r", encoding="utf-8") as file:
                payload = json.load(file)
            return [self._score_from_payload(item) for item in payload]
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return []

    @staticmethod
    def _score_from_payload(payload: dict) -> ScoreEntry:
        # Older score files had timestamps but no names; keep them readable.
        return ScoreEntry(
            player_name=payload.get("player_name", "Player"),
            score=int(payload["score"]),
        )
