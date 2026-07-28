import argparse
import re
import sys
from pathlib import Path

from . import store
from .executor import ClaudeCodeError, build_with_claude_code
from .llm_client import OllamaError
from .planner import build_plan
from .reflector import reflect
from .resources import find_resources
from .web_lookup import search


def _slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "project"


def _require_dream(dream_id):
    dream = store.get_dream(dream_id)
    if not dream:
        print(f"No dream with id '{dream_id}'.", file=sys.stderr)
        sys.exit(1)
    return dream


def cmd_add(args):
    dream = store.create_dream(args.title, args.description)
    print(f"Created dream {dream['id']}: {dream['title']}")


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
    build_plan(dream)
    print(f"Plan for '{dream['title']}':")
    for i, s in enumerate(dream["plan"], 1):
        tag = " [needs internet]" if s["needs_internet"] else ""
        print(f"{i}. {s['step']}{tag}")


def cmd_resources(args):
    dream = _require_dream(args.id)
    resources = find_resources(dream)
    print(f"Resources for '{dream['title']}':")
    for r in resources:
        print(f"\n- {r['resource']} ({r['why']})")
        print(f"  {r['recommendation']}")
        for o in r["options"]:
            print(f"    * {o['title']} — {o['url']}")


def cmd_show(args):
    dream = _require_dream(args.id)
    print(f"{dream['title']} — {dream['status']}")
    print(dream["description"])
    if dream["plan"]:
        print("\nPlan:")
        for i, s in enumerate(dream["plan"], 1):
            box = "x" if s["done"] else " "
            print(f"[{box}] {i}. {s['step']}")
    if dream["resources"]:
        print("\nResources:")
        for r in dream["resources"]:
            print(f"- {r['resource']}: {r['recommendation']}")
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


def cmd_build(args):
    dream = _require_dream(args.id)
    target_dir = args.dir or Path("builds") / f"{dream['id']}-{_slugify(dream['title'])}"
    print(f"Building '{dream['title']}' in {target_dir} using Claude Code "
          f"(permission mode: {args.permission_mode})...")
    build_with_claude_code(dream, target_dir, permission_mode=args.permission_mode)
    print(f"\nDone. Project is in {target_dir}")


def cmd_lookup(args):
    for r in search(args.query):
        print(f"- {r['title']}\n  {r['url']}\n  {r['snippet']}\n")


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

    p_lookup = sub.add_parser("lookup", help="Run a one-off web search")
    p_lookup.add_argument("query")
    p_lookup.set_defaults(func=cmd_lookup)

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

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except (OllamaError, ClaudeCodeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
