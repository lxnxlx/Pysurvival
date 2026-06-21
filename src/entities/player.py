"""Player entity with shooting and reload state."""

from __future__ import annotations

import pygame

from src.core.constants import (
    BLUE,
    BLACK,
    PLAYER_DAMAGE_INVULNERABILITY_SECONDS,
    PLAYER_INVULNERABILITY_SECONDS,
    PLAYER_AMMO,
    PLAYER_MAX_HP,
    PLAYER_RELOAD_SECONDS,
    PLAYER_RESERVE_AMMO,
    PLAYER_SHOOT_COOLDOWN,
    PLAYER_SIZE,
    PLAYER_SPEED,
)
from src.entities.base import Entity
from src.entities.bullet import Bullet


class Player(Entity):
    def __init__(self, position: pygame.Vector2) -> None:
        super().__init__(position, PLAYER_SIZE, BLUE, PLAYER_MAX_HP)
        self.ammo = PLAYER_AMMO
        self.reserve_ammo = PLAYER_RESERVE_AMMO
        self.infinite_ammo = True
        self.score = 0
        self.has_key = False
        self._shoot_timer = 0.0
        self._reload_timer = 0.0
        self._invulnerability_timer = 0.0
        self._damage_invulnerability_timer = 0.0

    @property
    def is_reloading(self) -> bool:
        return self._reload_timer > 0

    @property
    def is_invulnerable(self) -> bool:
        return self._invulnerability_timer > 0

    @property
    def is_damage_protected(self) -> bool:
        return self.is_invulnerable or self._damage_invulnerability_timer > 0

    def update_timers(self, dt: float) -> None:
        self._shoot_timer = max(0.0, self._shoot_timer - dt)
        self._reload_timer = max(0.0, self._reload_timer - dt)
        self._invulnerability_timer = max(
            0.0,
            self._invulnerability_timer - dt,
        )
        self._damage_invulnerability_timer = max(
            0.0,
            self._damage_invulnerability_timer - dt,
        )
        self.color = BLACK if self.is_invulnerable else BLUE
        if self._reload_timer == 0 and self.ammo == 0:
            self._finish_reload()

    def move(
        self,
        direction: pygame.Vector2,
        dt: float,
        walls: list[pygame.Rect],
        bounds: pygame.Rect,
    ) -> None:
        if direction.length_squared() > 0:
            direction = direction.normalize()
        # Axis-separated movement keeps collision response simple and stable.
        velocity = direction * PLAYER_SPEED * dt
        self._move_axis(pygame.Vector2(velocity.x, 0), walls, bounds)
        self._move_axis(pygame.Vector2(0, velocity.y), walls, bounds)

    def try_shoot(self, target: pygame.Vector2) -> Bullet | None:
        if (
            self._shoot_timer > 0
            or self.is_reloading
            or (not self.infinite_ammo and self.ammo <= 0)
        ):
            return None
        direction = target - self.center
        if direction.length_squared() == 0:
            return None

        if not self.infinite_ammo:
            self.ammo -= 1
        self._shoot_timer = PLAYER_SHOOT_COOLDOWN
        return Bullet(self.center, direction.normalize())

    def reload(self) -> None:
        if self.infinite_ammo:
            return
        if self.ammo == PLAYER_AMMO or self.reserve_ammo <= 0:
            return
        self._reload_timer = PLAYER_RELOAD_SECONDS

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

    def _finish_reload(self) -> None:
        needed = PLAYER_AMMO - self.ammo
        loaded = min(needed, self.reserve_ammo)
        self.ammo += loaded
        self.reserve_ammo -= loaded

    def _move_axis(
        self,
        delta: pygame.Vector2,
        walls: list[pygame.Rect],
        bounds: pygame.Rect,
    ) -> None:
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
