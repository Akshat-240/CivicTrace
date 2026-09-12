# Incident Fusion Contract

The Incident Fusion subsystem determines whether newly processed `Evidence` belongs to an existing `Incident` or requires the creation of a new one. This ensures that multiple reports of the same issue (e.g., three people photographing the same pothole) are deduplicated deterministically.

## Core Rules

1. **Deterministic Scoring**: Fusion relies on a weighted mathematical score based on geographic proximity, time, and issue category.
2. **No ML Embeddings**: Fusion does not use vector databases or LLM similarity metrics. It is strictly algorithmic.
3. **Guardrails**:
   - Never merge if distance > `MAX_RADIUS_METERS`.
   - Never merge if the AI explicitly flagged the evidence as `ambiguous`.
   - Never merge if the time gap exceeds `MAX_TIME_DAYS`.

## Algorithm Parameters

- `MAX_RADIUS_METERS` = 50.0 meters
- `MAX_TIME_DAYS` = 14 days
- `WEIGHT_LOCATION` = 0.5
- `WEIGHT_CATEGORY` = 0.4
- `WEIGHT_TIME` = 0.1
- `MATCH_THRESHOLD` = 0.85

## Scoring Logic

Candidate incidents are pre-filtered to those within `MAX_RADIUS_METERS`, `MAX_TIME_DAYS`, and active statuses.

For each candidate:
1. **Location Score** = `max(0, 1.0 - (distance_in_meters / MAX_RADIUS_METERS))`
2. **Category Score** = `1.0` if `Evidence.ai_category == Incident.issue_type`, else `0.0`
3. **Time Score** = `max(0, 1.0 - (days_diff / MAX_TIME_DAYS))`
4. **Total Score** = `(Loc * 0.5) + (Cat * 0.4) + (Time * 0.1)`

If `max(Total Score) >= MATCH_THRESHOLD`, the evidence is appended to the winning `Incident` and its `evidence_count` is incremented.

If no candidate meets the threshold (or if the evidence is flagged as ambiguous), a *new* `Incident` is created based on the `Evidence`.

## Ambiguity Behavior

If `Evidence.ai_ambiguity_flag == True`, the system explicitly creates a new `Incident` and skips fusion. The new incident will have the `UNDER_REVIEW` state, flagging it for manual triage, because the system cannot safely fuse ambiguous data.

## Output

The service logs `INCIDENT_FUSED` or `INCIDENT_CREATED` to the incident's timeline with a human-readable explanation of the score.
