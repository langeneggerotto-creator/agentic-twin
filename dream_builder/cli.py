import argparse
import sys
from pathlib import Path

from . import service, store
from .executor import ClaudeCodeError, build_with_claude_code
from .llm_client import OllamaError
from .projections import project_dream
from .recommendations import adopt_recommendation, generate_recommendations
from .reflector import reflect
from .resources import find_resources
from .scaling import plan_scaling
from .util import slugify
from .web_lookup import search


def _require_dream(dream_id):
    dream = store.get_dream(dream_id)
    if not dream:
        print(f"No dream with id '{dream_id}'.", file=sys.stderr)
        sys.exit(1)
    return dream


def _print_hints(dream):
    hints = dream.get("resource_hints") or []
    if hints:
        print("\nMight be worth a look:")
        for h in hints:
            print(f"- {h}")


def cmd_add(args):
    dream = service.create_dream_with_hints(args.title, args.description)
    print(f"Created dream {dream['id']}: {dream['title']}")
    _print_hints(dream)


def cmd_list(args):
    dreams = store.load_dreams()
    if not dreams:
        print("No dreams yet. Add one with `add`.")
        return
    for d in dreams:
        done = sum(1 for s in d["plan"] if s["done"])
        total = len(d["plan"])
        print(f"[{d['id']}] {d['title']} — {d['status']} ({done}/{total} steps)")


def cmd_plan(args):
    dream = _require_dream(args.id)
    service.plan_dream(dream)
    print(f"Plan for '{dream['title']}':")
    for i, s in enumerate(dream["plan"], 1):
        tag = " [needs internet]" if s["needs_internet"] else ""
        print(f"{i}. {s['step']}{tag}")
    _print_hints(dream)


def _print_recommendations(recommendations):
    if not recommendations:
        return
    print("\n3 recommended approaches — pick one with `adopt <id> <n>`:")
    for i, r in enumerate(recommendations, 1):
        tag = " [synthesized: combines the above in a new way]" if r["is_synthesized"] else ""
        print(f"\n{i}. {r['title']}{tag}")
        print(f"   {r['summary']}")
        for s in r["plan"]:
            print(f"   - {s['step']}")
        if r["resources_used"]:
            print(f"   Uses: {', '.join(r['resources_used'])}")


def cmd_recommend(args):
    dream = _require_dream(args.id)
    recommendations = generate_recommendations(dream)
    print(f"Recommendations for '{dream['title']}':")
    _print_recommendations(recommendations)


def cmd_adopt(args):
    dream = _require_dream(args.id)
    try:
        dream = adopt_recommendation(dream, args.index - 1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Adopted '{dream['adopted_recommendation']['title']}' as the plan for '{dream['title']}':")
    for i, s in enumerate(dream["plan"], 1):
        print(f"{i}. {s['step']}")


def cmd_resources(args):
    dream = _require_dream(args.id)
    resources = find_resources(dream)
    print(f"Resources for '{dream['title']}':")
    for r in resources:
        print(f"\n- {r['resource']} ({r['why']})")
        print(f"  {r['recommendation']}")
        for o in r["options"]:
            print(f"    * {o['title']} — {o['url']}")


def _print_projection(projection):
    if not projection:
        return
    print(f"\nProjected time: {projection['time_estimate']}")
    print(f"Projected cost: {projection['cost_estimate']}")
    if projection["lead_measures"]:
        print("\nLead measures (things you control, track weekly):")
        for m in projection["lead_measures"]:
            print(f"- {m}")
    if projection["lag_measures"]:
        print("\nLag measures (outcomes that confirm you're getting there):")
        for m in projection["lag_measures"]:
            print(f"- {m}")


def cmd_show(args):
    dream = _require_dream(args.id)
    print(f"{dream['title']} — {dream['status']}")
    print(dream["description"])
    _print_hints(dream)
    if dream.get("adopted_recommendation"):
        print(f"\nAdopted approach: {dream['adopted_recommendation']['title']}")
    if dream["plan"]:
        print("\nPlan:")
        for i, s in enumerate(dream["plan"], 1):
            box = "x" if s["done"] else " "
            print(f"[{box}] {i}. {s['step']}")
    elif dream.get("recommendations"):
        _print_recommendations(dream["recommendations"])
    if dream["resources"]:
        print("\nResources:")
        for r in dream["resources"]:
            print(f"- {r['resource']}: {r['recommendation']}")
    _print_projection(dream.get("projection"))
    _print_scaling(dream.get("scaling"))
    if dream["reflections"]:
        print(f"\nLatest reflection ({dream['reflections'][-1]['date']}):")
        print(dream["reflections"][-1]["text"])


def cmd_done(args):
    dream = _require_dream(args.id)
    idx = args.step - 1
    if idx < 0 or idx >= len(dream["plan"]):
        print("Step out of range.", file=sys.stderr)
        sys.exit(1)
    dream["plan"][idx]["done"] = True
    if all(s["done"] for s in dream["plan"]):
        dream["status"] = "done"
    store.update_dream(dream)
    print(f"Marked step {args.step} done.")


def cmd_reflect(args):
    dream = _require_dream(args.id)
    print(reflect(dream))


def cmd_project(args):
    dream = _require_dream(args.id)
    projection = project_dream(dream)
    print(f"Projection for '{dream['title']}':")
    _print_projection(projection)


def _print_scaling(scaling):
    if not scaling:
        return
    print(f"\nFunding strategy: {scaling['funding_strategy']}")
    print(f"\nScaling strategy: {scaling['scaling_strategy']}")
    if scaling["funding_milestones"]:
        print("\nFunding milestones:")
        for m in scaling["funding_milestones"]:
            print(f"- {m}")
    if scaling["scaling_lead_measures"]:
        print("\nScaling lead measures (things you control, track weekly):")
        for m in scaling["scaling_lead_measures"]:
            print(f"- {m}")
    if scaling["scaling_lag_measures"]:
        print("\nScaling lag measures (outcomes that confirm real growth):")
        for m in scaling["scaling_lag_measures"]:
            print(f"- {m}")


def cmd_scale(args):
    dream = _require_dream(args.id)
    scaling = plan_scaling(dream)
    print(f"Funding & scaling plan for '{dream['title']}':")
    _print_scaling(scaling)


def cmd_build(args):
    dream = _require_dream(args.id)
    target_dir = args.dir or Path("builds") / f"{dream['id']}-{slugify(dream['title'])}"
    print(f"Building '{dream['title']}' in {target_dir} using Claude Code "
          f"(permission mode: {args.permission_mode})...")
    build_with_claude_code(dream, target_dir, permission_mode=args.permission_mode)
    print(f"\nDone. Project is in {target_dir}")


def cmd_lookup(args):
    for r in search(args.query):
        print(f"- {r['title']}\n  {r['url']}\n  {r['snippet']}\n")


def cmd_capture(args):
    dream = _require_dream(args.dream_id)
    idx = args.index - 1
    if args.kind == "resource":
        items = dream.get("resources") or []
        if idx < 0 or idx >= len(items):
            print("Resource index out of range.", file=sys.stderr)
            sys.exit(1)
        r = items[idx]
        label, detail = r["resource"], r["recommendation"]
        url = r["options"][0]["url"] if r.get("options") else None
    else:
        items = dream.get("resource_hints") or []
        if idx < 0 or idx >= len(items):
            print("Hint index out of range.", file=sys.stderr)
            sys.exit(1)
        hint = items[idx]
        label, detail, url = hint[:60], hint, None
    item = store.add_to_bucket(
        label, detail, url=url, source_dream_id=dream["id"], source_dream_title=dream["title"]
    )
    print(f"Captured to action bucket: [{item['id']}] {item['label']}")


def cmd_bucket(args):
    items = store.load_bucket()
    if not items:
        print("Action bucket is empty. Capture something with `capture <dream_id> resource|hint <n>`.")
        return
    for i in items:
        src = f" (from {i['source_dream_title']})" if i.get("source_dream_title") else ""
        print(f"[{i['id']}] {i['label']}{src}")
        print(f"    {i['detail']}")
        if i.get("url"):
            print(f"    {i['url']}")


def cmd_uncapture(args):
    store.remove_from_bucket(args.item_id)
    print(f"Removed {args.item_id} from action bucket.")


def cmd_combine(args):
    try:
        dream = service.combine_bucket_items(args.item_ids, args.title, args.description or "")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Created combined dream {dream['id']}: {dream['title']}")
    _print_hints(dream)


def cmd_serve(args):
    try:
        import uvicorn
    except ImportError:
        print(
            "Install web UI deps first: pip install fastapi uvicorn httpx",
            file=sys.stderr,
        )
        sys.exit(1)
    uvicorn.run(
        "dream_builder.webapp.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


def build_parser():
    parser = argparse.ArgumentParser(prog="dream-builder")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add a new dream/goal")
    p_add.add_argument("title")
    p_add.add_argument("description")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="List all dreams")
    p_list.set_defaults(func=cmd_list)

    p_plan = sub.add_parser("plan", help="Generate/regenerate a plan for a dream")
    p_plan.add_argument("id")
    p_plan.set_defaults(func=cmd_plan)

    p_resources = sub.add_parser(
        "resources", help="Find resources needed for a dream (lowest cost, highest value)"
    )
    p_resources.add_argument("id")
    p_resources.set_defaults(func=cmd_resources)

    p_show = sub.add_parser("show", help="Show a dream, its plan, resources and last reflection")
    p_show.add_argument("id")
    p_show.set_defaults(func=cmd_show)

    p_done = sub.add_parser("done", help="Mark a plan step as done")
    p_done.add_argument("id")
    p_done.add_argument("step", type=int)
    p_done.set_defaults(func=cmd_done)

    p_reflect = sub.add_parser("reflect", help="Get a reflection on progress")
    p_reflect.add_argument("id")
    p_reflect.set_defaults(func=cmd_reflect)

    p_project = sub.add_parser(
        "project", help="Project time/cost to reach a dream, and lead/lag measures to track"
    )
    p_project.add_argument("id")
    p_project.set_defaults(func=cmd_project)

    p_scale = sub.add_parser(
        "scale", help="Plan how to fund and scale a dream (works for any kind of goal)"
    )
    p_scale.add_argument("id")
    p_scale.set_defaults(func=cmd_scale)

    p_recommend = sub.add_parser(
        "recommend",
        help="Have the AI synthesize gathered info into 3 complete approaches to pick from",
    )
    p_recommend.add_argument("id")
    p_recommend.set_defaults(func=cmd_recommend)

    p_adopt = sub.add_parser(
        "adopt", help="Adopt one of the 3 recommended approaches as the dream's actual plan"
    )
    p_adopt.add_argument("id")
    p_adopt.add_argument("index", type=int, help="1, 2, or 3")
    p_adopt.set_defaults(func=cmd_adopt)

    p_lookup = sub.add_parser("lookup", help="Run a one-off web search")
    p_lookup.add_argument("query")
    p_lookup.set_defaults(func=cmd_lookup)

    p_capture = sub.add_parser(
        "capture", help="Save a resource or hint from a dream into your action bucket"
    )
    p_capture.add_argument("dream_id")
    p_capture.add_argument("kind", choices=["resource", "hint"])
    p_capture.add_argument("index", type=int)
    p_capture.set_defaults(func=cmd_capture)

    p_bucket = sub.add_parser("bucket", help="List everything captured in your action bucket")
    p_bucket.set_defaults(func=cmd_bucket)

    p_uncapture = sub.add_parser("uncapture", help="Remove an item from your action bucket")
    p_uncapture.add_argument("item_id")
    p_uncapture.set_defaults(func=cmd_uncapture)

    p_combine = sub.add_parser(
        "combine", help="Combine one or more captured items into a new dream"
    )
    p_combine.add_argument("item_ids", nargs="+")
    p_combine.add_argument("--title", required=True)
    p_combine.add_argument("--description", default="")
    p_combine.set_defaults(func=cmd_combine)

    p_build = sub.add_parser(
        "build", help="Have Claude Code implement the plan as a real project"
    )
    p_build.add_argument("id")
    p_build.add_argument(
        "--dir", type=Path, default=None,
        help="Target directory (default: builds/<id>-<slug>/)",
    )
    p_build.add_argument(
        "--permission-mode", default="acceptEdits",
        choices=["acceptEdits", "auto", "bypassPermissions", "manual", "dontAsk", "plan"],
        help="Claude Code permission mode (default: acceptEdits — auto-accept "
             "file edits, everything else still gated)",
    )
    p_build.set_defaults(func=cmd_build)

    p_serve = sub.add_parser("serve", help="Run the local web UI")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.add_argument("--reload", action="store_true")
    p_serve.set_defaults(func=cmd_serve)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except (OllamaError, ClaudeCodeError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
