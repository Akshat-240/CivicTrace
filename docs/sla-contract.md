# Accountability and SLA Contract

The Accountability Engine enforces the resolution deadlines set by a civic Authority. It deterministically computes due dates and advances the state of an Incident's SLA.

## Core Principles
1. **Deterministic Dependency**: SLA calculation requires both an **Authority** (determined by GIS) and a **PriorityLevel** (determined by Priority Engine).
2. **Authority Ownership**: The authority explicitly defines their own SLA windows (in hours) for each priority tier (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
3. **Testable Time**: The engine relies on timezone-aware UTC timestamps and accepts injected clocks for deterministic testing.
4. **Append-Only Tracking**: State changes emit Timeline events.

## Initialization
When an incident is confirmed and transitioned to `ACTIVE`:
1. `started_at = NOW()`
2. `due_at = started_at + Authority.sla_hours_<priority>`
3. SLA state = `PENDING`

## State Machine Execution
A background evaluation periodically checks active SLAs against the current time.

- `PENDING` → `DUE`: Transitions if `now() >= (due_at - DUE_WARNING_HOURS)`.
- `PENDING`/`DUE` → `OVERDUE`: Transitions if `now() >= due_at`. Sets `overdue_at`.
- `OVERDUE` → `ESCALATION_ELIGIBLE`: Transitions if `now() >= (due_at + ESCALATION_DELAY_HOURS)`. Sets `escalated_at` and `is_escalation_eligible = True`.

## Configurable Thresholds
- `DUE_WARNING_HOURS`: Default 24 hours. (Incident becomes DUE when less than 24 hours remain).
- `ESCALATION_DELAY_HOURS`: Default 72 hours. (Incident becomes eligible for escalation if not resolved 3 days after deadline).
