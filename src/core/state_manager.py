"""Хранилище состояния меню, игрового процесса и экрана рекордов."""

from src.core.constants import MENU_STATE


class StateManager:
    def __init__(self) -> None:
        self._state = MENU_STATE

    @property
    def state(self) -> str:
        return self._state

    def set_state(self, state: str) -> None:
        self._state = state

    def is_state(self, state: str) -> bool:
        return self._state == state
