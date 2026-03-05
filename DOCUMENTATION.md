# Tournament Backend Documentation

This document explains the design, algorithms, and data structures used for the "Double Elimination Tennis Tournament" backend.

## Overview

The backend exposes a minimal REST API (built with FastAPI) that allows:

1. Configuring the tournament (number of serves per match, number of players).
2. Randomly pairing active players into singles matches.
3. Reporting match results and updating player statistics.
4. Producing a final leaderboard of eliminated players sorted by their total score.

The tournament follows a **double-elimination** rule: a player is only eliminated after suffering two losses. Matches are singles, so each pairing involves two participants.

## Data Structures

- `Player` (Pydantic model) – represents an individual participant. Fields:
  - `id` (int): unique identifier.
  - `name` (Optional[str]): placeholder for future naming.
  - `total_score` (int): cumulative points earned from matches.
  - `wins`/`losses` (int): counters of match outcomes.
  - `eliminated` (bool): true once losses >= 2.


- `Match` – holds two `Player` instances (singles), a unique `id`, serve count, a `round` number for scheduling, a `bracket` field indicating winner/loser bracket, and a `finished` flag.

- `TournamentConfig` – stores global configuration (serves and player count).

- `TournamentState` – in-memory state manager. It uses:
  - a list for players (`List[Player]`) to represent individual competitors (singles).
  - a dictionary (`Dict[int, Match]`) to map match IDs to match objects for O(1) retrieval.
  - a `rounds` dictionary mapping round numbers to the list of matches scheduled that round, and a `current_round` counter for sequencing.

## Algorithms

### Group Assignment & Scheduling
- Uses Python's built-in `random.shuffle` (Fisher–Yates, O(n)) to permute the list of **active** players.
- Iterates in steps of two to create matches between individual players. When exactly two active players remain a special final match is scheduled instead of requiring four competitors. The operation is linear in the number of players.
- Each invocation represents a new **round**; a simple counter (`current_round`) increments and every `Match` created in that call is tagged with that round number.
- Matches are also assigned a `bracket` label:
  - **winner** bracket if both players have zero losses
  - **loser** bracket if one or both players already have a loss
  - **final** when only two players remain *and* at least one of them has a loss; this ensures the losers‑bracket has been fully resolved before the championship duel.
  This simple classification makes it easy to distinguish winners‑bracket and losers‑bracket pairings in the output. Actual bracket‑specific scheduling logic would be a natural next step.
- Scheduled matches are stored in the `rounds` dictionary so that the backend can later reference or display the history of round pairings.
- Active filtering removes eliminated players (`O(n)`), ensuring only eligible participants remain.

### Reporting Matches
- Lookup match by ID via dictionary (O(1)).
- Validate scores against tournament rules: a winner must reach at least `serves_per_match` points and lead by two (deuce logic).
- Update scores and flags.
- Determine winner/loser using simple comparison (`O(1)`).
- Update each player's statistics; check for elimination on second loss.

### Service Handling (simulation only)
- The `service_change_interval` configuration controls how often service alternates during simulated points. Real API does not track service state, but this parameter can be used for more realistic point-by-point modeling.

### Leaderboard Generation
- Filters the player list for `eliminated == True` (O(n)).
- Sorts by `total_score` ascending (`O(k log k)` for k eliminated players).


## Complexity Summary
- **Setup:** O(p) to create player records.
- **Group generation:** O(p) for shuffle and grouping.
- **Reporting a match:** O(1) updates per player (constant number of players per match).
- **Computing leaderboard:** O(p + k log k) where k ≤ p.

Space complexity is linear in the number of players and matches.

## API Endpoints

- `POST /tournament/setup`
  - Request body: JSON with `serves_per_match` (int), `player_count` (even ≥ 2), and optional `service_change_interval` (int).
  - Request body: JSON with `serves_per_match` (int) and `player_count` (even ≥ 4).
  - Response: confirmation message and initial player list.

- `GET /tournament/groups`
  - Returns a list of upcoming `Match` objects with randomly selected teams.
  - Raises error when configuration is missing or not enough active players remain.

- `POST /tournament/match`
  - Query parameters: `match_id`, `score1`, `score2`.
  - Records the result and updates player stats; handles elimination.

- `GET /tournament/leaderboard` (alias `/leaderboard/losers`)
  - Returns eliminated players sorted by `total_score` (lowest first).
- `GET /tournament/leaderboard/readable`
  - Provides a plain-text, ranked table of the same information suitable for console output or email copy-paste.
- `GET /tournament/leaderboard/losers`
  - Equivalent to `/tournament/leaderboard`.
- `GET /tournament/leaderboard/winners`
  - Returns active (non-eliminated) players sorted by number of wins (descending) then total score.



