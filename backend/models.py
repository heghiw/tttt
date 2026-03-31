from typing import List, Optional
from pydantic import BaseModel


class Player(BaseModel):
    id: int
    name: Optional[str]
    total_score: int = 0
    wins: int = 0
    losses: int = 0
    eliminated: bool = False  # true after two losses (double elimination)


# for singles tournament we no longer use a Team wrapper

class Match(BaseModel):
    id: int
    player1: Player
    player2: Player
    score1: int = 0
    score2: int = 0
    serves: Optional[int] = None
    round: Optional[int] = None  # scheduling round number
    bracket: Optional[str] = None  # 'winner' or 'loser' bracket match
    finished: bool = False


class TournamentConfig(BaseModel):
    serves_per_match: int
    player_count: int
    service_change_interval: int = 3  # change serving player every N points

    # could be extended with more tournament rules in future

