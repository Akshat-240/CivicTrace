# Priority Engine Contract

The Priority Engine deterministically calculates the final priority for an incident. It is the sole owner of the `PriorityLevel` state, aggregating evidence-level AI observations into a holistic mathematical score.

## Core Rules

1. **Deterministic Execution**: Given the same severity, safety risk, and persistence, the engine must produce the exact same priority.
2. **Evidence Aggregation**:
   - **Severity**: The highest AI-perceived severity across all linked evidence.
   - **Safety Risk**: `True` if ANY linked evidence detected a safety risk.
3. **Mathematical Model**: No ML. No ambiguous ranking. Strict thresholds.

## Algorithm Parameters

- `WEIGHT_SEVERITY` = 0.5
- `WEIGHT_SAFETY` = 0.3
- `WEIGHT_PERSISTENCE` = 0.2

## Scoring Logic

### 1. Factor Extraction
*   **Severity Score**: Maps the highest `SeverityLevel` to a float.
    *   CRITICAL = 1.0
    *   HIGH = 0.75
    *   MEDIUM = 0.5
    *   LOW = 0.25
    *   (None = 0.0)
*   **Safety Score**: 1.0 if any safety risk is detected, else 0.0.
*   **Persistence Score**: Computes ongoing impact: 
    *   `min(1.0, (evidence_count * 0.1) + (days_active / 30.0))`

### 2. Weighted Sum
`Total Score = (Severity * 0.5) + (Safety * 0.3) + (Persistence * 0.2)`

### 3. Threshold Mapping
*   `Total Score >= 0.75` → **CRITICAL**
*   `Total Score >= 0.50` → **HIGH**
*   `Total Score >= 0.25` → **MEDIUM**
*   `Total Score < 0.25`  → **LOW**

## Explainability

Every priority calculation yields a human-readable explanation stored in the `Priority.explanation` column and timeline event.

Example:
> "Computed priority is HIGH (score: 0.65). Highest severity across 3 evidence items is HIGH. Safety risk was DETECTED. Persistence score is 0.30."

## Integration Flow
Invoked by the `PriorityService.compute_priority(incident_id)` method, which:
1. Calculates scores.
2. Upserts the `Priority` model attached to the `Incident`.
3. Creates a `PRIORITY_COMPUTED` or `PRIORITY_UPDATED` event in the timeline.
