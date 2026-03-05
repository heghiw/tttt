# Double Elimination Tennis Tournament Backend

This is a simple FastAPI backend for tracking a double-elimination table tennis (singles) tournament.

## Features

- Configure number of serves per match and number of players
- Randomly pair players for singles matches
- Record match results
- Compute a leaderboard of eliminated players sorted by total score (double elimination)

For an in-depth discussion of the algorithms and data structures used in this semestral project, see [DOCUMENTATION.md](DOCUMENTATION.md).

## Run Locally

1. (Recommended) Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   ```
   Activate it:
   - Windows (PowerShell): `.venv\Scripts\Activate.ps1`
   - macOS/Linux: `source .venv/bin/activate`

2. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```

3. Start the server from the repository root:
   ```bash
   python -m uvicorn main:app --reload
   ```

4. Open:
   - UI: `http://localhost:8000/`
   - API docs (Swagger): `http://localhost:8000/docs`

5. (Optional) Run the included smoke test to exercise the API:
   ```bash
   python test_tournament.py
   ```

## API Endpoints

- `GET /` - open the simple HTML web interface for setup, viewing groups, reporting match scores and leaderboards.
- `POST /tournament/setup` - initialize tournament configuration (supports `service_change_interval`).
- `GET  /tournament/groups` - get random player pairings for the next round (singles). Each match now includes `player1`, `player2`, a `round` number, and `bracket`.
- `POST /tournament/match` - report score for a match. Scores must meet the deuce rule: at least the configured number of serves and two-point margin.
- `GET  /tournament/leaderboard` - retrieve current leaderboard of losers.
- `GET  /tournament/leaderboard/readable` - text table of losers' leaderboard.
- `GET  /tournament/leaderboard/losers` - alias for the same losers list.
- `GET  /tournament/leaderboard/winners` - retrieve list of active players sorted by wins.

