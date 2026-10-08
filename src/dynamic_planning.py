"""
Topic 10 — Dynamic Planning in Code.

Tasks implemented:
    Task 1 — Breadth-first planning
    Task 2 — Sequential execution
    Task 3 — Dynamic replanning

The implementation uses only the Python standard library.
"""

from __future__ import annotations

from collections import deque


# ============================================================
# Reference World
# ============================================================

ACTIONS = {
    "take_highway": (
        {"at_home"},
        {"at_city"},
    ),
    "take_backroad": (
        {"at_home"},
        {"at_city"},
    ),
    "park": (
        {"at_city"},
        {"parked"},
    ),
    "walk_to_office": (
        {"parked"},
        {"at_office"},
    ),
}


# ============================================================
# Task 1 — Breadth-First Planner
# ============================================================

def plan(
    start: frozenset[str],
    goal: frozenset[str],
    actions: dict[str, tuple[set[str], set[str]]],
) -> list[str] | None:
    """
    Find the shortest action plan from start to goal.

    Breadth-first search is used, so the first solution
    found has the minimum number of actions.
    """

    if not isinstance(start, frozenset):
        raise TypeError(
            "start must be a frozenset"
        )

    if not isinstance(goal, frozenset):
        raise TypeError(
            "goal must be a frozenset"
        )

    if not isinstance(actions, dict):
        raise TypeError(
            "actions must be a dictionary"
        )

    if goal.issubset(start):
        return []

    queue = deque(
        [
            (
                start,
                [],
            )
        ]
    )

    visited = {
        start
    }

    while queue:
        current_state, path = queue.popleft()

        for action_name in sorted(actions):
            action = actions[action_name]

            if (
                not isinstance(action, tuple)
                or len(action) != 2
            ):
                raise ValueError(
                    f"invalid action definition: "
                    f"{action_name}"
                )

            preconditions, effects = action

            if not isinstance(
                preconditions,
                set,
            ):
                raise TypeError(
                    f"preconditions for "
                    f"'{action_name}' must be a set"
                )

            if not isinstance(
                effects,
                set,
            ):
                raise TypeError(
                    f"effects for "
                    f"'{action_name}' must be a set"
                )

            if not preconditions.issubset(
                current_state
            ):
                continue

            next_state = frozenset(
                current_state | effects
            )

            if next_state in visited:
                continue

            next_path = [
                *path,
                action_name,
            ]

            if goal.issubset(
                next_state
            ):
                return next_path

            visited.add(
                next_state
            )

            queue.append(
                (
                    next_state,
                    next_path,
                )
            )

    return None


# ============================================================
# Task 2 — Static Executor
# ============================================================

def execute_plan(
    start: frozenset[str],
    action_plan: list[str],
    actions: dict[str, tuple[set[str], set[str]]],
) -> dict:
    """
    Execute an existing action plan sequentially.

    Returns:
        {
            "state": final_state,
            "log": execution_log,
        }
    """

    if not isinstance(
        start,
        frozenset,
    ):
        raise TypeError(
            "start must be a frozenset"
        )

    if not isinstance(
        action_plan,
        list,
    ):
        raise TypeError(
            "action_plan must be a list"
        )

    if not isinstance(
        actions,
        dict,
    ):
        raise TypeError(
            "actions must be a dictionary"
        )

    current = start

    log: list[dict] = []

    for step_number, action_name in enumerate(
        action_plan,
        start=1,
    ):
        if action_name not in actions:
            raise KeyError(
                f"unknown action: {action_name}"
            )

        preconditions, effects = actions[
            action_name
        ]

        if not preconditions.issubset(
            current
        ):
            raise RuntimeError(
                f"preconditions failed for "
                f"'{action_name}'"
            )

        current = frozenset(
            current | effects
        )

        log.append(
            {
                "step": step_number,
                "action": action_name,
                "state": sorted(current),
            }
        )

    return {
        "state": current,
        "log": log,
    }


# ============================================================
# Task 3 — Dynamic Executor and Replanning
# ============================================================

def run_dynamic(
    start: frozenset[str],
    goal: frozenset[str],
    actions: dict[str, tuple[set[str], set[str]]],
    events: dict[int, list[str]] | None = None,
    max_replans: int = 3,
) -> dict:
    """
    Execute a dynamically changing plan.

    events:
        Maps an execution step number to action names
        that become unavailable immediately before that
        execution step.

    Example:

        events = {
            3: ["walk_to_office"],
        }

    means the planned action walk_to_office becomes
    unavailable before execution step 3.

    When the current plan becomes invalid, the planner
    replans from the CURRENT state.

    Returns:

        {
            "ok": bool,
            "state": final_state,
            "log": execution_log,
            "replans": number_of_replans,
        }
    """

    if not isinstance(
        start,
        frozenset,
    ):
        raise TypeError(
            "start must be a frozenset"
        )

    if not isinstance(
        goal,
        frozenset,
    ):
        raise TypeError(
            "goal must be a frozenset"
        )

    if not isinstance(
        actions,
        dict,
    ):
        raise TypeError(
            "actions must be a dictionary"
        )

    if events is None:
        events = {}

    if not isinstance(
        events,
        dict,
    ):
        raise TypeError(
            "events must be a dictionary"
        )

    if not isinstance(
        max_replans,
        int,
    ) or isinstance(
        max_replans,
        bool,
    ):
        raise TypeError(
            "max_replans must be an integer"
        )

    if max_replans < 0:
        raise ValueError(
            "max_replans must not be negative"
        )

    # Never modify the caller's dictionary.
    available_actions = {
        name: (
            set(preconditions),
            set(effects),
        )
        for name, (
            preconditions,
            effects,
        ) in actions.items()
    }

    current = start
    replans = 0
    execution_step = 0

    log: list[dict] = []

    current_plan = plan(
        current,
        goal,
        available_actions,
    )

    if current_plan is None:
        return {
            "ok": False,
            "state": current,
            "log": log,
            "replans": replans,
        }

    while current_plan:

        # ----------------------------------------------------
        # Apply events before the next action.
        # ----------------------------------------------------

        next_step_number = (
            execution_step + 1
        )

        for removed_action in events.get(
            next_step_number,
            [],
        ):
            available_actions.pop(
                removed_action,
                None,
            )

        next_action = current_plan[0]

        # ----------------------------------------------------
        # Check whether the planned action still exists.
        # ----------------------------------------------------

        if next_action not in available_actions:

            replans += 1

            log.append(
                {
                    "event": "replan",
                    "step": next_step_number,
                    "reason": (
                        f"action '{next_action}' "
                        "is no longer available"
                    ),
                    "replan": replans,
                    "state": sorted(current),
                }
            )

            if replans > max_replans:
                return {
                    "ok": False,
                    "state": current,
                    "log": log,
                    "replans": replans,
                }

            current_plan = plan(
                current,
                goal,
                available_actions,
            )

            if current_plan is None:
                return {
                    "ok": False,
                    "state": current,
                    "log": log,
                    "replans": replans,
                }

            continue

        preconditions, effects = (
            available_actions[
                next_action
            ]
        )

        # ----------------------------------------------------
        # Check whether the action is still applicable.
        # ----------------------------------------------------

        if not preconditions.issubset(
            current
        ):

            replans += 1

            log.append(
                {
                    "event": "replan",
                    "step": next_step_number,
                    "reason": (
                        f"preconditions for "
                        f"'{next_action}' "
                        "are no longer satisfied"
                    ),
                    "replan": replans,
                    "state": sorted(current),
                }
            )

            if replans > max_replans:
                return {
                    "ok": False,
                    "state": current,
                    "log": log,
                    "replans": replans,
                }

            current_plan = plan(
                current,
                goal,
                available_actions,
            )

            if current_plan is None:
                return {
                    "ok": False,
                    "state": current,
                    "log": log,
                    "replans": replans,
                }

            continue

        # ----------------------------------------------------
        # Execute action.
        # ----------------------------------------------------

        current = frozenset(
            current | effects
        )

        execution_step += 1

        log.append(
            {
                "event": "action",
                "step": execution_step,
                "action": next_action,
                "state": sorted(current),
            }
        )

        # Remove the action we just executed from
        # the current plan.
        current_plan = current_plan[1:]

        # ----------------------------------------------------
        # If the goal has been reached, stop.
        # ----------------------------------------------------

        if goal.issubset(current):
            break

        # ----------------------------------------------------
        # Otherwise continue the existing plan.
        # ----------------------------------------------------

    return {
        "ok": goal.issubset(current),
        "state": current,
        "log": log,
        "replans": replans,
    }


# ============================================================
# Demonstration
# ============================================================

def main() -> None:
    """
    Demonstrate the basic planner.
    """

    start = frozenset(
        {"at_home"}
    )

    goal = frozenset(
        {"at_office"}
    )

    result = plan(
        start,
        goal,
        ACTIONS,
    )

    print(
        "Topic 10 — Dynamic Planning"
    )
    print(
        "=" * 60
    )

    print()
    print(
        f"Start: {sorted(start)}"
    )

    print(
        f"Goal: {sorted(goal)}"
    )

    print()
    print(
        "Plan:"
    )

    print(
        result
    )


if __name__ == "__main__":
    main()