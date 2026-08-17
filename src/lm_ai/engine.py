from __future__ import annotations

import hashlib
import random
from statistics import mean
from typing import Iterable

from .models import Club, Player, Proposal


DEFAULT_TARGETS = {"GK": 2, "CB": 4, "FB": 4, "MID": 5, "WIDE": 4, "ATT": 3}
DEFAULT_STARTERS = {"GK": 1, "CB": 2, "FB": 2, "MID": 3, "WIDE": 2, "ATT": 1}
DEFAULT_WEIGHTS = {
    "need": 30,
    "quality": 20,
    "potential": 15,
    "affordability": 10,
    "prestige": 10,
    "age": 5,
    "market_fit": 5,
    "randomness": 5,
}


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _stable_rng(seed: int, club_id: int, player_id: int) -> random.Random:
    raw = f"{seed}:{club_id}:{player_id}".encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    return random.Random(int.from_bytes(digest[:8], "little"))


def estimate_fee(player: Player) -> float:
    """Simple negotiation estimate. This is intentionally replaceable later by ML memory data."""
    if player.club_id is None:
        return 0.0
    contract_factor = 0.85 + 0.18 * min(max(player.contract_years, 0.0), 5.0)
    importance_factor = 0.90 + 0.35 * _clamp(player.importance)
    return round(player.value_m * contract_factor * importance_factor, 2)


class TransferDirector:
    def __init__(self, clubs: Iterable[Club], players: Iterable[Player], config: dict, seed: int = 26):
        club_list = list(clubs)
        player_list = list(players)

        club_ids = [club.id for club in club_list]
        player_ids = [player.id for player in player_list]
        if len(club_ids) != len(set(club_ids)):
            raise ValueError("Duplicate club IDs detected in world snapshot")
        if len(player_ids) != len(set(player_ids)):
            raise ValueError("Duplicate player IDs detected in world snapshot")

        self.clubs = {club.id: club for club in club_list}
        self.players = {player.id: player for player in player_list}
        self.config = config
        self.seed = seed

        # Build a second membership index from Club.player_ids. We keep both sources
        # because the future FL26 inspector may expose roster membership separately
        # from the player's club field. Contradictions must fail loudly.
        self._listed_club_by_player: dict[int, int] = {}
        for club in club_list:
            seen_in_club: set[int] = set()
            for player_id in club.player_ids:
                if player_id in seen_in_club:
                    raise ValueError(f"Player {player_id} appears twice in {club.name}'s player_ids")
                seen_in_club.add(player_id)

                if player_id not in self.players:
                    raise ValueError(
                        f"Club {club.id} ({club.name}) references unknown player ID {player_id}"
                    )
                previous_club = self._listed_club_by_player.get(player_id)
                if previous_club is not None and previous_club != club.id:
                    raise ValueError(
                        f"Player {player_id} is listed in multiple clubs: {previous_club} and {club.id}"
                    )
                self._listed_club_by_player[player_id] = club.id

        for player in player_list:
            # Validate position mapping now rather than silently corrupting squad needs later.
            _ = player.group
            listed_club = self._listed_club_by_player.get(player.id)
            if listed_club is not None and player.club_id is not None and player.club_id != listed_club:
                raise ValueError(
                    f"Conflicting club membership for player {player.id} ({player.name}): "
                    f"club_id={player.club_id}, player_ids says {listed_club}"
                )

    def _belongs_to_club(self, club: Club, player: Player) -> bool:
        return player.club_id == club.id or self._listed_club_by_player.get(player.id) == club.id

    def squad(self, club: Club) -> list[Player]:
        return [player for player in self.players.values() if self._belongs_to_club(club, player)]

    def calculate_needs(self, club: Club) -> dict[str, float]:
        targets = dict(DEFAULT_TARGETS)
        targets.update(self.config.get("roster_targets", {}))
        starters = dict(DEFAULT_STARTERS)
        starters.update(self.config.get("starter_slots", {}))

        squad = self.squad(club)
        grouped: dict[str, list[Player]] = {group: [] for group in targets}
        for player in squad:
            grouped.setdefault(player.group, []).append(player)

        needs: dict[str, float] = {}
        for group, target in targets.items():
            group_players = sorted(grouped.get(group, []), key=lambda p: p.overall, reverse=True)
            count = len(group_players)
            depth_deficit = _clamp((target - count) / max(target, 1))

            starter_count = min(starters.get(group, 1), len(group_players))
            if starter_count == 0:
                quality_deficit = 1.0
            else:
                current_quality = mean(p.overall for p in group_players[:starter_count])
                desired_quality = max(60.0, club.strength - 2.0)
                quality_deficit = _clamp((desired_quality - current_quality) / 10.0)

            need = 0.68 * depth_deficit + 0.32 * quality_deficit
            needs[group] = round(_clamp(max(0.03, need)), 4)
        return needs

    def _age_fit(self, club: Club, player: Player) -> float:
        archetype_ranges = self.config.get("age_ranges", {})
        low, high = archetype_ranges.get(club.archetype, [20, 29])
        if low <= player.age <= high:
            return 1.0
        distance = min(abs(player.age - low), abs(player.age - high))
        return _clamp(1.0 - distance / 10.0)

    def _required_prestige(self, player: Player) -> float:
        # OVR 75 ~= prestige 50, OVR 85 ~= 80, OVR 90 ~= 95.
        return max(35.0, min(96.0, 35.0 + (player.overall - 70.0) * 3.0))

    def rejection_reason(self, buyer: Club, player: Player, fee_m: float) -> str | None:
        gates = self.config.get("hard_gates", {})
        if self._belongs_to_club(buyer, player):
            return "already_at_club"
        if player.age > gates.get("max_age", 37):
            return "age_ceiling"
        if fee_m > buyer.budget_m * gates.get("max_budget_ratio", 1.05):
            return "unaffordable_fee"
        if player.wage_k > buyer.wage_ceiling_k * gates.get("max_wage_ratio", 1.15):
            return "wage_structure"

        star_ovr = gates.get("star_ovr", 86)
        star_min_prestige = gates.get("star_min_prestige", 72)
        if player.overall >= star_ovr and buyer.prestige < star_min_prestige:
            # Older free-agent stars may realistically step down a level.
            if not (player.club_id is None and player.age >= 31 and buyer.prestige >= star_min_prestige - 12):
                return "club_not_attractive_enough_for_star"

        quality_floor = buyer.strength - gates.get("max_quality_drop", 10)
        prospect_exception = player.age <= 21 and player.potential >= buyer.strength + 4
        developer_exception = buyer.archetype == "developer" and player.age <= 23 and player.potential >= buyer.strength
        if player.overall < quality_floor and not prospect_exception and not developer_exception:
            return "quality_too_low"

        # A mid/low-prestige club should almost never strip an important prime player
        # from a substantially bigger club just because it happens to have money.
        if player.club_id is not None and player.club_id in self.clubs:
            seller = self.clubs[player.club_id]
            prestige_gap = seller.prestige - buyer.prestige
            if (
                prestige_gap >= gates.get("seller_prestige_gap", 22)
                and player.importance >= gates.get("protected_importance", 0.72)
                and player.contract_years > 1.0
                and player.age <= 30
            ):
                return "seller_and_player_above_buyer_level"
        return None

    def score_candidate(self, buyer: Club, player: Player, needs: dict[str, float]) -> Proposal | None:
        fee_m = estimate_fee(player)
        rejected = self.rejection_reason(buyer, player, fee_m)
        if rejected:
            return None

        weights = dict(DEFAULT_WEIGHTS)
        weights.update(self.config.get("weights", {}))
        need = needs.get(player.group, 0.03)

        desired = buyer.strength + (2 if buyer.archetype in {"elite", "contender"} else 0)
        quality_fit = _clamp(1.0 - abs(player.overall - desired) / 16.0)

        potential_gain = max(0, player.potential - player.overall)
        potential_fit = _clamp((potential_gain / 12.0) + (0.25 if player.age <= 21 else 0.0))
        if buyer.archetype == "developer":
            potential_fit = _clamp(potential_fit * 1.25)

        if fee_m <= 0.0:
            affordability = 1.0
        else:
            affordability = _clamp(1.0 - fee_m / max(buyer.budget_m, 1.0))

        required_prestige = self._required_prestige(player)
        prestige_fit = _clamp(buyer.prestige / max(required_prestige, 1.0))
        age_fit = self._age_fit(buyer, player)

        market_fit = 0.55
        if player.club_id is None:
            market_fit += 0.20
        elif player.club_id in self.clubs and self.clubs[player.club_id].league == buyer.league:
            market_fit += 0.15
        if player.contract_years <= 1.0:
            market_fit += 0.15
        market_fit = _clamp(market_fit)

        rng = _stable_rng(self.seed, buyer.id, player.id)
        randomness = rng.uniform(0.0, 1.0)

        score = (
            weights["need"] * need
            + weights["quality"] * quality_fit
            + weights["potential"] * potential_fit
            + weights["affordability"] * affordability
            + weights["prestige"] * prestige_fit
            + weights["age"] * age_fit
            + weights["market_fit"] * market_fit
            + weights["randomness"] * randomness
        )

        reasons = [f"{player.group}_need={need:.2f}"]
        if quality_fit >= 0.8:
            reasons.append("quality_matches_club")
        if potential_fit >= 0.75:
            reasons.append("strong_development_upside")
        if player.contract_years <= 1.0:
            reasons.append("contract_opportunity")
        if affordability >= 0.75:
            reasons.append("financially_accessible")
        if prestige_fit < 0.7:
            reasons.append("prestige_stretch")

        return Proposal(
            buyer_id=buyer.id,
            player_id=player.id,
            seller_id=player.club_id,
            score=score,
            position_need=need,
            estimated_fee_m=fee_m,
            reasons=reasons,
        )

    def shortlist_for_club(self, club_id: int, limit: int = 8) -> list[Proposal]:
        if limit < 1:
            raise ValueError("shortlist limit must be >= 1")
        club = self.clubs[club_id]
        needs = self.calculate_needs(club)
        proposals = []
        for player in self.players.values():
            proposal = self.score_candidate(club, player, needs)
            if proposal is not None:
                proposals.append(proposal)
        proposals.sort(key=lambda p: (p.score, p.position_need), reverse=True)
        return proposals[:limit]

    def generate_market(self, limit_per_club: int = 5) -> dict:
        if limit_per_club < 1:
            raise ValueError("limit_per_club must be >= 1")
        result = {"seed": self.seed, "clubs": {}}
        for club in sorted(self.clubs.values(), key=lambda c: (-c.prestige, c.id)):
            needs = self.calculate_needs(club)
            shortlist = self.shortlist_for_club(club.id, limit=limit_per_club)
            result["clubs"][str(club.id)] = {
                "name": club.name,
                "archetype": club.archetype,
                "needs": needs,
                "shortlist": [proposal.as_dict() for proposal in shortlist],
            }
        return result
