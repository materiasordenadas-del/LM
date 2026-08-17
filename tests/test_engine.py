import json
import unittest
from pathlib import Path

from lm_ai.engine import TransferDirector
from lm_ai.models import Club, Player


ROOT = Path(__file__).resolve().parents[1]


class TransferDirectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / "config" / "fl26_1_4.json").open("r", encoding="utf-8") as handle:
            cls.config = json.load(handle)

    def test_midtable_club_cannot_buy_superstar(self):
        buyer = Club(1, "Midtable", "ESP1", 60, 76, 200.0, 500.0, "midtable")
        star = Player(10, "Superstar", 2, "CF", 26, 90, 91, 120.0, 300.0, contract_years=3.0, importance=1.0)
        director = TransferDirector([buyer], [star], self.config)
        self.assertIsNone(director.score_candidate(buyer, star, {"ATT": 1.0}))

    def test_elite_club_rejects_low_quality_prime_player(self):
        buyer = Club(1, "Elite", "ESP1", 95, 88, 200.0, 500.0, "elite")
        player = Player(10, "Random", 2, "RB", 27, 72, 73, 5.0, 40.0)
        director = TransferDirector([buyer], [player], self.config)
        self.assertEqual(director.rejection_reason(buyer, player, 5.0), "quality_too_low")

    def test_missing_position_creates_need(self):
        buyer = Club(1, "Club", "ESP1", 80, 82, 100.0, 250.0, "contender", player_ids=[1, 2, 3])
        players = [
            Player(1, "GK", 1, "GK", 25, 82, 83, 20.0, 80.0),
            Player(2, "CB1", 1, "CB", 25, 82, 83, 20.0, 80.0),
            Player(3, "CB2", 1, "CB", 25, 82, 83, 20.0, 80.0),
        ]
        director = TransferDirector([buyer], players, self.config)
        needs = director.calculate_needs(buyer)
        self.assertGreater(needs["ATT"], needs["CB"])

    def test_same_seed_is_deterministic(self):
        buyer = Club(1, "Club", "ESP1", 85, 84, 100.0, 250.0, "contender")
        candidate = Player(10, "Candidate", 2, "RB", 23, 83, 87, 40.0, 120.0)
        d1 = TransferDirector([buyer], [candidate], self.config, seed=26)
        d2 = TransferDirector([buyer], [candidate], self.config, seed=26)
        p1 = d1.score_candidate(buyer, candidate, {"FB": 0.8})
        p2 = d2.score_candidate(buyer, candidate, {"FB": 0.8})
        self.assertIsNotNone(p1)
        self.assertIsNotNone(p2)
        self.assertAlmostEqual(p1.score, p2.score, places=8)

    def test_player_listed_at_buyer_is_not_treated_as_free_agent(self):
        buyer = Club(1, "Club", "ESP1", 80, 80, 100.0, 200.0, "midtable", player_ids=[10])
        player = Player(10, "Own Player", None, "CMF", 25, 80, 82, 20.0, 80.0)
        director = TransferDirector([buyer], [player], self.config)
        self.assertEqual(director.rejection_reason(buyer, player, 0.0), "already_at_club")

    def test_conflicting_membership_fails_fast(self):
        club_a = Club(1, "A", "ESP1", 80, 80, 100.0, 200.0, player_ids=[10])
        club_b = Club(2, "B", "ESP1", 80, 80, 100.0, 200.0)
        player = Player(10, "Conflict", 2, "CMF", 25, 80, 82, 20.0, 80.0)
        with self.assertRaisesRegex(ValueError, "Conflicting club membership"):
            TransferDirector([club_a, club_b], [player], self.config)

    def test_duplicate_player_ids_fail_fast(self):
        club = Club(1, "Club", "ESP1", 80, 80, 100.0, 200.0)
        p1 = Player(10, "A", None, "CMF", 25, 80, 82, 20.0, 80.0)
        p2 = Player(10, "B", None, "CF", 24, 79, 83, 18.0, 70.0)
        with self.assertRaisesRegex(ValueError, "Duplicate player IDs"):
            TransferDirector([club], [p1, p2], self.config)

    def test_unknown_position_fails_fast(self):
        club = Club(1, "Club", "ESP1", 80, 80, 100.0, 200.0)
        player = Player(10, "Unknown", None, "XYZ", 25, 80, 82, 20.0, 80.0)
        with self.assertRaisesRegex(ValueError, "Unsupported position"):
            TransferDirector([club], [player], self.config)

    def test_partial_weight_override_keeps_defaults(self):
        config = dict(self.config)
        config["weights"] = {"randomness": 0}
        buyer = Club(1, "Club", "ESP1", 80, 80, 100.0, 200.0)
        player = Player(10, "Candidate", None, "CMF", 25, 80, 82, 20.0, 80.0)
        director = TransferDirector([buyer], [player], config)
        proposal = director.score_candidate(buyer, player, {"MID": 0.8})
        self.assertIsNotNone(proposal)

    def test_non_positive_shortlist_limit_is_rejected(self):
        club = Club(1, "Club", "ESP1", 80, 80, 100.0, 200.0)
        player = Player(10, "Candidate", None, "CMF", 25, 80, 82, 20.0, 80.0)
        director = TransferDirector([club], [player], self.config)
        with self.assertRaisesRegex(ValueError, "limit"):
            director.shortlist_for_club(1, limit=0)


if __name__ == "__main__":
    unittest.main()
