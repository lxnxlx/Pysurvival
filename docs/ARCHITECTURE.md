# Архитектура PySurvival

Схема показывает основные слои проекта и направление зависимостей. Центральный
класс `Game` управляет игровым циклом, но передает специализированную работу
отдельным менеджерам.

```mermaid
flowchart TB
    Main["src.main<br/>Точка входа"] --> Game

    subgraph Core["Ядро и игровой цикл"]
        Game["Game<br/>события -> обновление -> отрисовка"]
        State["StateManager<br/>menu / playing / pause / scores"]
        LevelLoader["LevelLoader<br/>загрузка карты"]
        Level["Level<br/>сетка, точки появления, портал"]
        Game --> State
        Game --> LevelLoader
        LevelLoader --> Level
    end

    subgraph Managers["Игровые подсистемы"]
        Entities["EntityManager<br/>хранение и очистка сущностей"]
        Waves["WaveManager<br/>волны и типы врагов"]
        Random["PseudoRandom<br/>единый генератор событий"]
        Path["Pathfinder<br/>поиск пути A*"]
        Collision["CollisionManager<br/>AABB и разделение хитбоксов"]
        Save["SaveSystem<br/>сохранение и рекорды"]
        Sound["SoundManager<br/>звуки и музыка"]
        Game --> Entities
        Game --> Waves
        Game --> Collision
        Game --> Save
        Game --> Sound
        Waves --> Random
        Game --> Random
    end

    subgraph Domain["Игровые сущности"]
        Entity["Entity<br/>позиция, размер, HP, хитбокс"]
        Player["Player<br/>движение, стрельба, усиления"]
        Zombie["Zombie<br/>преследование и атака"]
        Bullet["Bullet<br/>полет и урон"]
        Pickups["Key / Medkit / Orb / Portal"]
        Entity --> Player
        Entity --> Zombie
        Entity --> Bullet
        Entity --> Pickups
        Entities --> Player
        Entities --> Zombie
        Entities --> Bullet
        Entities --> Pickups
        Zombie --> Path
        Path --> Level
    end

    subgraph View["Представление"]
        GameView["GameView<br/>экраны, карта и HUD"]
        UI["Button / MenuArt / WallTileSet"]
        Sprites["SpriteCache<br/>загрузка и кеширование"]
        Game --> GameView
        GameView --> UI
        Player --> Sprites
        Zombie --> Sprites
        Pickups --> Sprites
    end

    subgraph Data["Файлы и ресурсы"]
        Levels[("data/levels/*.json")]
        Saves[("data/saves/*.json")]
        Assets[("assets/sprites и backgrounds")]
        Audio[("wav и music")]
        LevelLoader --> Levels
        Save --> Saves
        Sprites --> Assets
        UI --> Assets
        Sound --> Audio
    end

    classDef core fill:#dce8f2,stroke:#3b617d,color:#101820;
    classDef manager fill:#e4eddc,stroke:#587044,color:#101820;
    classDef domain fill:#f3e5d4,stroke:#93683b,color:#101820;
    classDef view fill:#eadff0,stroke:#765587,color:#101820;
    classDef data fill:#eeeeee,stroke:#666666,color:#101820;

    class Game,State,LevelLoader,Level core;
    class Entities,Waves,Random,Path,Collision,Save,Sound manager;
    class Entity,Player,Zombie,Bullet,Pickups domain;
    class GameView,UI,Sprites view;
    class Levels,Saves,Assets,Audio data;
```

## Один кадр игры

1. `Game` получает события pygame и передает их активному состоянию.
2. Игрок и враги обновляют позиции; враги строят маршрут через A*.
3. Пространственная сетка отбирает соседние пары, затем AABB обрабатывает
   столкновения, попадания и подбор предметов.
4. `WaveManager` проверяет прогресс волны и создает новых врагов через общий
   `PseudoRandom`.
5. `EntityManager` удаляет неактивные объекты.
6. `GameView` рисует уровень, сущности, HUD и текущий экран интерфейса.

Сохранение фиксирует состояние игрока, текущей волны, живых врагов и предметов.
Поэтому `Continue` восстанавливает прохождение, а не начинает уровень заново.
