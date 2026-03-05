"""Simple simulation script that runs a tournament with random scores."""
import random
from tt_new.storage import state


def run_simulation(serves: int, players: int):
    state.setup(serves, players)
    print(f"Setup tournament with {players} players, {serves} serves per match")

    round_num = 0
    while True:
        try:
            groups = state.assign_groups()
        except ValueError as e:
            print("No more groups can be formed:", e)
            break
        round_num += 1
        print(f"\n--- Round {round_num} ({len(groups)} matches) ---")
        for match in groups:
            # simulate point-by-point with deuce and service changes
            score1 = 0
            score2 = 0
            server = match.player1.id  # track which player is serving
            serve_count = 0
            interval = state.config.service_change_interval if state.config else serves
            while True:
                # random point
                if random.random() < 0.5:
                    score1 += 1
                else:
                    score2 += 1
                serve_count += 1
                if serve_count >= interval:
                    # swap server
                    server = match.player2.id if server == match.player1.id else match.player1.id
                    serve_count = 0
                # check for end condition
                if (score1 >= serves or score2 >= serves) and abs(score1 - score2) >= 2:
                    break
            print(f"Match {match.id} players {match.player1.id} vs {match.player2.id}: {score1}-{score2} (final)")
            state.report_match(match.id, score1, score2)
        print("Leaderboard so far (eliminated):")
        for p in state.leaderboard():
            print(f"  player {p.id} losses={p.losses} score={p.total_score}")

    print("\nFinal leaderboard:")
    for p in state.leaderboard():
        print(f"  player {p.id} losses={p.losses} score={p.total_score}")


if __name__ == '__main__':
    # default parameters
    run_simulation(serves=11, players=12)
