from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import TransferDirector
from .models import Club, Player


def _load_json(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_world(path: str | Path) -> tuple[list[Club], list[Player]]:
    raw = _load_json(path)
    clubs = [Club(**item) for item in raw.get("clubs", [])]
    players = [Player(**item) for item in raw.get("players", [])]
    return clubs, players


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate realistic Master League transfer shortlists.")
    parser.add_argument("--world", required=True, help="JSON snapshot containing clubs and players")
    parser.add_argument("--config", required=True, help="Director configuration JSON")
    parser.add_argument("--seed", type=int, default=26, help="Deterministic market seed")
    parser.add_argument("--limit", type=int, default=5, help="Candidates per club")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    if args.limit < 1:
        parser.error("--limit must be >= 1")

    config = _load_json(args.config)
    clubs, players = _load_world(args.world)
    director = TransferDirector(clubs, players, config, seed=args.seed)
    market = director.generate_market(limit_per_club=args.limit)
    market["target"] = config.get("target", {})
    market["mode"] = config.get("mode", "proposal_only")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(market, handle, ensure_ascii=False, indent=2)

    print(f"LM AI Director: wrote {output}")


if __name__ == "__main__":
    main()
