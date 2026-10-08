"""
Topic 10 — Dynamic Planning Tests.

Tasks:
    1. Breadth-first planning
    2. Sequential execution
    3. Dynamic replanning
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]

SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(
    0,
    str(SRC_DIR),
)

from dynamic_planning import (  # noqa: E402
    ACTIONS,
    execute_plan,
    plan,
    run_dynamic,
)


# ============================================================
# Task 1 — Planning
# ============================================================

def test_plan_finds_shortest_route():
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

    assert result is not None
    assert len(result) == 3


def test_plan_uses_valid_actions():
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

    assert result is not None

    assert result[0] in {
        "take_highway",
        "take_backroad",
    }

    assert result[1] == "park"
    assert result[2] == "walk_to_office"


def test_plan_returns_empty_when_goal_already_reached():
    start = frozenset(
        {"at_office"}
    )

    goal = frozenset(
        {"at_office"}
    )

    result = plan(
        start,
        goal,
        ACTIONS,
    )

    assert result == []


def test_plan_returns_none_for_impossible_goal():
    start = frozenset(
        {"at_home"}
    )

    goal = frozenset(
        {"on_moon"}
    )

    result = plan(
        start,
        goal,
        ACTIONS,
    )

    assert result is None


def test_plan_does_not_modify_start_state():
    start = frozenset(
        {"at_home"}
    )

    original = start

    goal = frozenset(
        {"at_office"}
    )

    plan(
        start,
        goal,
        ACTIONS,
    )

    assert start == original


def test_plan_is_deterministic():
    start = frozenset(
        {"at_home"}
    )

    goal = frozenset(
        {"at_office"}
    )

    first = plan(
        start,
        goal,
        ACTIONS,
    )

    second = plan(
        start,
        goal,
        ACTIONS,
    )

    assert first == second


def test_plan_requires_frozenset_start():
    try:
        plan(
            {"at_home"},
            frozenset(
                {"at_office"}
            ),
            ACTIONS,
        )
    except TypeError:
        pass
    else:
        raise AssertionError(
            "Expected TypeError"
        )


def test_plan_requires_frozenset_goal():
    try:
        plan(
            frozenset(
                {"at_home"}
            ),
            {"at_office"},
            ACTIONS,
        )
    except TypeError:
        pass
    else:
        raise AssertionError(
            "Expected TypeError"
        )


# ============================================================
# Task 2 — Executor
# ============================================================

def test_execute_plan_reaches_goal():
    start = frozenset(
        {"at_home"}
    )

    action_plan = plan(
        start,
        frozenset(
            {"at_office"}
        ),
        ACTIONS,
    )

    assert action_plan is not None

    result = execute_plan(
        start,
        action_plan,
        ACTIONS,
    )

    assert "at_office" in result["state"]


def test_execute_plan_logs_every_action():
    start = frozenset(
        {"at_home"}
    )

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

    assert len(
        result["log"]
    ) == 3

    assert [
        item["action"]
        for item in result["log"]
    ] == action_plan


def test_execute_plan_updates_state_between_steps():
    start = frozenset(
        {"at_home"}
    )

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

    assert "at_city" in set(
        result["log"][0]["state"]
    )

    assert "parked" in set(
        result["log"][1]["state"]
    )

    assert "at_office" in set(
        result["log"][2]["state"]
    )


def test_execute_plan_rejects_invalid_precondition():
    start = frozenset(
        {"at_home"}
    )

    action_plan = [
        "park",
    ]

    try:
        execute_plan(
            start,
            action_plan,
            ACTIONS,
        )
    except RuntimeError as error:
        assert (
            "preconditions failed"
            in str(error)
        )
    else:
        raise AssertionError(
            "Expected RuntimeError"
        )


def test_execute_plan_rejects_unknown_action():
    start = frozenset(
        {"at_home"}
    )

    action_plan = [
        "unknown_action",
    ]

    try:
        execute_plan(
            start,
            action_plan,
            ACTIONS,
        )
    except KeyError:
        pass
    else:
        raise AssertionError(
            "Expected KeyError"
        )


# ============================================================
# Task 3 — Dynamic Replanning
# ============================================================

def test_dynamic_replans_when_action_removed_at_step_1():
    start = frozenset(
        {"at_home"}
    )

    goal = frozenset(
        {"at_office"}
    )

    result = run_dynamic(
        start,
        goal,
        ACTIONS,
        events={
            1: [
                "take_backroad"
            ],
        },
    )

    assert result["ok"] is True
    assert result["replans"] == 1
    assert "at_office" in result["state"]

    actions = [
        item["action"]
        for item in result["log"]
        if item["event"] == "action"
    ]

    assert actions == [
        "take_highway",
        "park",
        "walk_to_office",
    ]


def test_dynamic_replans_when_action_removed_at_step_2():
    start = frozenset(
        {"at_home"}
    )

    goal = frozenset(
        {"at_office"}
    )

    result = run_dynamic(
        start,
        goal,
        ACTIONS,
        events={
            2: [
                "park"
            ],
        },
    )

    assert result["replans"] >= 1

    assert any(
        item["event"] == "replan"
        for item in result["log"]
    )


def test_dynamic_replan_uses_current_state():
    start = frozenset(
        {"at_home"}
    )

    goal = frozenset(
        {"at_office"}
    )

    custom_actions = {
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
        start,
        goal,
        custom_actions,
        events={
            3: [
                "walk_to_office"
            ],
        },
    )

    assert result["ok"] is True

    assert result["replans"] == 1

    action_entries = [
        item
        for item in result["log"]
        if item["event"] == "action"
    ]

    assert len(
        action_entries
    ) == 4

    assert action_entries[0]["action"] in {
        "take_highway",
        "take_backroad",
    }

    assert (
        action_entries[1]["action"]
        == "park"
    )

    assert (
        action_entries[2]["action"]
        == "prepare_shuttle"
    )

    assert (
        action_entries[3]["action"]
        == "call_shuttle"
    )

    assert (
        "at_office"
        in result["state"]
    )


def test_dynamic_does_not_modify_original_actions():
    start = frozenset(
        {"at_home"}
    )

    goal = frozenset(
        {"at_office"}
    )

    original_actions = {
        name: (
            set(preconditions),
            set(effects),
        )
        for name, (
            preconditions,
            effects,
        ) in ACTIONS.items()
    }

    run_dynamic(
        start,
        goal,
        original_actions,
        events={
            1: [
                "take_backroad"
            ],
        },
    )

    assert original_actions == {
        name: (
            set(preconditions),
            set(effects),
        )
        for name, (
            preconditions,
            effects,
        ) in ACTIONS.items()
    }


def test_dynamic_without_change_completes_normally():
    start = frozenset(
        {"at_home"}
    )

    goal = frozenset(
        {"at_office"}
    )

    result = run_dynamic(
        start,
        goal,
        ACTIONS,
    )

    assert result["ok"] is True
    assert result["replans"] == 0
    assert "at_office" in result["state"]

def test_dynamic_respects_max_replans():
    start = frozenset(
        {"at_home"}
    )

    goal = frozenset(
        {"at_office"}
    )

    result = run_dynamic(
        start,
        goal,
        ACTIONS,
        events={
            1: [
                "take_backroad"
            ],
        },
        max_replans=0,
    )

    assert result["ok"] is False

    assert result["replans"] == 1

    assert any(
        item["event"] == "replan"
        for item in result["log"]
    )


def test_dynamic_fails_when_replan_limit_is_exceeded():
    start = frozenset(
        {"at_home"}
    )

    goal = frozenset(
        {"at_office"}
    )

    result = run_dynamic(
        start,
        goal,
        ACTIONS,
        events={
            1: [
                "take_backroad"
            ],
        },
        max_replans=0,
    )

    assert result["ok"] is False

    assert "at_office" not in result["state"]


def test_dynamic_fails_safely_when_no_replacement_plan_exists():
    start = frozenset(
        {"at_home"}
    )

    goal = frozenset(
        {"at_office"}
    )

    result = run_dynamic(
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

    assert result["ok"] is False

    assert "at_office" not in result["state"]

    assert result["replans"] == 1


def test_dynamic_accepts_zero_replan_limit():
    start = frozenset(
        {"at_home"}
    )

    goal = frozenset(
        {"at_office"}
    )

    result = run_dynamic(
        start,
        goal,
        ACTIONS,
        max_replans=0,
    )

    assert result["ok"] is True

    assert result["replans"] == 0


def test_dynamic_rejects_negative_replan_limit():
    start = frozenset(
        {"at_home"}
    )

    goal = frozenset(
        {"at_office"}
    )

    try:
        run_dynamic(
            start,
            goal,
            ACTIONS,
            max_replans=-1,
        )
    except ValueError as error:
        assert (
            "must not be negative"
            in str(error)
        )
    else:
        raise AssertionError(
            "Expected ValueError"
        )

def test_extended_world_reaches_new_goal():
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

    start = frozenset(
        {"at_home"}
    )

    goal = frozenset(
        {"at_meeting_room"}
    )

    result = plan(
        start,
        goal,
        extended_actions,
    )

    assert result is not None

    assert result[-2:] == [
        "enter_building",
        "go_to_meeting_room",
    ]

    assert len(result) == 5


def test_extended_world_executes_new_goal():
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

    start = frozenset(
        {"at_home"}
    )

    goal = frozenset(
        {"at_meeting_room"}
    )

    action_plan = plan(
        start,
        goal,
        extended_actions,
    )

    assert action_plan is not None

    result = execute_plan(
        start,
        action_plan,
        extended_actions,
    )

    assert (
        "at_meeting_room"
        in result["state"]
    )


def test_extended_world_dynamic_replanning():
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
        "use_side_entrance": (
            {"at_office"},
            {"inside_building"},
        ),
    }

    start = frozenset(
        {"at_home"}
    )

    goal = frozenset(
        {"at_meeting_room"}
    )

    result = run_dynamic(
        start,
        goal,
        extended_actions,
        events={
            4: [
                "enter_building"
            ],
        },
    )

    assert result["ok"] is True

    assert result["replans"] == 1

    assert (
        "at_meeting_room"
        in result["state"]
    )

    actions = [
        item["action"]
        for item in result["log"]
        if item["event"] == "action"
    ]

    assert actions[-2:] == [
        "use_side_entrance",
        "go_to_meeting_room",
    ]


def test_extended_world_does_not_modify_base_actions():
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

    assert "enter_building" not in ACTIONS

    assert (
        "go_to_meeting_room"
        not in ACTIONS
    )

    assert (
        "enter_building"
        in extended_actions
    )

    assert (
        "go_to_meeting_room"
        in extended_actions
    )


def test_extended_world_rejects_unknown_goal():
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

    start = frozenset(
        {"at_home"}
    )

    goal = frozenset(
        {"at_mars"}
    )

    result = plan(
        start,
        goal,
        extended_actions,
    )

    assert result is None