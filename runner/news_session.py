import json
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents import news_analyst
from governance.gatekeeper import enforce_claims_safety

DATA_PATH = str(REPO_ROOT / "vault" / "business_opportunities.json")
REPORT_PATH = str(REPO_ROOT / "outputs" / "news_session_report.md")


def build_report(ranked: list, tracks: list, generated_on: str) -> str:
    lines = [
        f"# News Session -- Online Business Opportunity Scan ({generated_on})",
        "",
        "This is a decision-support digest, not financial advice or a guarantee of income.",
        "Scores are heuristic estimates from the criteria below, calibrated against public 2026 market",
        "write-ups (see Sources in each entry). Validate demand yourself before committing time or money.",
        "",
        "**Ranking criteria (weights):** remote-friendliness (30%), low ongoing effort (30%), "
        "low startup cost (15%), speed to first revenue (10%), income potential (15%).",
        "",
        "## Ranked Opportunities",
        "",
        "| # | Opportunity | Match Score | Remote | Effort | Startup Cost | Time to $ | Monthly Potential |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for i, op in enumerate(ranked, start=1):
        lines.append(
            f"| {i} | {op['name']} | {op['match_score']} | {op['remote_score']}/10 | "
            f"{op['effort_score']}/10 | ${op['startup_cost_usd']} | {op['time_to_first_revenue_days']}d | "
            f"${op['income_potential_monthly_usd_low']}-{op['income_potential_monthly_usd_high']}/mo |"
        )

    top = ranked[0]
    lines += [
        "",
        f"## Top Match: {top['name']}",
        "",
        top["description"],
        "",
        f"**Why it ranks first:** {top['why_it_fits']}",
        "",
        "**Getting started:**",
    ]
    lines += [f"- {step}" for step in top["first_steps"]]

    lines += ["", "## Full Opportunity Detail", ""]
    for op in ranked:
        lines += [
            f"### {op['name']} (match {op['match_score']})",
            op["description"],
            f"- Category: {op['category']}",
            f"- Skills needed: {', '.join(op['skills_required'])}",
            f"- Sources: {', '.join(op['source_urls'])}",
            "",
        ]

    lines += ["## Educational Tracks (support skills, not standalone businesses)", ""]
    for t in tracks:
        lines += [
            f"### {t['name']}",
            t["description"],
            f"- Why it helps: {t['relevance']}",
            f"- Resources: {', '.join(t['resources'])}",
            "",
        ]

    lines += [
        "## Governance Note",
        "",
        "Per this repo's Core OS inheritance, these are simulated/forecast estimates drawn from public",
        "market commentary, not observed or validated outcomes. Treat this as a shortlist to validate",
        "yourself (demand testing, a small pilot, real customer conversations) before committing "
        "significant time or money.",
    ]
    return "\n".join(lines)


def run_news_session() -> str:
    opportunities = news_analyst.load_opportunities(DATA_PATH)
    ranked = news_analyst.rank_opportunities(opportunities)
    tracks = news_analyst.educational_tracks(opportunities)
    report = build_report(ranked, tracks, date.today().isoformat())

    violations = enforce_claims_safety(report)
    if violations:
        raise ValueError(f"Report failed claims-safety check: {violations}")

    Path("outputs").mkdir(exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        f.write(report)

    return report


if __name__ == "__main__":
    print(run_news_session())
