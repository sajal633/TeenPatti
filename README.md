# Teen Patti Pro Arena

A full-stack multiplayer Teen Patti + Twenty-Nine (29) + Ludo platform with:

- Real-time lobby and table gameplay
- User profile management
- Admin panel with bot injection and platform overview
- 120 seeded tables with tiered stakes
- Dedicated Twenty-Nine (29) trick-taking game tables
- International-rules Ludo tables (4-player, capture, safe-squares, home-lane finish)
- Teen Patti hand ranking engine and elite bot intelligence turns

## Tech Stack

- FastAPI + SQLAlchemy + SQLite
- WebSocket for live table updates
- Vanilla JS modern UI

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open: `http://127.0.0.1:8000`

## Default Admin

- username: `admin`
- password: `Admin@12345`

## API Domains

- `/api/auth/*` registration and login
- `/api/profile/*` player profile
- `/api/lobby/*` discover 100+ tables
- `/api/game/*` join and action endpoints
- `/api/admin/*` admin insights and bot controls
- `/api/twentynine/*` create/join/start/bid/play/state for 29 game
- `/api/ludo/*` create/join/start/roll/move/state for Ludo game

## Teen Patti Rules Implemented

- 52-card deck, 3 cards per player
- Boot ante at hand start
- Blind/seen state and betting impact
- Pack/call/raise/see/show actions
- Winner by fold elimination or showdown comparison
- Hand ranking order:
  1. Trail (three of a kind)
  2. Pure sequence (straight flush)
  3. Sequence (straight, with A-2-3 above K-Q-J by common table convention)
  4. Color (flush)
  5. Pair
  6. High card

## Test

```bash
pytest -q
```


## Ludo Rules Implemented

- 4 players, 4 tokens per player.
- Entry from yard requires rolling 6.
- Three consecutive sixes forfeit the turn.
- Exact roll required to finish in home lane.
- Safe squares protect from capture.
- Capturing an opponent grants an extra turn.
- Reaching home with a token grants an extra turn.
- Blockade/double-token squares are created automatically and cannot be crossed.
- Capture-chain opportunities are supported via bonus turns.
