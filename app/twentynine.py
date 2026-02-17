from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import random
from threading import Lock
from typing import Any

RANKS = ["J", "9", "A", "10", "K", "Q", "8", "7"]
SUITS = ["S", "H", "D", "C"]
RANK_POINTS = {"J": 3, "9": 2, "A": 1, "10": 1, "K": 0, "Q": 0, "8": 0, "7": 0}


@dataclass(frozen=True)
class T29Card:
    rank: str
    suit: str

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"


@dataclass
class T29Player:
    player_id: str
    display_name: str
    is_bot: bool = False
    hand: list[T29Card] = field(default_factory=list)


@dataclass
class T29Table:
    table_id: int
    name: str
    players: list[T29Player] = field(default_factory=list)
    hand_active: bool = False
    bids: dict[str, int] = field(default_factory=dict)
    highest_bid: int = 16
    highest_bidder: str | None = None
    trump_suit: str | None = None
    turn_idx: int = 0
    lead_suit: str | None = None
    trick_cards: list[tuple[str, T29Card]] = field(default_factory=list)
    won_tricks: dict[str, int] = field(default_factory=dict)
    team_points: dict[int, int] = field(default_factory=lambda: {0: 0, 1: 0})
    history: list[dict[str, Any]] = field(default_factory=list)
    deck: list[T29Card] = field(default_factory=list)
    hand_started_at: datetime | None = None


class TwentyNineManager:
    def __init__(self) -> None:
        self.tables: dict[int, T29Table] = {}
        self.user_table: dict[str, int] = {}
        self.next_table_id = 1
        self.lock = Lock()

    def create_table(self, name: str) -> dict[str, Any]:
        with self.lock:
            table = T29Table(table_id=self.next_table_id, name=name)
            self.tables[self.next_table_id] = table
            self.next_table_id += 1
            return self._state(table, None)

    def list_tables(self) -> list[dict[str, Any]]:
        with self.lock:
            return [
                {
                    "table_id": t.table_id,
                    "name": t.name,
                    "players": len(t.players),
                    "hand_active": t.hand_active,
                    "highest_bid": t.highest_bid,
                }
                for t in self.tables.values()
            ]

    def join_table(self, table_id: int, player_id: str, display_name: str, is_bot: bool = False) -> dict[str, Any]:
        with self.lock:
            if player_id in self.user_table:
                raise ValueError("Player already joined a table")
            table = self.tables[table_id]
            if len(table.players) >= 4:
                raise ValueError("Twenty-Nine table is full")
            table.players.append(T29Player(player_id=player_id, display_name=display_name, is_bot=is_bot))
            self.user_table[player_id] = table_id
            table.won_tricks[player_id] = 0
            table.history.append({"event": "join", "player_id": player_id, "at": datetime.utcnow().isoformat()})
            return self._state(table, player_id)

    def add_bots(self, table_id: int, count: int) -> dict[str, Any]:
        with self.lock:
            table = self.tables[table_id]
            for _ in range(count):
                if len(table.players) >= 4:
                    break
                bot_id = f"t29-bot-{table_id}-{len(table.players)+1}-{random.randint(1000,9999)}"
                bot_name = random.choice(["Orion", "Nova", "Alpha", "Sigma"]) + " Bot"
                table.players.append(T29Player(player_id=bot_id, display_name=bot_name, is_bot=True))
                self.user_table[bot_id] = table_id
                table.won_tricks[bot_id] = 0
            return self._state(table, None)

    def start_hand(self, table_id: int) -> dict[str, Any]:
        with self.lock:
            table = self.tables[table_id]
            if len(table.players) != 4:
                raise ValueError("Twenty-Nine needs exactly 4 players")

            table.deck = [T29Card(rank=r, suit=s) for s in SUITS for r in RANKS]
            random.shuffle(table.deck)
            for p in table.players:
                p.hand = sorted([table.deck.pop() for _ in range(8)], key=lambda c: (SUITS.index(c.suit), RANKS.index(c.rank)))
            table.hand_active = True
            table.bids = {}
            table.highest_bid = 16
            table.highest_bidder = None
            table.trump_suit = None
            table.turn_idx = 0
            table.team_points = {0: 0, 1: 0}
            table.trick_cards = []
            table.lead_suit = None
            table.hand_started_at = datetime.utcnow()
            table.history.append({"event": "hand_start", "at": datetime.utcnow().isoformat()})
            self._auto_bid_if_bots(table)
            return self._state(table, None)

    def bid(self, player_id: str, amount: int, trump_suit: str) -> dict[str, Any]:
        with self.lock:
            table = self.tables[self.user_table[player_id]]
            if amount <= table.highest_bid or amount > 29:
                raise ValueError("Invalid bid")
            if trump_suit not in SUITS:
                raise ValueError("Invalid trump suit")
            table.bids[player_id] = amount
            table.highest_bid = amount
            table.highest_bidder = player_id
            table.trump_suit = trump_suit
            table.history.append({"event": "bid", "player_id": player_id, "amount": amount, "trump": trump_suit})
            self._auto_bid_if_bots(table)
            return self._state(table, player_id)

    def play_card(self, player_id: str, card_repr: str) -> dict[str, Any]:
        with self.lock:
            table = self.tables[self.user_table[player_id]]
            if not table.hand_active:
                raise ValueError("No active hand")
            current = table.players[table.turn_idx]
            if current.player_id != player_id:
                raise ValueError("Not your turn")

            card = self._parse_card(card_repr)
            player = current
            if card not in player.hand:
                raise ValueError("Card not in hand")

            if table.lead_suit and card.suit != table.lead_suit:
                if any(c.suit == table.lead_suit for c in player.hand):
                    raise ValueError("Must follow lead suit")

            player.hand.remove(card)
            if not table.lead_suit:
                table.lead_suit = card.suit
            table.trick_cards.append((player_id, card))
            table.history.append({"event": "play", "player_id": player_id, "card": str(card)})

            if len(table.trick_cards) == 4:
                self._finish_trick(table)
            else:
                table.turn_idx = (table.turn_idx + 1) % 4

            self._auto_play_bots(table)
            return self._state(table, player_id)

    def get_state(self, table_id: int, for_player: str | None = None) -> dict[str, Any]:
        with self.lock:
            return self._state(self.tables[table_id], for_player)

    def _parse_card(self, card_repr: str) -> T29Card:
        if len(card_repr) < 2:
            raise ValueError("Invalid card format")
        rank = card_repr[:-1]
        suit = card_repr[-1]
        return T29Card(rank=rank, suit=suit)

    def _card_strength(self, card: T29Card, lead_suit: str, trump: str) -> tuple[int, int]:
        if card.suit == trump:
            return (3, -RANKS.index(card.rank))
        if card.suit == lead_suit:
            return (2, -RANKS.index(card.rank))
        return (1, -RANKS.index(card.rank))

    def _team_idx(self, seat_idx: int) -> int:
        return seat_idx % 2

    def _finish_trick(self, table: T29Table) -> None:
        assert table.trump_suit is not None
        assert table.lead_suit is not None
        winner_pid, winner_card = max(
            table.trick_cards,
            key=lambda entry: self._card_strength(entry[1], table.lead_suit or "S", table.trump_suit or "S"),
        )
        winner_seat = next(i for i, p in enumerate(table.players) if p.player_id == winner_pid)
        points = sum(RANK_POINTS[c.rank] for _, c in table.trick_cards)
        table.team_points[self._team_idx(winner_seat)] += points
        table.won_tricks[winner_pid] += 1
        table.history.append({"event": "trick_win", "winner": winner_pid, "points": points, "winning_card": str(winner_card)})

        table.trick_cards = []
        table.lead_suit = None
        table.turn_idx = winner_seat

        if all(len(p.hand) == 0 for p in table.players):
            self._finish_hand(table)

    def _finish_hand(self, table: T29Table) -> None:
        table.hand_active = False
        if table.highest_bidder is None:
            table.history.append({"event": "hand_end", "result": "no_bid"})
            return

        bidder_seat = next(i for i, p in enumerate(table.players) if p.player_id == table.highest_bidder)
        bidder_team = self._team_idx(bidder_seat)
        bidder_points = table.team_points[bidder_team]
        success = bidder_points >= table.highest_bid
        table.history.append(
            {
                "event": "hand_end",
                "bidder": table.highest_bidder,
                "bid": table.highest_bid,
                "bidder_team_points": bidder_points,
                "contract_made": success,
            }
        )

    def _auto_bid_if_bots(self, table: T29Table) -> None:
        if not table.hand_active:
            return
        for p in table.players:
            if not p.is_bot:
                continue
            strength = self._estimate_hand_strength(p.hand)
            target = min(29, max(table.highest_bid + 1, 16 + int(strength * 13)))
            if target > table.highest_bid:
                trump = self._best_trump(p.hand)
                table.bids[p.player_id] = target
                table.highest_bid = target
                table.highest_bidder = p.player_id
                table.trump_suit = trump
                table.history.append({"event": "bot_bid", "player_id": p.player_id, "amount": target, "trump": trump})

        if table.trump_suit is None:
            first = table.players[0]
            table.highest_bidder = first.player_id
            table.trump_suit = self._best_trump(first.hand)

    def _estimate_hand_strength(self, hand: list[T29Card]) -> float:
        points = sum(RANK_POINTS[c.rank] for c in hand)
        suit_density = max(sum(1 for c in hand if c.suit == s) for s in SUITS)
        return min(1.0, (points / 28.0) * 0.75 + (suit_density / 8.0) * 0.25)

    def _best_trump(self, hand: list[T29Card]) -> str:
        return max(SUITS, key=lambda s: sum(RANK_POINTS[c.rank] + 0.25 for c in hand if c.suit == s))

    def _auto_play_bots(self, table: T29Table) -> None:
        if not table.hand_active:
            return
        loop = 0
        while table.hand_active and loop < 20:
            loop += 1
            player = table.players[table.turn_idx]
            if not player.is_bot:
                break
            card = self._elite_choose_card(table, player)
            player.hand.remove(card)
            if table.lead_suit is None:
                table.lead_suit = card.suit
            table.trick_cards.append((player.player_id, card))
            table.history.append({"event": "bot_play", "player_id": player.player_id, "card": str(card)})

            if len(table.trick_cards) == 4:
                self._finish_trick(table)
            else:
                table.turn_idx = (table.turn_idx + 1) % 4

    def _elite_choose_card(self, table: T29Table, bot: T29Player) -> T29Card:
        legal = self._legal_cards(table, bot)
        # Perfect-information greedy minimax-lite:
        # maximize trick-winning probability first, then preserve point cards if cannot win.
        if table.lead_suit is None:
            return max(legal, key=lambda c: (RANK_POINTS[c.rank], c.suit == table.trump_suit, -RANKS.index(c.rank)))

        assert table.trump_suit is not None
        current_winner = max(
            table.trick_cards,
            key=lambda entry: self._card_strength(entry[1], table.lead_suit or "S", table.trump_suit or "S"),
        )
        winning_cards = [
            c
            for c in legal
            if self._card_strength(c, table.lead_suit, table.trump_suit)
            > self._card_strength(current_winner[1], table.lead_suit, table.trump_suit)
        ]

        if winning_cards:
            # Win with lowest sufficient winner to save higher trumps.
            return min(winning_cards, key=lambda c: (RANKS.index(c.rank), RANK_POINTS[c.rank]))

        # Can't win: dump lowest value card.
        return min(legal, key=lambda c: (RANK_POINTS[c.rank], RANKS.index(c.rank)))

    def _legal_cards(self, table: T29Table, player: T29Player) -> list[T29Card]:
        if table.lead_suit is None:
            return list(player.hand)
        same_suit = [c for c in player.hand if c.suit == table.lead_suit]
        return same_suit if same_suit else list(player.hand)

    def _state(self, table: T29Table, for_player: str | None) -> dict[str, Any]:
        players: list[dict[str, Any]] = []
        for p in table.players:
            cards = [str(c) for c in p.hand] if p.player_id == for_player else ["XX"] * len(p.hand)
            players.append(
                {
                    "player_id": p.player_id,
                    "display_name": p.display_name,
                    "is_bot": p.is_bot,
                    "hand": cards,
                    "won_tricks": table.won_tricks.get(p.player_id, 0),
                }
            )

        return {
            "table_id": table.table_id,
            "name": table.name,
            "hand_active": table.hand_active,
            "highest_bid": table.highest_bid,
            "highest_bidder": table.highest_bidder,
            "trump_suit": table.trump_suit,
            "team_points": table.team_points,
            "turn_player": table.players[table.turn_idx].player_id if table.players and table.hand_active else None,
            "players": players,
            "trick_cards": [{"player_id": pid, "card": str(card)} for pid, card in table.trick_cards],
            "history": table.history[-40:],
        }
