# Architecture Decision Records

## ADR 1: Modular Monolith
**Status:** Accepted
**Context:** The system needs to be end-to-end operational without premature complexity. Microservices or complex event-driven architectures introduce unnecessary operational overhead for an MVP.
**Decision:** We will use a modular monolith architecture with a Python FastAPI backend.
**Consequences:** Easier debugging, simplified deployment, clean service boundaries enforced by Python module structures. Cross-domain communication happens via function calls rather than network hops.

## ADR 2: Deterministic Incident Fusion
**Status:** Accepted
**Context:** We need a simple, explainable way to deduplicate or group incident evidence. Complex ML deduplication is opaque and prone to edge-case failures.
**Decision:** We will use deterministic weighted matching (e.g., same category + proximity within X meters + within Y hours) to group related evidence into a single fused incident.
**Consequences:** Clear, predictable grouping of issues. Easy to trace why two reports were linked and adjust thresholds.

## ADR 3: Relational + Spatial Database
**Status:** Accepted
**Context:** We need to store structured incident data, handle spatial queries (GIS/Jurisdiction mapping), and enforce data integrity.
**Decision:** We will use PostgreSQL with the PostGIS extension.
**Consequences:** Robust spatial queries, transactional guarantees, single datastore for relational and GIS data.

## ADR 4: AI Perception Boundary
**Status:** Accepted
**Context:** AI must only be used for perception, extraction, and ambiguity handling, NOT for final accountability decisions.
**Decision:** AI services will purely output structured representations of evidence (e.g., categories, extracted text, estimated severity). The deterministic core business logic will determine priority and accountability based on this structured data.
**Consequences:** Decisions remain deterministic and auditable. AI failure modes are isolated to data extraction.

## ADR 5: Explainability & Predictability
**Status:** Accepted
**Context:** Priority, accountability, and verification need to be explainable and robust.
**Decision:** 
- Priority is determined purely by discrete factors: Severity, Safety, Persistence.
- Accountability states progress linearly: Pending → Due → Overdue → Escalation Eligible.
- Verification states: Fully Resolved, Partially Resolved, Unresolved, Insufficient Evidence.
**Consequences:** Rules-based system for core states, easily displayed on dashboards and justifiable to stakeholders.
