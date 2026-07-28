import shutil
import subprocess
from pathlib import Path


class ClaudeCodeError(RuntimeError):
    """Raised when the `claude` CLI isn't available or exits with an error."""


BUILD_PROMPT_TEMPLATE = """\
You are implementing a software project for the user. Build it for real —
create actual files, a real project structure, and working code. Don't just
describe what you would do.

Goal: {title}
Details: {description}

Plan:
{plan}

Recommended resources:
{resources}

Start by scaffolding the project (pick a concrete language/framework and
justify it briefly), then implement the core functionality. Explain what
you're doing as you go.
"""


def _format_plan(dream):
    if not dream["plan"]:
        return "(no plan yet — figure out a sensible approach yourself)"
    return "\n".join(f"- {s['step']}" for s in dream["plan"])


def _format_resources(dream):
    if not dream["resources"]:
        return "(none gathered yet)"
    return "\n".join(f"- {r['resource']}: {r['recommendation']}" for r in dream["resources"])


def build_prompt(dream):
    return BUILD_PROMPT_TEMPLATE.format(
        title=dream["title"],
        description=dream["description"],
        plan=_format_plan(dream),
        resources=_format_resources(dream),
    )


def build_with_claude_code(dream, target_dir, permission_mode="acceptEdits", log_path=None):
    """Hand the dream's plan to a real `claude` CLI in `target_dir` to
    implement it. By default runs with output streamed live (not captured)
    since this can take a while. Pass `log_path` to instead redirect output
    to that file — used by the web UI, which has no terminal to stream to
    and runs this in a background thread. `permission_mode="acceptEdits"`
    auto-accepts file writes but still gates everything else (e.g. running
    commands) — intentionally not `bypassPermissions`, since this targets
    the user's real machine with real internet access."""
    if shutil.which("claude") is None:
        raise ClaudeCodeError(
            "The `claude` CLI isn't on your PATH. Install Claude Code "
            "(https://claude.com/code) and make sure you're logged in "
            "before running `build`."
        )

    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "claude",
        "-p",
        build_prompt(dream),
        "--permission-mode",
        permission_mode,
    ]

    if log_path is None:
        result = subprocess.run(cmd, cwd=target_dir, check=False)
    else:
        log_path = Path(log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as f:
            result = subprocess.run(
                cmd, cwd=target_dir, check=False, stdout=f, stderr=subprocess.STDOUT
            )
    if result.returncode != 0:
        raise ClaudeCodeError(f"claude exited with code {result.returncode}. See output above.")
    return target_dir
