# Resolution Verification Contract

Resolution Verification determines whether an incident is actually resolved based *only* on submitted "after" evidence, rejecting authority claims if they lack proof.

## Core Rules

1. **Evidence-Driven**: Verification requires at least one processed Evidence item marked as `is_verification_evidence = True`.
2. **Deterministic Comparison**: The engine compares the state of the "after" evidence against the incident's original severity.
3. **No Automatic Closure**: Merely triggering verification does not close an incident. The evidence must support it.

## State Logic

Each valid "after" evidence item is evaluated individually:
- **No Issue Found**: If `ai_category` differs from the incident's `issue_type`, the evidence shows no trace of the original issue.
- **Improved**: If the `ai_category` matches, but the mapped `ai_severity_raw` is strictly lower than the incident's original severity.
- **Unresolved**: If the `ai_category` matches and the mapped `ai_severity_raw` is greater than or equal to the original severity.

**Aggregation**:
- **INSUFFICIENT_EVIDENCE**: If no "after" evidence exists, or if ALL "after" evidence is flagged as `ai_ambiguity_flag = True` (poor/unusable).
- **UNRESOLVED**: If ANY valid "after" evidence is scored as `Unresolved`. (Contradictory evidence defaults to safety).
- **PARTIALLY_RESOLVED**: If the highest remaining evidence score is `Improved`.
- **FULLY_RESOLVED**: If ALL valid "after" evidence scores as `No Issue Found` (or explicitly `RESOLVED` by severity).

## Outcomes and Effects

- If `FULLY_RESOLVED`:
  - Incident `status` → `RESOLVED`
  - SLA `state` → `RESOLVED`
  - SLA `resolved_at` → `now()`
- Any other result keeps the incident `ACTIVE` (or `UNDER_REVIEW`) and leaves the SLA clock running.

## AI Dependency
Verification relies entirely on the deterministic fields extracted during the prior `AI Perception` phase (`ai_category`, `ai_severity_raw`, `ai_ambiguity_flag`). It does not execute new CV models.
