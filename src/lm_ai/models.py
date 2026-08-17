from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


POSITION_GROUPS = {
    "GK": "GK",
    "CB": "CB",
    "LB": "FB",
    "RB": "FB",
    "LWB": "FB",
    "RWB": "FB",
    "DMF": "MID",
    "CMF": "MID",
    "AMF": "MID",
    "LMF": "WIDE",
    "RMF": "WIDE",
    "LWF": "WIDE",
    "RWF": "WIDE",
    "SS": "ATT",
    "CF": "ATT",
}


@dataclass(slots=True)
class Player:
    id: int
    name: str
    club_id: int | None
    position: str
    age: int
    overall: int
    potential: int
    value_m: float
    wage_k: float
    nationality: str = ""
    contract_years: float = 2.0
    importance: float = 0.5

    @property
    def group(self) -> str:
        return POSITION_GROUPS.get(self.position.upper(), "MID")


@dataclass(slots=True)
class Club:
    id: int
    name: str
    league: str
    prestige: int
    strength: int
    budget_m: float
    wage_ceiling_k: float
    archetype: str = "midtable"
    european_status: str = "none"
    player_ids: list[int] = field(default_factory=list)


@dataclass(slots=True)
class Proposal:
    buyer_id: int
    player_id: int
    seller_id: int | None
    score: float
    position_need: float
    estimated_fee_m: float
    reasons: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "buyer_id": self.buyer_id,
            "player_id": self.player_id,
            "seller_id": self.seller_id,
            "score": round(self.score, 3),
            "position_need": round(self.position_need, 3),
            "estimated_fee_m": round(self.estimated_fee_m, 2),
            "reasons": self.reasons,
        }
