"""Runs ON the Jetson. This is the edge half of the architecture that was
missing: everything else built in this repo (governance/, runner/providers/)
runs on "the more capable host" per the original design, because the
Jetson's stock JetPack 4 / Ubuntu 18.04 image doesn't meet Claude Code's
supported-OS floor -- Claude/OpenAI execution was never going to happen
on-device.

What the Jetson node actually does: watch local services (systemd units,
health checks), and when something's wrong, package it as a "dream" via
agents.dream_builder and drop it in a file-based queue directory. It never
calls Claude Code or OpenAI directly, and never touches git or the
repository itself -- it only produces a request. runner/dream_queue_worker.py
(on the control-plane host) is what actually picks the queue up and routes
it through governance.

No network dependency between the two beyond a shared filesystem/queue
directory in this reference implementation -- swap queue_dir for a
synced or mounted path (e.g. rsync, a shared volume, S3) for a real
two-machine deployment.
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.dream_builder import build_dream

DEFAULT_QUEUE_DIR = "vault/dream_queue/pending"


def check_service(name: str) -> str:
    """Returns 'active', 'inactive', 'failed', or 'unknown' (no systemd on
    this host, or the unit doesn't exist)."""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", name],
            capture_output=True, text=True, timeout=10,
        )
        status = result.stdout.strip()
        return status if status else "unknown"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "unknown"


def check_services(service_names: list) -> dict:
    return {name: check_service(name) for name in service_names}


def queue_dream(contract: dict, queue_dir: str = DEFAULT_QUEUE_DIR) -> Path:
    path = Path(queue_dir)
    path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    slug = "".join(c if c.isalnum() else "_" for c in contract["goal"])[:40]
    file_path = path / f"{timestamp}_{slug}.json"
    file_path.write_text(json.dumps(contract, indent=2))
    return file_path


def monitor_and_queue(
    service_names: list,
    allowed_paths: list,
    allowed_commands: list,
    queue_dir: str = DEFAULT_QUEUE_DIR,
) -> list:
    """Checks each service; for anything not 'active', builds a repair dream
    and queues it. Returns the list of queued file paths (empty if
    everything's healthy)."""
    statuses = check_services(service_names)
    queued = []
    for name, status in statuses.items():
        if status == "active":
            continue
        contract = build_dream(
            description=f"Repair the {name} service, which is currently '{status}'",
            allowed_paths=allowed_paths,
            allowed_commands=allowed_commands,
            acceptance_criteria=[f"systemctl is-active {name} reports 'active'"],
        )
        queued.append(queue_dream(contract, queue_dir))
    return queued


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("service", nargs="+", help="systemd unit name(s) to monitor")
    parser.add_argument("--allowed-path", action="append", default=[], dest="allowed_paths",
                         help="Repeatable. Glob pattern a repair dream may edit.")
    parser.add_argument("--allowed-command", action="append", default=[], dest="allowed_commands",
                         help="Repeatable. Command a repair dream may run.")
    parser.add_argument("--queue-dir", default=DEFAULT_QUEUE_DIR)
    args = parser.parse_args()

    queued = monitor_and_queue(args.service, args.allowed_paths, args.allowed_commands, args.queue_dir)
    if queued:
        print(f"Queued {len(queued)} repair dream(s):")
        for path in queued:
            print(f"  {path}")
    else:
        print("All monitored services are active. Nothing queued.")


if __name__ == "__main__":
    main()
