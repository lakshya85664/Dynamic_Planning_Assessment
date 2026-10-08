"""
Topic 10 — Dynamic Planning
Evidence Generator

Generates structured evidence for:
    Task 1 — BFS planning
    Task 2 — Execution
    Task 3 — Dynamic replanning
    Task 4 — Replan limits and safe failure
    Task 5 — Extended world
    Final pytest regression
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


# ============================================================
# Project paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
EVIDENCE_DIR = PROJECT_ROOT / "evidence"

sys.path.insert(0, str(SRC_DIR))


# ============================================================
# Import project implementation
# ============================================================

from dynamic_planning import (  # noqa: E402
    ACTIONS,
    execute_plan,
    plan,
    run_dynamic,
)


# ============================================================
# JSON-safe conversion
# ============================================================

def json_safe(value: Any) -> Any:
    """
    Recursively convert Python values into JSON-serializable values.

    Handles:
        - frozenset
        - set
        - tuple
        - list
        - dictionaries with non-string keys
        - nested combinations of the above
    """

    if isinstance(value, (set, frozenset)):
        converted = [json_safe(item) for item in value]

        # Make output deterministic where possible.
        try:
            return sorted(converted, key=lambda item: str(item))
        except Exception:
            return converted

    if isinstance(value, tuple):
        return [json_safe(item) for item in value]

    if isinstance(value, list):
        return [json_safe(item) for item in value]

    if isinstance(value, dict):
        return {
            str(key): json_safe(item)
            for key, item in value.items()
        }

    # Basic JSON-compatible values.
    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    # Fallback for unexpected objects.
    return str(value)


# ============================================================
# Save helper
# ============================================================

def save_json(filename: str, data: Any) -> None:
    """
    Save JSON evidence using the recursive json_safe converter.
    """

    path = EVIDENCE_DIR / filename

    safe_data = json_safe(data)

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            safe_data,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(f"Created: evidence/{filename}")


# ============================================================
# Task 1 — BFS planning
# ============================================================

def generate_task1_evidence() -> None:
    start = frozenset({"at_home"})
    goal = frozenset({"at_office"})

    result = plan(
        start,
        goal,
        ACTIONS,
    )

    impossible = plan(
        start,
        frozenset({"on_moon"}),
        ACTIONS,
    )

    save_json(
        "task1_planning.json",
        {
            "task": 1,
            "title": "Breadth-first planning",
            "start": start,
            "goal": goal,
            "plan": result,
            "plan_length": (
                len(result)
                if result is not None
                else None
            ),
            "impossible_goal_result": impossible,
            "planner_type": "breadth-first search",
        },
    )


# ============================================================
# Task 2 — Sequential execution
# ============================================================

def generate_task2_evidence() -> None:
    start = frozenset({"at_home"})

    action_plan = [
        "take_backroad",
        "park",
        "walk_to_office",
    ]

    result = execute_plan(
        start,
        action_plan,
        ACTIONS,
    )

    save_json(
        "task2_execution.json",
        {
            "task": 2,
            "title": "Sequential execution",
            "action_plan": action_plan,
            "final_state": result["state"],
            "execution_log": result["log"],
            "goal_reached": "at_office" in result["state"],
        },
    )


# ============================================================
# Task 3 — Dynamic replanning
# ============================================================

def generate_task3_evidence() -> None:
    """
    Demonstrates replanning after the original action
    becomes unavailable.

    Initial route:

        at_home
          |
          v
      take_backroad
          |
          v
        at_city
          |
          v
         park
          |
          v
        parked
          |
          v
    walk_to_office
          |
          v
       at_office

    At step 3, walk_to_office is removed.

    The planner then replans from the CURRENT state:

        parked
          |
          v
    prepare_shuttle
          |
          v
     shuttle_ready
          |
          v
      call_shuttle
          |
          v
       at_office
    """

    custom_actions = {
        **ACTIONS,
        "prepare_shuttle": (
            {"parked"},
            {"shuttle_ready"},
        ),
        "call_shuttle": (
            {"shuttle_ready"},
            {"at_office"},
        ),
    }

    result = run_dynamic(
        frozenset({"at_home"}),
        frozenset({"at_office"}),
        custom_actions,
        events={
            3: ["walk_to_office"],
        },
    )

    save_json(
        "task3_dynamic_replanning.json",
        {
            "task": 3,
            "title": "Dynamic replanning",
            "event": {
                "step": 3,
                "removed_action": "walk_to_office",
            },
            "actions_available_before_event": sorted(
                custom_actions.keys()
            ),
            "result": result,
            "replans": result["replans"],
            "goal_reached": result["ok"],
        },
    )


# ============================================================
# Task 4 — Replan limits and safe failure
# ============================================================

def generate_task4_evidence() -> None:
    start = frozenset({"at_home"})
    goal = frozenset({"at_office"})

    # --------------------------------------------------------
    # Case 1 — Zero replans allowed
    # --------------------------------------------------------

    limited = run_dynamic(
        start,
        goal,
        ACTIONS,
        events={
            1: ["take_backroad"],
        },
        max_replans=0,
    )

    # --------------------------------------------------------
    # Case 2 — No replacement plan exists
    # --------------------------------------------------------

    impossible = run_dynamic(
        start,
        goal,
        ACTIONS,
        events={
            1: [
                "take_backroad",
                "take_highway",
            ],
        },
    )

    save_json(
        "task4_replan_limits.json",
        {
            "task": 4,
            "title": "Replan limits and safe failure",

            "zero_replan_limit": {
                "result": limited,
                "safe_failure": limited["ok"] is False,
            },

            "no_replacement_plan": {
                "result": impossible,
                "safe_failure": impossible["ok"] is False,
            },
        },
    )


# ============================================================
# Task 5 — Extended world and new goal
# ============================================================

def generate_task5_evidence() -> None:
    """
    Extends the planning world with:

        enter_building
        go_to_meeting_room

    New goal:

        at_meeting_room
    """

    extended_actions = {
        **ACTIONS,

        "enter_building": (
            {"at_office"},
            {"inside_building"},
        ),

        "go_to_meeting_room": (
            {"inside_building"},
            {"at_meeting_room"},
        ),
    }

    start = frozenset({"at_home"})
    goal = frozenset({"at_meeting_room"})

    action_plan = plan(
        start,
        goal,
        extended_actions,
    )

    execution = execute_plan(
        start,
        action_plan or [],
        extended_actions,
    )

    save_json(
        "task5_extended_world.json",
        {
            "task": 5,
            "title": "Extended world and new goal",

            "new_actions": [
                "enter_building",
                "go_to_meeting_room",
            ],

            "new_goal": goal,

            "plan": action_plan,

            "final_state": execution["state"],

            "execution_log": execution["log"],

            "goal_reached": (
                "at_meeting_room"
                in execution["state"]
            ),
        },
    )


# ============================================================
# Final pytest regression
# ============================================================

def generate_test_summary() -> None:
    print()
    print("Running final pytest regression...")
    print("-" * 60)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    output = (
        result.stdout
        + result.stderr
    ).strip()

    save_json(
        "test_summary.json",
        {
            "command": "python -m pytest -q",
            "return_code": result.returncode,
            "passed": result.returncode == 0,
            "output": output,
        },
    )

    print()
    print(output)
    print()

    if result.returncode != 0:
        raise RuntimeError(
            "Final pytest regression failed."
        )


# ============================================================
# Main
# ============================================================

def main() -> None:
    EVIDENCE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Topic 10 — Evidence Generation")
    print("=" * 60)

    generate_task1_evidence()
    generate_task2_evidence()
    generate_task3_evidence()
    generate_task4_evidence()
    generate_task5_evidence()
    generate_test_summary()

    print()
    print("=" * 60)
    print("All Topic 10 evidence generated successfully.")
    print("=" * 60)


if __name__ == "__main__":
    main()