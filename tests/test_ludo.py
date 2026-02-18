import random

import pytest

from app.ludo import MAX_STEPS, LudoManager


def _seed_table(manager: LudoManager, name: str = "T") -> int:
    tid = manager.create_table(name)["table_id"]
    manager.join_table(tid, "u1", "P1")
    manager.join_table(tid, "u2", "P2")
    manager.join_table(tid, "u3", "P3")
    manager.join_table(tid, "u4", "P4")
    manager.start_game(tid)
    return tid


def test_ludo_create_join_and_start() -> None:
    manager = LudoManager()
    tid = _seed_table(manager, "Ludo Pro")
    state = manager.get_state(tid, "u1")
    assert state["hand_active"] is True
    assert len(state["players"]) == 4
    assert state["turn_player"] == "u1"


def test_ludo_requires_six_to_leave_yard() -> None:
    manager = LudoManager()
    _seed_table(manager)

    orig = random.randint
    random.randint = lambda a, b: 6
    try:
        rolled = manager.roll_dice("u1")
    finally:
        random.randint = orig

    assert rolled["pending_move"] is True
    assert rolled["movable_tokens"] == [0, 1, 2, 3]

    moved = manager.move_token("u1", 0)
    p1 = next(p for p in moved["players"] if p["player_id"] == "u1")
    assert p1["tokens"][0]["steps"] == 0


def test_ludo_capture_sends_opponent_to_yard() -> None:
    manager = LudoManager()
    tid = _seed_table(manager, "Capture")

    table_obj = manager.tables[tid]
    p1 = table_obj.players[0]  # red start index 0
    p2 = table_obj.players[1]  # green start index 13

    p1.tokens[0].steps = 13  # board position 13
    p2.tokens[0].steps = 1   # board position 14

    table_obj.turn_idx = 0
    table_obj.dice_value = 1
    table_obj.pending_move = True

    state = manager.move_token("u1", 0)

    assert p2.tokens[0].steps == -1
    assert state["turn_player"] == "u1"  # capture bonus turn


def test_ludo_three_consecutive_sixes_forfeit_turn() -> None:
    manager = LudoManager()
    _seed_table(manager, "Sixes")

    seq = iter([6, 6, 6])
    orig = random.randint
    random.randint = lambda a, b: next(seq)
    try:
        s1 = manager.roll_dice("u1")
        manager.move_token("u1", 0)

        s2 = manager.roll_dice("u1")
        manager.move_token("u1", 0)

        s3 = manager.roll_dice("u1")
    finally:
        random.randint = orig

    assert s1["pending_move"] is True
    assert s2["pending_move"] is True
    assert s3["pending_move"] is False
    assert s3["turn_player"] == "u2"
    assert any(e.get("event") == "turn_forfeit" for e in s3["history"])


def test_ludo_safe_square_blocks_capture() -> None:
    manager = LudoManager()
    tid = _seed_table(manager, "SafeCapture")

    table_obj = manager.tables[tid]
    p1 = table_obj.players[0]  # red start 0
    p2 = table_obj.players[1]  # green start 13

    p1.tokens[0].steps = 7   # will move to safe square index 8
    p2.tokens[0].steps = 47  # board position also 8 for green

    table_obj.turn_idx = 0
    table_obj.dice_value = 1
    table_obj.pending_move = True

    manager.move_token("u1", 0)
    assert p2.tokens[0].steps == 47


def test_ludo_overshoot_move_is_blocked() -> None:
    manager = LudoManager()
    tid = _seed_table(manager, "Finish")

    table_obj = manager.tables[tid]
    p1 = table_obj.players[0]

    p1.tokens[0].steps = MAX_STEPS - 1
    table_obj.turn_idx = 0
    table_obj.dice_value = 2
    table_obj.pending_move = True

    with pytest.raises(ValueError, match="Illegal token move"):
        manager.move_token("u1", 0)


def test_ludo_rejects_unknown_player_action() -> None:
    manager = LudoManager()
    with pytest.raises(ValueError, match="not seated"):
        manager.roll_dice("ghost")


def test_ludo_home_reach_grants_bonus_turn() -> None:
    manager = LudoManager()
    tid = _seed_table(manager, "HomeBonus")

    table_obj = manager.tables[tid]
    p1 = table_obj.players[0]
    p1.tokens[0].steps = MAX_STEPS - 1

    table_obj.turn_idx = 0
    table_obj.dice_value = 1
    table_obj.pending_move = True

    state = manager.move_token("u1", 0)
    assert state["turn_player"] == "u1"
    assert any(e.get("event") == "move" and e.get("reached_home") for e in state["history"])


def test_ludo_double_token_creates_blockade_and_blocks_path() -> None:
    manager = LudoManager()
    tid = _seed_table(manager, "Blockade")
    table_obj = manager.tables[tid]
    p1, p2 = table_obj.players[0], table_obj.players[1]

    # Create P1 blockade at board position 8 using two tokens.
    p1.tokens[0].steps = 8
    p1.tokens[1].steps = 8

    # P2 tries to move from board pos 6 to 9 crossing 8, which should be blocked.
    p2.tokens[0].steps = 45  # green start 13 => (13+45)%52 = 6
    table_obj.turn_idx = 1
    table_obj.dice_value = 3
    table_obj.pending_move = True

    with pytest.raises(ValueError, match="Illegal token move"):
        manager.move_token("u2", 0)

    state = manager.get_state(tid, "u1")
    assert 8 in state["blockades"]


def test_ludo_extra_turn_can_chain_for_second_capture() -> None:
    manager = LudoManager()
    tid = _seed_table(manager, "DoubleCut")
    table_obj = manager.tables[tid]
    p1, p2, p3 = table_obj.players[0], table_obj.players[1], table_obj.players[2]

    # First capture target at position 14.
    p1.tokens[0].steps = 13
    p2.tokens[0].steps = 1
    # Second capture target at position 15 for immediate bonus turn.
    p3.tokens[0].steps = 41  # yellow start 26 => (26+41)%52 = 15

    table_obj.turn_idx = 0
    table_obj.dice_value = 1
    table_obj.pending_move = True

    first = manager.move_token("u1", 0)
    assert first["turn_player"] == "u1"
    assert p2.tokens[0].steps == -1

    table_obj.dice_value = 1
    table_obj.pending_move = True
    second = manager.move_token("u1", 0)

    assert p3.tokens[0].steps == -1
    assert second["turn_player"] == "u1"
