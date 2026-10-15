"""
core/cli_tracker.py
===================
CLI wrapper for state_tracker.py — Rule 1.

Usage:
  python core/cli_tracker.py start --stage "Stage 1" --step "Step 1.0" \\
      --tool "01_curl_cffi" --action "scrape_for_leetcode" --subtask "Init run"

  python core/cli_tracker.py update --progress 50 --subtask "Parsing HTML"

  python core/cli_tracker.py complete

  python core/cli_tracker.py fail --reason "Network timeout"

  python core/cli_tracker.py status

  python core/cli_tracker.py workers
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.state_tracker import (
    complete_task,
    fail_task,
    read_state,
    refresh_workers,
    start_task,
    update_progress,
)


def cmd_start(args: argparse.Namespace) -> None:
    start_task(
        stage=args.stage,
        step=args.step,
        tool_id=args.tool,
        action=args.action,
        subtask=args.subtask,
    )
    state = read_state()
    print(
        f"[cli_tracker] STARTED — {args.stage} / {args.step} | "
        f"Tool: {args.tool} | Action: {args.action}"
    )


def cmd_update(args: argparse.Namespace) -> None:
    update_progress(
        progress_percent=args.progress,
        subtask=args.subtask,
    )
    print(f"[cli_tracker] PROGRESS {args.progress}% — {args.subtask}")


def cmd_complete(args: argparse.Namespace) -> None:
    complete_task(message=args.message)
    print(f"[cli_tracker] COMPLETED — {args.message}")


def cmd_fail(args: argparse.Namespace) -> None:
    fail_task(reason=args.reason)
    print(f"[cli_tracker] FAILED — {args.reason}")


def cmd_status(args: argparse.Namespace) -> None:
    state = read_state()
    print(json.dumps(state, indent=2, default=str))


def cmd_workers(args: argparse.Namespace) -> None:
    workers = refresh_workers()
    if workers:
        print(f"[cli_tracker] Found {len(workers)} worker process(es):")
        for w in workers:
            print(
                f"  PID {w['pid']} | {w['name']} | CPU {w['cpu_pct']}% | "
                f"RAM {w['ram_mb']}MB | Runtime {w['runtime_s']}s"
            )
    else:
        print("[cli_tracker] No project worker processes found.")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="cli_tracker",
        description="Antigravity Live State Telemetry CLI — Rule 1",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # start
    p_start = subparsers.add_parser("start", help="Start a new task")
    p_start.add_argument("--stage", default="")
    p_start.add_argument("--step", default="")
    p_start.add_argument("--tool", default="")
    p_start.add_argument("--action", default="")
    p_start.add_argument("--subtask", default="")
    p_start.set_defaults(func=cmd_start)

    # update
    p_update = subparsers.add_parser("update", help="Update progress")
    p_update.add_argument("--progress", type=int, default=0)
    p_update.add_argument("--subtask", default="")
    p_update.set_defaults(func=cmd_update)

    # complete
    p_complete = subparsers.add_parser("complete", help="Mark task complete")
    p_complete.add_argument("--message", default="Task completed.")
    p_complete.set_defaults(func=cmd_complete)

    # fail
    p_fail = subparsers.add_parser("fail", help="Mark task failed")
    p_fail.add_argument("--reason", default="Unknown error.")
    p_fail.set_defaults(func=cmd_fail)

    # status
    p_status = subparsers.add_parser("status", help="Print current live state")
    p_status.set_defaults(func=cmd_status)

    # workers
    p_workers = subparsers.add_parser("workers", help="List active worker processes")
    p_workers.set_defaults(func=cmd_workers)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
