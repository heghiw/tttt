from typing import Dict, List
from models import Player, Match, TournamentConfig
import random


class TournamentState:
    def __init__(self):
        self.config: TournamentConfig | None = None
        self.players: List[Player] = []
        self.matches: Dict[int, Match] = {}
        # schedule: map round number to list of matches
        self.rounds: Dict[int, List[Match]] = {}
        self.next_match_id = 1
        self.current_round = 0

    def setup(self, serves_per_match: int, player_count: int, service_change_interval: int = 3):
        self.config = TournamentConfig(serves_per_match=serves_per_match, player_count=player_count,
                                         service_change_interval=service_change_interval)
        # initialize players with sequential ids
        self.players = [Player(id=i + 1, name=None) for i in range(player_count)]
        self.matches.clear()
        self.rounds.clear()
        self.next_match_id = 1
        self.current_round = 0

    def assign_groups(self) -> List[Match]:
        if not self.config:
            raise ValueError("Tournament not configured")
        # exclude eliminated players when generating new groups
        active_players = [p for p in self.players if not p.eliminated]
        if len(active_players) < 4:
            raise ValueError("Not enough active players to form a group")

        # special case: final duel between last two active players **only once
        # at least one of them has already lost** (i.e. loser bracket completed)
        if len(active_players) == 2:
            p1, p2 = active_players
            # postpone final until a loser bracket winner exists
            if p1.losses > 0 or p2.losses > 0:
                bracket = "final"
                self.current_round += 1
                round_num = self.current_round
                match = Match(
                    id=self.next_match_id,
                    player1=p1,
                    player2=p2,
                    serves=self.config.serves_per_match,
                    round=round_num,
                    bracket=bracket,
                )
                self.matches[self.next_match_id] = match
                self.next_match_id += 1
                self.rounds[round_num] = [match]
                return [match]
            # otherwise, do not create a final yet; fall through to pairing logic

        shuffled = active_players.copy()
        random.shuffle(shuffled)
        groups: List[Match] = []

        # schedule: increment round and tag each match
        self.current_round += 1
        round_num = self.current_round

        # singles: pair players two-by-two
        for i in range(0, len(shuffled), 2):
            chunk = shuffled[i : i + 2]
            if len(chunk) < 2:
                break
            p1, p2 = chunk
            # classify bracket: winner if both have zero losses
            bracket = "winner" if (p1.losses == 0 and p2.losses == 0) else "loser"
            match = Match(
                id=self.next_match_id,
                player1=p1,
                player2=p2,
                serves=self.config.serves_per_match,
                round=round_num,
                bracket=bracket,
            )
            self.matches[self.next_match_id] = match
            self.next_match_id += 1
            groups.append(match)
        self.rounds[round_num] = groups
        return groups

    def report_match(self, match_id: int, score1: int, score2: int):
        match = self.matches.get(match_id)
        if not match:
            raise ValueError(f"Match {match_id} not found")
        # enforce deuce rule: winner must have at least serves_per_match points
        # and lead by 2
        if not self.config:
            raise ValueError("Tournament not configured")
        min_points = self.config.serves_per_match
        if not ((score1 >= min_points or score2 >= min_points) and abs(score1 - score2) >= 2):
            raise ValueError("Score does not satisfy serves/minimum+2 rule")
        match.score1 = score1
        match.score2 = score2
        match.finished = True
        # update player stats
        if score1 > score2:
            winner = match.player1
            loser = match.player2
        else:
            winner = match.player2
            loser = match.player1
        winner.wins += 1
        winner.total_score += max(score1, score2)
        loser.losses += 1
        loser.total_score += min(score1, score2)
        if loser.losses >= 2:
            loser.eliminated = True

    def leaderboard(self) -> List[Player]:
        # only show eliminated players in final leaderboard
        eliminated = [p for p in self.players if p.eliminated]
        return sorted(eliminated, key=lambda p: p.total_score)

    def rename_player(self, player_id: int, name: str) -> Player:
        for player in self.players:
            if player.id == player_id:
                player.name = name
                return player
        raise ValueError(f"Player {player_id} not found")

state = TournamentState()
