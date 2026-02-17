import pytest

from app.game import GameManager
from app.teenpatti import Card, compare_hands, evaluate_hand


def test_trail_beats_sequence() -> None:
    trail = [Card("A", "♠"), Card("A", "♥"), Card("A", "♦")]
    sequence = [Card("Q", "♠"), Card("K", "♥"), Card("A", "♦")]
    assert compare_hands(trail, sequence) == 1


def test_pure_sequence_beats_sequence() -> None:
    pure = [Card("Q", "♠"), Card("K", "♠"), Card("A", "♠")]
    sequence = [Card("Q", "♠"), Card("K", "♥"), Card("A", "♦")]
    assert compare_hands(pure, sequence) == 1


def test_a23_sequence_beats_kqj_sequence_by_standard() -> None:
    a23 = [Card("A", "♠"), Card("2", "♥"), Card("3", "♦")]
    kqj = [Card("K", "♠"), Card("Q", "♥"), Card("J", "♦")]
    assert compare_hands(a23, kqj) == 1


def test_pair_detection() -> None:
    pair = [Card("9", "♠"), Card("9", "♥"), Card("A", "♦")]
    score = evaluate_hand(pair)
    assert score[0] == 2
    assert score[1][0] == 9


def test_duplicate_cards_are_rejected() -> None:
    bad_hand = [Card("A", "♠"), Card("A", "♠"), Card("K", "♦")]
    with pytest.raises(ValueError):
        evaluate_hand(bad_hand)


def test_show_action_rejects_when_not_two_active_players() -> None:
    manager = GameManager()
    manager.seed_tables([
        {"id": 1, "name": "T1", "max_players": 6, "boot_amount": 10, "min_buyin": 100, "max_buyin": 1000}
    ])
    manager.join_table(1, "u1", "U1", 200)
    manager.join_table(1, "u2", "U2", 200)
    manager.join_table(1, "u3", "U3", 200)

    state = manager.get_table_state(1, "u1")
    current_player = state["current_player"]
    with pytest.raises(ValueError):
        manager.act(current_player, "show")
