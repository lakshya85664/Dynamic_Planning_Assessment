# Topic 10 — Implement Dynamic Planning in Code

## Project Information

- **Project:** Dynamic Planning Assessment
- **Course Area:** Agent Planning and Reasoning
- **Topic:** Topic 10 — Implement Dynamic Planning in Code
- **Language:** Python
- **Environment:** Windows CMD, Python 3.13.9, pytest 8.4.2

## Objective

The objective of this project is to implement a dynamic planning system that can create an action plan, execute the plan, detect changes in the environment, and replan from the current state when the original plan is no longer valid.

The implementation models actions through preconditions and effects over a state represented by a set of facts.

## Tasks Completed

### Task 1 — Implement `plan()` Using Breadth-First Search

Implemented `plan()` using deterministic Breadth-First Search (BFS). The planner explores reachable states and returns a shortest valid action sequence from the start state to the goal state.

It also safely returns `None` when the goal cannot be reached.

### Task 2 — Implement the Executor

Implemented `execute_plan()` to execute actions sequentially.

The executor:
- validates that actions exist;
- checks action preconditions;
- applies action effects;
- updates the current state;
- records an execution log;
- returns the final state and execution information.

### Task 3 — Detect Changes and Replan

Implemented `run_dynamic()` to support environmental changes during execution.

When an upcoming action becomes unavailable or its preconditions are no longer satisfied, the system replans from the **current state**, rather than restarting from the original state.

The implementation demonstrates an alternate shuttle route when `walk_to_office` becomes unavailable.

### Task 4 — Limit Replans and Fail Safely

The dynamic planner supports a configurable `max_replans` limit.

The implementation:
- respects the maximum number of replans;
- supports zero replans;
- fails safely when the replan limit is exceeded;
- fails safely when no replacement plan exists;
- rejects invalid negative replan limits.

### Task 5 — Extend the World With New Actions and Goal

The planning world was extended with:
- `enter_building`
- `go_to_meeting_room`

A new goal, `at_meeting_room`, was introduced and successfully planned and executed.

## Project Structure

```text
Dynamic_Planning_Assessment/
├── .gitignore
├── requirements.txt
├── src/
│   └── dynamic_planning.py
├── tests/
│   └── test_dynamic_planning.py
└── evidence/
    ├── generate_evidence.py
    ├── task1_planning.json
    ├── task2_execution.json
    ├── task3_dynamic_replanning.json
    ├── task4_replan_limits.json
    ├── task5_extended_world.json
    └── test_summary.json
```

## Verification

The complete test suite was executed using:

```cmd
python -m pytest -q
```

Final result:

```text
28 passed in 0.04s
```

Evidence was generated using:

```cmd
python evidence\generate_evidence.py
```

The evidence generator completed successfully and performed the final pytest regression.

## Example CLI Output

```text
Topic 10 — Dynamic Planning
============================================================

Start: ['at_home']
Goal: ['at_office']

Plan:
['take_backroad', 'park', 'walk_to_office']
```

## Evidence

The evidence directory contains structured JSON evidence for every required task:

- `task1_planning.json` — BFS planning and unreachable-goal behavior
- `task2_execution.json` — sequential execution and execution trace
- `task3_dynamic_replanning.json` — environment change and replanning
- `task4_replan_limits.json` — replan limits and safe failure
- `task5_extended_world.json` — new actions and new goal
- `test_summary.json` — final automated regression result

## Reflection

This project helped me understand the difference between static planning and dynamic planning in an executable system. A static planner can generate a valid sequence when the environment remains unchanged, but a practical agent cannot assume that the world will remain stable. The most important part of this activity was implementing replanning from the current state instead of restarting the entire process whenever something changes.

Using breadth-first search made the planning behavior deterministic and easy to validate because the first discovered goal path is a shortest path in terms of action count. I also learned that testing dynamic behavior requires carefully designed scenarios. A change only demonstrates replanning when the original plan is actually invalidated and a different valid route remains available. This made the tests more meaningful than simply changing an unused action.

The executor and planner were kept as separate responsibilities. This made it easier to validate planning independently from execution and then combine them in the dynamic runner. Adding a maximum replan limit was also important because unrestricted replanning could lead to repeated attempts without safe termination. The safe-failure tests show that the system can stop cleanly when the environment makes the goal unreachable.

Finally, extending the world with a new destination demonstrated that the planner is not tied to one fixed route. New actions and goals can be introduced while preserving the existing action definitions. Overall, this activity strengthened my understanding of state-space search, execution traces, environmental changes, replanning, bounded recovery, and defensive testing for agentic planning systems.
