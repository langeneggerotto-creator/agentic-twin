import json

DEFAULT_WEIGHTS = {
    "remote": 0.30,
    "low_effort": 0.30,
    "low_startup_cost": 0.15,
    "speed_to_revenue": 0.10,
    "income_potential": 0.15,
}


def load_opportunities(data_path: str = "vault/business_opportunities.json") -> dict:
    with open(data_path) as f:
        return json.load(f)


def _normalize(value: float, low: float, high: float, invert: bool = False) -> float:
    if high == low:
        return 0.5
    score = (value - low) / (high - low)
    score = max(0.0, min(1.0, score))
    return 1 - score if invert else score


def score_opportunity(op: dict, weights: dict = None) -> float:
    weights = weights or DEFAULT_WEIGHTS

    remote = op["remote_score"] / 10
    low_effort = 1 - (op["effort_score"] / 10)
    low_cost = _normalize(op["startup_cost_usd"], 0, 2000, invert=True)
    speed = _normalize(op["time_to_first_revenue_days"], 1, 180, invert=True)
    income_mid = (op["income_potential_monthly_usd_low"] + op["income_potential_monthly_usd_high"]) / 2
    income = _normalize(income_mid, 0, 10000)

    composite = (
        weights["remote"] * remote
        + weights["low_effort"] * low_effort
        + weights["low_startup_cost"] * low_cost
        + weights["speed_to_revenue"] * speed
        + weights["income_potential"] * income
    )
    return round(composite * 100, 1)


def rank_opportunities(opportunities: dict, weights: dict = None) -> list:
    scored = [
        {**op, "match_score": score_opportunity(op, weights)}
        for op in opportunities["business_opportunities"]
    ]
    return sorted(scored, key=lambda o: o["match_score"], reverse=True)


def educational_tracks(opportunities: dict) -> list:
    return opportunities.get("educational_tracks", [])
