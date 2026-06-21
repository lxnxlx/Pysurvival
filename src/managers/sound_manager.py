"""Загрузка и воспроизведение коротких игровых звуков."""

from __future__ import annotations

from pathlib import Path

import pygame

from src.core.constants import (
    BUFF_SOUND_FILE,
    ENDLESS_LEVEL_ID,
    ENDLESS_MUSIC_FILE,
    HEALTH_SOUND_FILE,
    KEY_SOUND_FILE,
    LEVEL_ONE_ID,
    LEVEL_ONE_MUSIC_FILE,
    LEVEL_TWO_ID,
    LEVEL_TWO_MUSIC_FILE,
    MENU_MUSIC_FILE,
    MONSTER_DEATH_SOUND_FILE,
    SHOT_SOUND_FILE,
)

MUSIC_BY_LEVEL = {
    LEVEL_ONE_ID: LEVEL_ONE_MUSIC_FILE,
    LEVEL_TWO_ID: LEVEL_TWO_MUSIC_FILE,
    ENDLESS_LEVEL_ID: ENDLESS_MUSIC_FILE,
}


class SoundManager:
    def __init__(self) -> None:
        self._enabled = self._initialize_mixer()
        self._shot = self._load(SHOT_SOUND_FILE)
        self._buff = self._load(BUFF_SOUND_FILE)
        self._key = self._load(KEY_SOUND_FILE)
        self._health = self._load(HEALTH_SOUND_FILE)
        self._monster_death = self._load(MONSTER_DEATH_SOUND_FILE)
        self._current_music: Path | None = None

    def play_shot(self) -> None:
        self._play(self._shot)

    def play_buff_pickup(self) -> None:
        self._play(self._buff)

    def play_key_pickup(self) -> None:
        self._play(self._key)

    def play_health_pickup(self) -> None:
        self._play(self._health)

    def play_monster_death(self) -> None:
        self._play(self._monster_death)

    def play_menu_music(self) -> None:
        self._play_music(MENU_MUSIC_FILE)

    def play_level_music(self, level_id: int) -> None:
        music_file = MUSIC_BY_LEVEL.get(level_id)
        if music_file is not None:
            self._play_music(music_file)

    def _load(self, path: Path) -> pygame.mixer.Sound | None:
        if not self._enabled:
            return None
        try:
            return pygame.mixer.Sound(str(path))
        except (FileNotFoundError, pygame.error):
            return None

    def _play_music(self, path: Path) -> None:
        if not self._enabled or path == self._current_music:
            return
        try:
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.play(loops=-1)
            self._current_music = path
        except (FileNotFoundError, pygame.error):
            self._current_music = None

    @staticmethod
    def _play(sound: pygame.mixer.Sound | None) -> None:
        if sound is not None:
            sound.play()

    @staticmethod
    def _initialize_mixer() -> bool:
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            return True
        except pygame.error:
            return False
