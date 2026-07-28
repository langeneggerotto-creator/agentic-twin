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
