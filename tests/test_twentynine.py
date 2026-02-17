from app.twentynine import T29Card, T29Player, T29Table, TwentyNineManager


def test_twentynine_create_join_and_start() -> None:
    manager = TwentyNineManager()
    table = manager.create_table("Pro 29")
    tid = table["table_id"]

    manager.join_table(tid, "u1", "U1")
    manager.join_table(tid, "u2", "U2")
    manager.join_table(tid, "u3", "U3")
    manager.join_table(tid, "u4", "U4")

    state = manager.start_hand(tid)
    assert state["hand_active"] is True
    assert len(state["players"]) == 4


def test_elite_bot_plays_legal_follow_suit() -> None:
    manager = TwentyNineManager()
    table = T29Table(table_id=1, name="T")
    bot = T29Player(player_id="b", display_name="Bot", is_bot=True, hand=[T29Card("J", "H"), T29Card("7", "S")])
    opp = T29Player(player_id="u", display_name="U", is_bot=False, hand=[T29Card("9", "H")])
    table.players = [bot, opp, T29Player("x","X"), T29Player("y","Y")]
    table.hand_active = True
    table.trump_suit = "S"
    table.lead_suit = "H"
    table.trick_cards = [("u", T29Card("9", "H"))]

    legal = manager._legal_cards(table, bot)
    assert legal == [T29Card("J", "H")]


def test_elite_bot_prefers_winning_card_when_possible() -> None:
    manager = TwentyNineManager()
    table = T29Table(table_id=1, name="T")
    bot = T29Player(player_id="b", display_name="Bot", is_bot=True, hand=[T29Card("J", "H"), T29Card("7", "H")])
    table.players = [
        T29Player("u", "U", hand=[]),
        bot,
        T29Player("x", "X", hand=[]),
        T29Player("y", "Y", hand=[]),
    ]
    table.turn_idx = 1
    table.hand_active = True
    table.trump_suit = "S"
    table.lead_suit = "H"
    table.trick_cards = [("u", T29Card("9", "H"))]

    card = manager._elite_choose_card(table, bot)
    assert card == T29Card("J", "H")
