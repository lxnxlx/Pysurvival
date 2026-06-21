from src.managers.save_system import (
    PickupSaveData,
    SaveData,
    SaveSystem,
    ZombieSaveData,
)


def test_save_system_roundtrip(tmp_path):
    save_system = SaveSystem(
        save_file=tmp_path / "save.json",
        scores_file=tmp_path / "scores.json",
    )
    data = SaveData(
        player_name="Max",
        level_id=2,
        score=120,
        hp=70,
        has_key=True,
        player_x=100.5,
        player_y=200.5,
        wave_number=2,
        kills_after_last_spawn=4,
        last_wave_size=15,
        zombies=[
            ZombieSaveData(
                x_pos=10.0,
                y_pos=20.0,
                hp=34,
                wave_number=2,
                kind="normal",
            )
        ],
        medkits=[PickupSaveData(x_pos=30.0, y_pos=40.0)],
    )

    save_system.save_game(data)

    assert save_system.load_game() == data


def test_save_system_ignores_obsolete_fields(tmp_path):
    save_file = tmp_path / "save.json"
    save_file.write_text(
        (
            '{"player_name": "Max", "level_id": 2, "score": 120, '
            '"hp": 70, "legacy_field": 5, "has_key": true}'
        ),
        encoding="utf-8",
    )
    save_system = SaveSystem(
        save_file=save_file,
        scores_file=tmp_path / "scores.json",
    )

    loaded = save_system.load_game()

    assert loaded is not None
    assert loaded.score == 120


def test_save_system_rejects_non_object_json(tmp_path):
    save_file = tmp_path / "save.json"
    save_file.write_text("[]", encoding="utf-8")
    save_system = SaveSystem(
        save_file=save_file,
        scores_file=tmp_path / "scores.json",
    )

    assert save_system.load_game() is None


def test_save_system_keeps_top_five_scores(tmp_path):
    save_system = SaveSystem(
        save_file=tmp_path / "save.json",
        scores_file=tmp_path / "scores.json",
    )

    for score in [10, 50, 20, 70, 30, 60]:
        save_system.add_score("Max", score)

    assert [entry.score for entry in save_system.load_scores()] == [
        70,
        60,
        50,
        30,
        20,
    ]


def test_save_system_stores_player_names_in_scores(tmp_path):
    save_system = SaveSystem(
        save_file=tmp_path / "save.json",
        scores_file=tmp_path / "scores.json",
    )

    save_system.add_score("Max", 100)

    [score] = save_system.load_scores()
    assert score.player_name == "Max"
    assert score.score == 100


def test_save_system_rejects_non_list_scores(tmp_path):
    scores_file = tmp_path / "scores.json"
    scores_file.write_text('{"score": 100}', encoding="utf-8")
    save_system = SaveSystem(
        save_file=tmp_path / "save.json",
        scores_file=scores_file,
    )

    assert save_system.load_scores() == []
