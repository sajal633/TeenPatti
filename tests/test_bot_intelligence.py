from app.game import GameManager, SeatPlayer, TableState
from app.teenpatti import Card


def test_elite_bot_packs_on_clear_loss() -> None:
    manager = GameManager()
    table = TableState(
        table_id=1,
        name="T",
        max_players=6,
        boot_amount=10,
        min_buyin=100,
        max_buyin=1000,
    )
    bot = SeatPlayer("b1", "Bot", chips=500, is_bot=True, cards=[Card("2", "♠"), Card("4", "♥"), Card("7", "♦")])
    human = SeatPlayer("u1", "Human", chips=500, is_bot=False, cards=[Card("A", "♠"), Card("A", "♥"), Card("K", "♦")])
    table.players = [bot, human]
    table.hand_active = True
    table.current_bet = 10

    action, _ = manager._bot_decision(table, bot)
    assert action == "pack"


def test_elite_bot_shows_on_near_certain_win_heads_up() -> None:
    manager = GameManager()
    table = TableState(
        table_id=1,
        name="T",
        max_players=6,
        boot_amount=10,
        min_buyin=100,
        max_buyin=1000,
    )
    bot = SeatPlayer("b1", "Bot", chips=500, is_bot=True, cards=[Card("A", "♠"), Card("A", "♥"), Card("A", "♦")])
    human = SeatPlayer("u1", "Human", chips=500, is_bot=False, cards=[Card("K", "♠"), Card("Q", "♥"), Card("J", "♦")])
    table.players = [bot, human]
    table.hand_active = True
    table.current_bet = 10

    action, _ = manager._bot_decision(table, bot)
    assert action in {"show", "raise"}
