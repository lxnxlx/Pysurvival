"""Storage and cleanup for active gameplay entities."""

from __future__ import annotations

import pygame

from src.entities.bullet import Bullet
from src.entities.pickup import InvulnerabilityOrb, Key, Medkit, Portal
from src.entities.player import Player
from src.entities.zombie import Zombie


class EntityManager:
    def __init__(self) -> None:
        self.player: Player | None = None
        self.zombies: list[Zombie] = []
        self.bullets: list[Bullet] = []
        self.key: Key | None = None
        self.medkits: list[Medkit] = []
        self.invulnerability_orbs: list[InvulnerabilityOrb] = []
        self.portal: Portal | None = None

    def clear(self) -> None:
        self.zombies.clear()
        self.bullets.clear()
        self.medkits.clear()
        self.invulnerability_orbs.clear()
        self.key = None
        self.portal = None

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        for entity in self.all_drawable():
            entity.draw(surface, camera)

    def cleanup(self) -> None:
        self.zombies = [zombie for zombie in self.zombies if zombie.alive]
        self.bullets = [bullet for bullet in self.bullets if bullet.alive]
        self.medkits = [medkit for medkit in self.medkits if medkit.alive]
        self.invulnerability_orbs = [
            orb for orb in self.invulnerability_orbs if orb.alive
        ]
        if self.key is not None and not self.key.alive:
            self.key = None

    def all_drawable(self) -> list:
        entities = []
        if self.key is not None:
            entities.append(self.key)
        if self.portal is not None:
            entities.append(self.portal)
        entities.extend(self.medkits)
        entities.extend(self.invulnerability_orbs)
        entities.extend(self.bullets)
        entities.extend(self.zombies)
        if self.player is not None:
            entities.append(self.player)
        return entities
