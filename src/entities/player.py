"""Игрок с механиками движения, стрельбы и временных усилений."""

from __future__ import annotations

import pygame

from src.core.constants import (
    BLUE,
    BLACK,
    INVULNERABLE_SPRITE_TINT,
    PLAYER_DAMAGE_INVULNERABILITY_SECONDS,
    PLAYER_INVULNERABILITY_SECONDS,
    PLAYER_MAX_HP,
    PLAYER_SPRITE_FILE,
    PLAYER_SHOOT_COOLDOWN,
    PLAYER_SIZE,
    PLAYER_SPEED,
)
from src.core.sprite_cache import SpriteCache
from src.entities.base import Entity
from src.entities.bullet import Bullet


class Player(Entity):
    def __init__(self, position: pygame.Vector2) -> None:
        super().__init__(position, PLAYER_SIZE, BLUE, PLAYER_MAX_HP)
        self.score = 0
        self.has_key = False
        self._shoot_timer = 0.0
        self._invulnerability_timer = 0.0
        self._damage_invulnerability_timer = 0.0
        self._facing_angle = 0.0
        self._sprite = SpriteCache.get(PLAYER_SPRITE_FILE, self.size)
        self._invulnerable_sprite = SpriteCache.get(
            PLAYER_SPRITE_FILE,
            self.size,
            INVULNERABLE_SPRITE_TINT,
        )

    @property
    def is_invulnerable(self) -> bool:
        return self._invulnerability_timer > 0

    @property
    def is_damage_protected(self) -> bool:
        return self.is_invulnerable or self._damage_invulnerability_timer > 0

    @property
    def facing_angle(self) -> float:
        return self._facing_angle

    def update_timers(self, dt: float) -> None:
        """Обновляет таймеры стрельбы и неуязвимости.

        Args:
            dt: Время с предыдущего кадра в секундах.

        Returns:
            Ничего.
        """
        self._shoot_timer = max(0.0, self._shoot_timer - dt)
        self._invulnerability_timer = max(
            0.0,
            self._invulnerability_timer - dt,
        )
        self._damage_invulnerability_timer = max(
            0.0,
            self._damage_invulnerability_timer - dt,
        )
        self.color = BLACK if self.is_invulnerable else BLUE

    def move(
        self,
        direction: pygame.Vector2,
        dt: float,
        walls: list[pygame.Rect],
        bounds: pygame.Rect,
    ) -> None:
        """Перемещает игрока с раздельной обработкой столкновений по осям.

        Args:
            direction: Исходный вектор направления движения.
            dt: Время с предыдущего кадра в секундах.
            walls: Прямоугольники непроходимых стен.
            bounds: Прямоугольник допустимой области движения игрока.

        Returns:
            Ничего.
        """
        if direction.length_squared() > 0:
            direction = direction.normalize()
        # Axis-separated movement keeps collision response simple and stable.
        velocity = direction * PLAYER_SPEED * dt
        self._move_axis(pygame.Vector2(velocity.x, 0), walls, bounds)
        self._move_axis(pygame.Vector2(0, velocity.y), walls, bounds)

    def try_shoot(self, target: pygame.Vector2) -> Bullet | None:
        """Создает снаряд, если цель корректна и перезарядка завершена.

        Args:
            target: Положение курсора в мировых координатах.

        Returns:
            Снаряд, направленный в цель, либо None во время перезарядки или
            при совпадении цели с центром игрока.
        """
        direction = target - self.center
        if direction.length_squared() == 0:
            return None
        self.aim_at(target)
        if self._shoot_timer > 0:
            return None

        self._shoot_timer = PLAYER_SHOOT_COOLDOWN
        return Bullet(self.center, direction.normalize())

    def aim_at(self, target: pygame.Vector2) -> None:
        direction = target - self.center
        if direction.length_squared() == 0:
            return
        sprite_forward = pygame.Vector2(0, -1)
        self._facing_angle = -sprite_forward.angle_to(direction)

    def heal(self, amount: int) -> None:
        self.hp = min(PLAYER_MAX_HP, self.hp + amount)

    def activate_invulnerability(self) -> None:
        self._invulnerability_timer = PLAYER_INVULNERABILITY_SECONDS
        self.color = BLACK

    def take_damage(self, amount: int) -> None:
        if self.is_damage_protected:
            return
        super().take_damage(amount)
        if self.alive:
            self._damage_invulnerability_timer = (
                PLAYER_DAMAGE_INVULNERABILITY_SECONDS
            )

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        sprite = (
            self._invulnerable_sprite
            if self.is_invulnerable
            else self._sprite
        )
        rotated_sprite = pygame.transform.rotate(
            sprite,
            self._facing_angle,
        )
        screen_center = self.center - camera
        rect = rotated_sprite.get_rect(center=screen_center)
        surface.blit(rotated_sprite, rect)

    def _move_axis(
        self,
        delta: pygame.Vector2,
        walls: list[pygame.Rect],
        bounds: pygame.Rect,
    ) -> None:
        """Применяет смещение по одной оси и обрабатывает препятствия.

        Раздельное движение по осям не позволяет проходить через углы стен
        по диагонали и помогает определить сторону столкновения.

        Args:
            delta: Горизонтальное или вертикальное смещение.
            walls: Прямоугольники непроходимых стен.
            bounds: Прямоугольник допустимой области движения игрока.

        Returns:
            Ничего.
        """
        self.position += delta
        rect = self.rect
        if not bounds.contains(rect):
            rect.clamp_ip(bounds)
            self.position.update(rect.topleft)

        for wall in walls:
            if self.rect.colliderect(wall):
                if delta.x > 0:
                    self.position.x = wall.left - self.size
                elif delta.x < 0:
                    self.position.x = wall.right
                if delta.y > 0:
                    self.position.y = wall.top - self.size
                elif delta.y < 0:
                    self.position.y = wall.bottom
