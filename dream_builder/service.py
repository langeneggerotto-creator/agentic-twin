"""Shared orchestration used by both the CLI and the web UI, so "what
happens on add/plan" lives in one place instead of being duplicated per
interface."""

from . import planner, resources, store


def create_dream_with_hints(title, description):
    dream = store.create_dream(title, description)
    resources.suggest_resources(dream)
    return dream


def plan_dream(dream):
    planner.build_plan(dream)
    resources.suggest_resources(dream)
    return dream


def combine_bucket_items(item_ids, title, description=""):
    """Turn one or more captured action-bucket items — possibly saved from
    different dreams' searches — into a single new dream, so a user can
    bundle e.g. several eldercare services into one combined plan."""
    items = [store.get_bucket_item(i) for i in item_ids]
    items = [i for i in items if i is not None]
    if not items:
        raise ValueError("No matching bucket items to combine.")
    combined = "\n".join(f"- {i['label']}: {i['detail']}" for i in items)
    full_description = (f"{description}\n\n" if description else "") + f"Combining:\n{combined}"
    return create_dream_with_hints(title, full_description)
