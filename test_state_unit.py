import unittest

from storage import TournamentState


class TestTournamentState(unittest.TestCase):
    def test_setup_initializes_data_structures(self):
        s = TournamentState()
        s.setup(serves_per_match=11, player_count=8, service_change_interval=3)

        self.assertIsInstance(s.players, list)
        self.assertEqual(len(s.players), 8)
        self.assertIsInstance(s.matches, dict)
        self.assertIsInstance(s.rounds, dict)
        self.assertEqual(s.current_round, 0)
        self.assertEqual(s.next_match_id, 1)

    def test_assign_groups_creates_matches_and_round(self):
        s = TournamentState()
        s.setup(serves_per_match=11, player_count=8, service_change_interval=3)
        groups = s.assign_groups()

        self.assertEqual(s.current_round, 1)
        self.assertEqual(len(groups), 4)  # 8 players -> 4 matches
        self.assertIn(1, s.rounds)
        self.assertEqual(len(s.rounds[1]), 4)
        self.assertEqual(len(s.matches), 4)
        self.assertTrue(all(m.round == 1 for m in groups))
        self.assertTrue(all(m.bracket in ("winner", "loser") for m in groups))

    def test_report_match_updates_stats_and_eliminates_after_two_losses(self):
        s = TournamentState()
        s.setup(serves_per_match=11, player_count=8, service_change_interval=3)
        match = s.assign_groups()[0]

        # Give player2 two losses by reporting the same match twice.
        s.report_match(match.id, 11, 7)
        s.report_match(match.id, 12, 10)

        loser = match.player2 if match.score1 > match.score2 else match.player1
        self.assertGreaterEqual(loser.losses, 2)
        self.assertTrue(loser.eliminated)


if __name__ == "__main__":
    unittest.main()

