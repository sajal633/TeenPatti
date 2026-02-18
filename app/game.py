from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import random
from threading import Lock
from typing import Any

from .teenpatti import Card, best_hand, compare_hands, new_deck


@dataclass
class SeatPlayer:
    player_id: str
    display_name: str
    chips: int
    is_bot: bool = False
    seen: bool = False
    packed: bool = False
    cards: list[Card] = field(default_factory=list)
    total_bet: int = 0


@dataclass
class TableState:
    table_id: int
    name: str
    max_players: int
    boot_amount: int
    min_buyin: int
    max_buyin: int
    players: list[SeatPlayer] = field(default_factory=list)
    pot: int = 0
    current_bet: int = 0
    dealer_idx: int = 0
    turn_idx: int = 0
    deck: list[Card] = field(default_factory=list)
    hand_active: bool = False
    hand_started_at: datetime | None = None
    action_log: list[dict[str, Any]] = field(default_factory=list)


class GameManager:
    def __init__(self) -> None:
        self.tables: dict[int, TableState] = {}
        self.user_table: dict[str, int] = {}
        self.lock = Lock()

    def seed_tables(self, configs: list[dict[str, Any]]) -> None:
        with self.lock:
            for cfg in configs:
                if cfg["id"] in self.tables:
                    continue
                self.tables[cfg["id"]] = TableState(
                    table_id=cfg["id"],
                    name=cfg["name"],
                    max_players=cfg["max_players"],
                    boot_amount=cfg["boot_amount"],
                    min_buyin=cfg["min_buyin"],
                    max_buyin=cfg["max_buyin"],
                )

    def list_tables(self) -> list[dict[str, Any]]:
        with self.lock:
            data: list[dict[str, Any]] = []
            for table in self.tables.values():
                data.append(
                    {
                        "table_id": table.table_id,
                        "name": table.name,
                        "players": len(table.players),
                        "max_players": table.max_players,
                        "boot_amount": table.boot_amount,
                        "pot": table.pot,
                        "hand_active": table.hand_active,
                    }
                )
            return sorted(data, key=lambda item: item["table_id"])

    def join_table(self, table_id: int, player_id: str, display_name: str, chips: int, is_bot: bool = False) -> dict[str, Any]:
        with self.lock:
            table = self.tables[table_id]
            if player_id in self.user_table:
                raise ValueError("Player already seated at a table")
            if len(table.players) >= table.max_players:
                raise ValueError("Table is full")
            if chips < table.min_buyin or chips > table.max_buyin:
                raise ValueError("Buy-in out of table range")

            table.players.append(SeatPlayer(player_id=player_id, display_name=display_name, chips=chips, is_bot=is_bot))
            self.user_table[player_id] = table_id
            table.action_log.append({"event": "join", "player_id": player_id, "at": datetime.utcnow().isoformat()})

            if len(table.players) >= 2 and not table.hand_active:
                self._start_hand(table)
            return self._public_state(table, for_player=player_id)

    def add_bot_players(self, table_id: int, count: int) -> None:
        with self.lock:
            table = self.tables[table_id]
            for _ in range(count):
                if len(table.players) >= table.max_players:
                    break
                bot_id = f"bot-{table_id}-{len(table.players)+1}-{random.randint(1000, 9999)}"
                bot_name = random.choice(["Ava", "Rex", "Nora", "Leo", "Mia", "Kane", "Iris"]) + " Bot"
                table.players.append(
                    SeatPlayer(player_id=bot_id, display_name=bot_name, chips=table.min_buyin * 2, is_bot=True)
                )
                self.user_table[bot_id] = table_id
                table.action_log.append({"event": "bot_join", "player_id": bot_id, "at": datetime.utcnow().isoformat()})
            if len(table.players) >= 2 and not table.hand_active:
                self._start_hand(table)

    def act(self, player_id: str, action: str, amount: int = 0) -> dict[str, Any]:
        with self.lock:
            table_id = self.user_table.get(player_id)
            if table_id is None:
                raise ValueError("Player is not seated at any table")

            table = self.tables[table_id]
            if not table.hand_active:
                raise ValueError("No active hand")

            player = self._current_player(table)
            if player.player_id != player_id:
                raise ValueError("Not your turn")
            if player.packed:
                raise ValueError("Player already packed")

            if action == "pack":
                player.packed = True
            elif action == "see":
                player.seen = True
            elif action in {"call", "raise"}:
                commit = self._compute_commit(table, player, action, amount)
                if player.chips < commit:
                    raise ValueError("Insufficient chips")
                player.chips -= commit
                player.total_bet += commit
                table.pot += commit
                if not player.seen and commit > table.current_bet:
                    table.current_bet = commit
                if player.seen and commit // 2 > table.current_bet:
                    table.current_bet = commit // 2
            elif action == "show":
                self._showdown_on_demand(table, player)
            else:
                raise ValueError("Invalid action")

            table.action_log.append(
                {
                    "event": "action",
                    "player_id": player_id,
                    "action": action,
                    "amount": amount,
                    "at": datetime.utcnow().isoformat(),
                }
            )
            self._advance_turn(table)
            self._maybe_finish_hand(table)
            self._play_bots_until_human_turn(table)
            return self._public_state(table, for_player=player_id)

    def get_table_state(self, table_id: int, for_player: str | None = None) -> dict[str, Any]:
        with self.lock:
            return self._public_state(self.tables[table_id], for_player=for_player)

    def _compute_commit(self, table: TableState, player: SeatPlayer, action: str, amount: int) -> int:
        base = table.current_bet
        if action == "call":
            return base if not player.seen else base * 2

        if player.seen:
            return max(amount, base * 4)
        return max(amount, base * 2)

    def _start_hand(self, table: TableState) -> None:
        table.deck = new_deck()
        table.pot = 0
        table.current_bet = table.boot_amount
        table.hand_active = True
        table.hand_started_at = datetime.utcnow()

        eligible_players = [player for player in table.players if player.chips >= table.boot_amount]
        removed = [player for player in table.players if player.chips < table.boot_amount]
        for player in removed:
            self.user_table.pop(player.player_id, None)

        table.players = eligible_players
        if len(table.players) < 2:
            table.hand_active = False
            table.action_log.append({"event": "hand_cancelled", "reason": "insufficient_eligible_players"})
            return

        for player in table.players:
            player.packed = False
            player.seen = False
            player.total_bet = table.boot_amount
            player.chips -= table.boot_amount
            table.pot += table.boot_amount
            player.cards = [table.deck.pop(), table.deck.pop(), table.deck.pop()]

        table.turn_idx = (table.dealer_idx + 1) % len(table.players)
        table.action_log.append({"event": "hand_start", "at": datetime.utcnow().isoformat(), "pot": table.pot})

    def _current_player(self, table: TableState) -> SeatPlayer:
        return table.players[table.turn_idx]

    def _advance_turn(self, table: TableState) -> None:
        if not table.players:
            return
        for _ in range(len(table.players)):
            table.turn_idx = (table.turn_idx + 1) % len(table.players)
            candidate = table.players[table.turn_idx]
            if not candidate.packed and candidate.chips > 0:
                return

    def _active_players(self, table: TableState) -> list[SeatPlayer]:
        return [player for player in table.players if not player.packed]

    def _showdown_on_demand(self, table: TableState, player: SeatPlayer) -> None:
        active_players = self._active_players(table)
        if len(active_players) != 2:
            raise ValueError("Show action is only allowed with exactly two active players")

        show_cost = table.current_bet if not player.seen else table.current_bet * 2
        if player.chips < show_cost:
            raise ValueError("Insufficient chips for show")

        player.chips -= show_cost
        player.total_bet += show_cost
        table.pot += show_cost

        players_cards = {active.player_id: active.cards for active in active_players}
        winner_id, _ = best_hand(players_cards)
        winner = next(active for active in active_players if active.player_id == winner_id)
        winner.chips += table.pot

        table.action_log.append({"event": "showdown", "winner": winner.player_id, "pot": table.pot})
        table.hand_active = False
        table.dealer_idx = (table.dealer_idx + 1) % len(table.players)

        if len([active for active in table.players if active.chips >= table.boot_amount]) >= 2:
            self._start_hand(table)

    def _maybe_finish_hand(self, table: TableState) -> None:
        active_players = self._active_players(table)
        if len(active_players) != 1:
            return

        winner = active_players[0]
        winner.chips += table.pot
        table.action_log.append({"event": "hand_win", "winner": winner.player_id, "pot": table.pot})
        table.dealer_idx = (table.dealer_idx + 1) % len(table.players)
        table.hand_active = False

        if len([player for player in table.players if player.chips >= table.boot_amount]) >= 2:
            self._start_hand(table)

    def _bot_dominance_score(self, table: TableState, bot: SeatPlayer) -> float:
        """
        Near-unbeatable elite mode:
        Bot evaluates real opponent cards (perfect-information strategy)
        and estimates dominance in current hand.
        """
        active = [p for p in self._active_players(table) if p.player_id != bot.player_id]
        if not active:
            return 1.0

        wins = 0.0
        for opp in active:
            result = compare_hands(bot.cards, opp.cards)
            if result > 0:
                wins += 1.0
            elif result == 0:
                wins += 0.5
        return wins / len(active)

    def _bot_decision(self, table: TableState, bot: SeatPlayer) -> tuple[str, int]:
        active_players = self._active_players(table)
        if len(active_players) == 2:
            bot.seen = True

        dominance = self._bot_dominance_score(table, bot)
        call_commit = self._compute_commit(table, bot, "call", 0)
        raise_commit = self._compute_commit(table, bot, "raise", table.current_bet * 8)

        if bot.chips < call_commit:
            return ("pack", 0)

        # If bot is likely losing badly, cut loss aggressively.
        if dominance < 0.2:
            return ("pack", 0)

        # With two players, trigger decisive showdown when dominating.
        if len(active_players) == 2 and dominance >= 0.95 and bot.chips >= call_commit:
            return ("show", 0)

        # High-confidence hands apply pressure with big raises.
        if dominance >= 0.75 and bot.chips >= raise_commit:
            return ("raise", raise_commit)

        # Mid-confidence hands keep pot control by calling.
        if dominance >= 0.4:
            return ("call", call_commit)

        # Low-confidence fallback: rare bluff otherwise fold.
        if random.random() < 0.05 and bot.chips >= raise_commit:
            return ("raise", raise_commit)
        return ("pack", 0)

    def _play_bots_until_human_turn(self, table: TableState) -> None:
        safety = 0
        while table.hand_active and safety < 40:
            safety += 1
            bot = self._current_player(table)
            if not bot.is_bot:
                break

            action, amount = self._bot_decision(table, bot)
            if action == "pack":
                bot.packed = True
            elif action == "show":
                self._showdown_on_demand(table, bot)
            else:
                commit = self._compute_commit(table, bot, action, amount)
                if bot.chips < commit:
                    bot.packed = True
                else:
                    bot.chips -= commit
                    bot.total_bet += commit
                    table.pot += commit
                    if action == "raise":
                        if not bot.seen and commit > table.current_bet:
                            table.current_bet = commit
                        if bot.seen and commit // 2 > table.current_bet:
                            table.current_bet = commit // 2

            table.action_log.append(
                {
                    "event": "bot_action",
                    "player_id": bot.player_id,
                    "action": action,
                    "amount": amount,
                    "at": datetime.utcnow().isoformat(),
                }
            )

            self._advance_turn(table)
            self._maybe_finish_hand(table)

    def _public_state(self, table: TableState, for_player: str | None) -> dict[str, Any]:
        players = []
        for player in table.players:
            cards = [str(card) for card in player.cards] if (for_player == player.player_id or not table.hand_active) else ["🂠", "🂠", "🂠"]
            players.append(
                {
                    "player_id": player.player_id,
                    "display_name": player.display_name,
                    "chips": player.chips,
                    "seen": player.seen,
                    "packed": player.packed,
                    "is_bot": player.is_bot,
                    "cards": cards,
                    "total_bet": player.total_bet,
                }
            )

        current_player = table.players[table.turn_idx].player_id if table.players and table.hand_active else None
        return {
            "table_id": table.table_id,
            "name": table.name,
            "pot": table.pot,
            "boot_amount": table.boot_amount,
            "current_bet": table.current_bet,
            "hand_active": table.hand_active,
            "current_player": current_player,
            "players": players,
            "action_log": table.action_log[-30:],
        }
