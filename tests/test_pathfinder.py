from src.managers.pathfinder import Pathfinder


def test_pathfinder_builds_path_around_wall():
    grid = [
        ".....",
        ".###.",
        ".....",
    ]
    path = Pathfinder(grid).find_path((0, 0), (4, 0))

    assert path[0] == (0, 0)
    assert path[-1] == (4, 0)
    assert (1, 1) not in path


def test_pathfinder_returns_empty_path_for_blocked_goal():
    grid = [
        "...",
        ".#.",
        "...",
    ]

    assert Pathfinder(grid).find_path((0, 0), (1, 1)) == []
