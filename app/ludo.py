from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import random
from threading import Lock
from typing import Any

COLORS = ["red", "green", "yellow", "blue"]
TOKENS_PER_PLAYER = 4
BOARD_SIZE = 52
HOME_LENGTH = 6
MAX_STEPS = BOARD_SIZE + HOME_LENGTH - 1
SAFE_SQUARES = {0, 8, 13, 21, 26, 34, 39, 47}


@dataclass
class LudoToken:
    token_id: int
    steps: int = -1

    @property
    def finished(self) -> bool:
        return self.steps >= MAX_STEPS


@dataclass
class LudoPlayer:
    player_id: str
    display_name: str
    color: str
    is_bot: bool = False
    tokens: list[LudoToken] = field(default_factory=list)
    rank: int | None = None


@dataclass
class LudoTable:
    table_id: int
    name: str
    players: list[LudoPlayer] = field(default_factory=list)
    hand_active: bool = False
    turn_idx: int = 0
    dice_value: int | None = None
    pending_move: bool = False
    consecutive_sixes: int = 0
    history: list[dict[str, Any]] = field(default_factory=list)
    winners: list[str] = field(default_factory=list)


class LudoManager:
    def __init__(self) -> None:
        self.tables: dict[int, LudoTable] = {}
        self.user_table: dict[str, int] = {}
        self.next_table_id = 1
        self.lock = Lock()

    def create_table(self, name: str) -> dict[str, Any]:
        with self.lock:
            table = LudoTable(table_id=self.next_table_id, name=name)
            self.tables[self.next_table_id] = table
            self.next_table_id += 1
            return self._state(table, None)

    def list_tables(self) -> list[dict[str, Any]]:
        with self.lock:
            return [
                {"table_id": t.table_id, "name": t.name, "players": len(t.players), "hand_active": t.hand_active}
                for t in self.tables.values()
            ]

    def join_table(self, table_id: int, player_id: str, display_name: str, is_bot: bool = False) -> dict[str, Any]:
        with self.lock:
            table = self.tables[table_id]
            return self._join_table_locked(table, player_id, display_name, is_bot)

    def add_bots(self, table_id: int, count: int) -> dict[str, Any]:
        with self.lock:
            table = self.tables[table_id]
            for _ in range(count):
                if len(table.players) >= 4:
                    break
                bot_id = f"ludo-bot-{table.table_id}-{len(table.players)+1}-{random.randint(1000,9999)}"
                bot_name = random.choice(["Atlas", "Nova", "Titan", "Pulse"]) + " Bot"
                self._join_table_locked(table, bot_id, bot_name, is_bot=True)
            return self._state(table, None)

    def start_game(self, table_id: int) -> dict[str, Any]:
        with self.lock:
            table = self.tables[table_id]
            if len(table.players) != 4:
                raise ValueError("Ludo requires exactly 4 players")
            table.hand_active = True
            table.turn_idx = 0
            table.dice_value = None
            table.pending_move = False
            table.consecutive_sixes = 0
            table.winners = []
            for player in table.players:
                player.rank = None
                player.tokens = [LudoToken(token_id=i) for i in range(TOKENS_PER_PLAYER)]
            table.history.append({"event": "game_start", "at": datetime.utcnow().isoformat()})
            self._auto_play_bots(table)
            return self._state(table, None)

    def roll_dice(self, player_id: str) -> dict[str, Any]:
        with self.lock:
            table, player = self._table_player(player_id)
            self._assert_turn(table, player_id)
            if not table.hand_active:
                raise ValueError("No active game")
            if table.pending_move:
                raise ValueError("Move pending; play a token first")

            dice = random.randint(1, 6)
            table.dice_value = dice
            table.consecutive_sixes = table.consecutive_sixes + 1 if dice == 6 else 0
            table.history.append({"event": "roll", "player_id": player_id, "dice": dice})

            if table.consecutive_sixes >= 3:
                table.history.append({"event": "turn_forfeit", "player_id": player_id, "reason": "three_consecutive_sixes"})
                table.dice_value = None
                table.pending_move = False
                table.consecutive_sixes = 0
                self._advance_turn(table)
                self._auto_play_bots(table)
                return self._state(table, player.player_id)

            movable = self._movable_tokens(table, player, dice)
            if not movable:
                table.dice_value = None
                table.pending_move = False
                table.history.append({"event": "no_move", "player_id": player_id})
                if dice != 6:
                    self._advance_turn(table)
                self._auto_play_bots(table)
                return self._state(table, player.player_id)

            table.pending_move = True
            self._auto_play_bots(table)
            return self._state(table, player.player_id)

    def move_token(self, player_id: str, token_id: int) -> dict[str, Any]:
        with self.lock:
            table, player = self._table_player(player_id)
            self._move_token_locked(table, player, token_id)
            self._auto_play_bots(table)
            return self._state(table, player.player_id)

    def get_state(self, table_id: int, for_player: str | None) -> dict[str, Any]:
        with self.lock:
            table = self.tables.get(table_id)
            if table is None:
                raise KeyError(table_id)
            return self._state(table, for_player)

    def _join_table_locked(self, table: LudoTable, player_id: str, display_name: str, is_bot: bool) -> dict[str, Any]:
        if player_id in self.user_table:
            raise ValueError("Player already joined a Ludo table")
        if table.hand_active:
            raise ValueError("Cannot join during active game")
        if len(table.players) >= 4:
            raise ValueError("Ludo supports exactly 4 players")

        color = COLORS[len(table.players)]
        player = LudoPlayer(
            player_id=player_id,
            display_name=display_name,
            color=color,
            is_bot=is_bot,
            tokens=[LudoToken(token_id=i) for i in range(TOKENS_PER_PLAYER)],
        )
        table.players.append(player)
        self.user_table[player_id] = table.table_id
        table.history.append({"event": "join", "player_id": player_id, "color": color, "at": datetime.utcnow().isoformat()})
        return self._state(table, player_id)

    def _move_token_locked(self, table: LudoTable, player: LudoPlayer, token_id: int) -> None:
        self._assert_turn(table, player.player_id)
        if not table.hand_active:
            raise ValueError("No active game")
        if not table.pending_move or table.dice_value is None:
            raise ValueError("Roll dice first")

        dice = table.dice_value
        token = self._find_token(player, token_id)
        if token not in self._movable_tokens(table, player, dice):
            raise ValueError("Illegal token move")

        prev = token.steps
        token.steps = 0 if token.steps == -1 else token.steps + dice
        captured_ids = self._capture_if_needed(table, player, token)
        reached_home_now = prev < MAX_STEPS and token.steps == MAX_STEPS

        if all(t.finished for t in player.tokens) and player.player_id not in table.winners:
            player.rank = len(table.winners) + 1
            table.winners.append(player.player_id)
            table.history.append({"event": "player_finished", "player_id": player.player_id, "rank": player.rank})

        table.history.append(
            {
                "event": "move",
                "player_id": player.player_id,
                "token_id": token_id,
                "from": prev,
                "to": token.steps,
                "dice": dice,
                "captures": captured_ids,
                "reached_home": reached_home_now,
            }
        )

        table.pending_move = False
        table.dice_value = None

        if len(table.winners) >= 3:
            table.hand_active = False
            table.history.append({"event": "game_end", "winners": table.winners, "at": datetime.utcnow().isoformat()})
            return

        grant_extra_turn = bool(captured_ids) or reached_home_now or dice == 6
        if not grant_extra_turn:
            table.consecutive_sixes = 0
            self._advance_turn(table)

    def _table_player(self, player_id: str) -> tuple[LudoTable, LudoPlayer]:
        table_id = self.user_table.get(player_id)
        if table_id is None:
            raise ValueError("Player is not seated at a Ludo table")
        table = self.tables.get(table_id)
        if table is None:
            raise ValueError("Table not found")
        player = next((p for p in table.players if p.player_id == player_id), None)
        if player is None:
            raise ValueError("Player seat is stale")
        return table, player

    def _assert_turn(self, table: LudoTable, player_id: str) -> None:
        if not table.players or table.players[table.turn_idx].player_id != player_id:
            raise ValueError("Not your turn")

    def _find_token(self, player: LudoPlayer, token_id: int) -> LudoToken:
        for token in player.tokens:
            if token.token_id == token_id:
                return token
        raise ValueError("Invalid token")

    def _movable_tokens(self, table: LudoTable, player: LudoPlayer, dice: int) -> list[LudoToken]:
        movable: list[LudoToken] = []
        blockades = self._blockade_positions(table)
        for token in player.tokens:
            if token.finished:
                continue
            if token.steps == -1:
                if dice != 6:
                    continue
                destination_steps = 0
            else:
                destination_steps = token.steps + dice
                if destination_steps > MAX_STEPS:
                    continue

            if self._path_blocked(table, player, token.steps, destination_steps, blockades):
                continue
            movable.append(token)
        return movable

    def _path_blocked(
        self,
        table: LudoTable,
        player: LudoPlayer,
        start_steps: int,
        destination_steps: int,
        blockades: set[int],
    ) -> bool:
        if destination_steps >= BOARD_SIZE:
            return False

        if start_steps < 0:
            destination_pos = self._board_position_from_steps(player, destination_steps)
            return destination_pos in blockades if destination_pos is not None else False

        # Check every traversed board square including destination for blockade crossing.
        for step in range(start_steps + 1, destination_steps + 1):
            if step >= BOARD_SIZE:
                break
            pos = self._board_position_from_steps(player, step)
            if pos in blockades:
                return True
        return False

    def _capture_if_needed(self, table: LudoTable, mover: LudoPlayer, moved_token: LudoToken) -> list[str]:
        moved_pos = self._board_position(mover, moved_token)
        if moved_pos is None or moved_pos in SAFE_SQUARES:
            return []

        captured_players: list[str] = []
        board_occ = self._occupancy_by_position(table)
        # Blockade (2+ tokens) is protected from capture and should be impossible to land on due to movement validation.
        if len(board_occ.get(moved_pos, [])) > 2:
            return []

        for opponent in table.players:
            if opponent.player_id == mover.player_id:
                continue
            for token in opponent.tokens:
                if token.steps < 0 or token.steps >= BOARD_SIZE:
                    continue
                if self._board_position(opponent, token) == moved_pos:
                    token.steps = -1
                    captured_players.append(opponent.player_id)
        return captured_players

    def _board_position(self, player: LudoPlayer, token: LudoToken) -> int | None:
        return self._board_position_from_steps(player, token.steps)

    def _board_position_from_steps(self, player: LudoPlayer, steps: int) -> int | None:
        if steps < 0 or steps >= BOARD_SIZE:
            return None
        start = COLORS.index(player.color) * 13
        return (start + steps) % BOARD_SIZE

    def _occupancy_by_position(self, table: LudoTable) -> dict[int, list[tuple[str, int]]]:
        occ: dict[int, list[tuple[str, int]]] = {}
        for player in table.players:
            for token in player.tokens:
                pos = self._board_position(player, token)
                if pos is None:
                    continue
                occ.setdefault(pos, []).append((player.player_id, token.token_id))
        return occ

    def _blockade_positions(self, table: LudoTable) -> set[int]:
        occ = self._occupancy_by_position(table)
        return {pos for pos, entries in occ.items() if len(entries) >= 2}

    def _advance_turn(self, table: LudoTable) -> None:
        for _ in range(len(table.players)):
            table.turn_idx = (table.turn_idx + 1) % len(table.players)
            if table.players[table.turn_idx].rank is None:
                return

    def _auto_play_bots(self, table: LudoTable) -> None:
        guard = 0
        while table.hand_active and table.players and table.players[table.turn_idx].is_bot and guard < 120:
            guard += 1
            bot = table.players[table.turn_idx]
            if not table.pending_move:
                dice = random.randint(1, 6)
                table.dice_value = dice
                table.consecutive_sixes = table.consecutive_sixes + 1 if dice == 6 else 0
                table.history.append({"event": "roll", "player_id": bot.player_id, "dice": dice})

                if table.consecutive_sixes >= 3:
                    table.history.append({"event": "turn_forfeit", "player_id": bot.player_id, "reason": "three_consecutive_sixes"})
                    table.consecutive_sixes = 0
                    table.dice_value = None
                    table.pending_move = False
                    self._advance_turn(table)
                    continue

                movable = self._movable_tokens(table, bot, dice)
                if not movable:
                    table.history.append({"event": "no_move", "player_id": bot.player_id})
                    table.dice_value = None
                    table.pending_move = False
                    if dice != 6:
                        self._advance_turn(table)
                    continue

                table.pending_move = True

            assert table.dice_value is not None
            move = self._choose_bot_move(table, bot, table.dice_value)
            self._move_token_locked(table, bot, move.token_id)

    def _choose_bot_move(self, table: LudoTable, bot: LudoPlayer, dice: int) -> LudoToken:
        candidates = self._movable_tokens(table, bot, dice)

        def score(token: LudoToken) -> tuple[int, int, int, int, int]:
            enter_bonus = 1 if token.steps == -1 and dice == 6 else 0
            finish_bonus = 1 if token.steps >= 0 and token.steps + dice == MAX_STEPS else 0
            capture_bonus = 1 if self._would_capture(table, bot, token, dice) else 0
            blockade_break_bonus = 1 if token.steps >= 0 and self._board_position(bot, token) in self._blockade_positions(table) else 0
            progress_bonus = token.steps
            return (finish_bonus, capture_bonus, blockade_break_bonus, enter_bonus, progress_bonus)

        return max(candidates, key=score)

    def _would_capture(self, table: LudoTable, player: LudoPlayer, token: LudoToken, dice: int) -> bool:
        new_steps = 0 if token.steps == -1 else token.steps + dice
        if new_steps >= BOARD_SIZE:
            return False
        target = (COLORS.index(player.color) * 13 + new_steps) % BOARD_SIZE
        if target in SAFE_SQUARES:
            return False

        occ = self._occupancy_by_position(table).get(target, [])
        if len(occ) >= 2:
            return False
        return any(pid != player.player_id for pid, _ in occ)

    def _movable_token_ids_for_player(self, table: LudoTable, for_player: str | None) -> list[int]:
        if not table.pending_move or table.dice_value is None or not for_player:
            return []
        player = next((p for p in table.players if p.player_id == for_player), None)
        if player is None:
            return []
        return [t.token_id for t in self._movable_tokens(table, player, table.dice_value)]

    def _state(self, table: LudoTable, for_player: str | None) -> dict[str, Any]:
        return {
            "table_id": table.table_id,
            "name": table.name,
            "hand_active": table.hand_active,
            "turn_player": table.players[table.turn_idx].player_id if table.players else None,
            "dice_value": table.dice_value,
            "pending_move": table.pending_move,
            "winners": table.winners,
            "blockades": sorted(self._blockade_positions(table)),
            "players": [
                {
                    "player_id": p.player_id,
                    "display_name": p.display_name,
                    "color": p.color,
                    "is_bot": p.is_bot,
                    "rank": p.rank,
                    "tokens": [
                        {
                            "token_id": t.token_id,
                            "steps": t.steps,
                            "finished": t.finished,
                            "board_position": self._board_position(p, t),
                        }
                        for t in p.tokens
                    ],
                }
                for p in table.players
            ],
            "movable_tokens": self._movable_token_ids_for_player(table, for_player),
            "history": table.history[-80:],
        }
