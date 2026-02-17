from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import random

RANK_ORDER = "23456789TJQKA"
SUITS = ["♠", "♥", "♦", "♣"]
RANK_VALUE = {r: i for i, r in enumerate(RANK_ORDER, start=2)}


@dataclass(frozen=True)
class Card:
    rank: str
    suit: str

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"


def new_deck(seed: int | None = None) -> list[Card]:
    deck = [Card(rank, suit) for rank in RANK_ORDER for suit in SUITS]
    rnd = random.Random(seed)
    rnd.shuffle(deck)
    return deck


def _validate_hand(cards: list[Card]) -> None:
    if len(cards) != 3:
        raise ValueError("Teen Patti hand must contain exactly 3 cards")
    if len(set(cards)) != len(cards):
        raise ValueError("Duplicate cards are not allowed in a hand")


def _is_sequence(values: list[int]) -> bool:
    sorted_values = sorted(values)
    if sorted_values == [2, 3, 14]:
        return True
    return sorted_values[1] == sorted_values[0] + 1 and sorted_values[2] == sorted_values[1] + 1


def _sequence_strength(values: list[int]) -> int:
    sorted_values = sorted(values)
    # International/common Teen Patti table convention:
    # AKQ is highest, A23 is second-highest sequence.
    if sorted_values == [12, 13, 14]:
        return 100
    if sorted_values == [2, 3, 14]:
        return 99
    return max(sorted_values)


def evaluate_hand(cards: list[Card]) -> tuple[int, list[int]]:
    _validate_hand(cards)

    values = [RANK_VALUE[c.rank] for c in cards]
    suits = [c.suit for c in cards]

    counts: dict[int, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1

    is_flush = len(set(suits)) == 1
    is_seq = _is_sequence(values)

    # ranking:
    # 6 trail > 5 pure sequence > 4 sequence > 3 color > 2 pair > 1 high card
    if len(counts) == 1:
        return (6, [values[0]])
    if is_flush and is_seq:
        return (5, [_sequence_strength(values)])
    if is_seq:
        return (4, [_sequence_strength(values)])
    if is_flush:
        return (3, sorted(values, reverse=True))
    if any(freq == 2 for freq in counts.values()):
        pair_value = max(card_value for card_value, freq in counts.items() if freq == 2)
        kicker = max(card_value for card_value, freq in counts.items() if freq == 1)
        return (2, [pair_value, kicker])
    return (1, sorted(values, reverse=True))


def compare_hands(hand_a: list[Card], hand_b: list[Card]) -> int:
    score_a = evaluate_hand(hand_a)
    score_b = evaluate_hand(hand_b)
    if score_a > score_b:
        return 1
    if score_b > score_a:
        return -1
    return 0


def best_hand(players_cards: dict[str, list[Card]]) -> tuple[str, tuple[int, list[int]]]:
    winner_player_id = ""
    winner_score = (0, [0])
    for player_id, cards in players_cards.items():
        score = evaluate_hand(cards)
        if score > winner_score:
            winner_player_id = player_id
            winner_score = score
    return winner_player_id, winner_score


def odds_snapshot(deck: list[Card], known_cards: list[Card], simulations: int = 500) -> float:
    if not known_cards:
        return 0.0
    if len(known_cards) != 3:
        raise ValueError("Known cards must be exactly 3 cards")

    sample_deck = [card for card in deck if card not in known_cards]
    if len(sample_deck) < 3:
        raise ValueError("Deck does not have enough cards for simulation")

    wins = 0
    for _ in range(simulations):
        opponent = random.sample(sample_deck, 3)
        if compare_hands(known_cards, opponent) >= 0:
            wins += 1
    return wins / simulations


def all_two_player_matchups() -> int:
    return len(list(combinations(range(52), 6)))
