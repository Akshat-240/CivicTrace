# GIS and Jurisdiction Contract

The GIS subsystem determines the responsible civic authority for an incident by evaluating its geographic coordinates against known administrative boundaries.

## Core Rules

1. **Deterministic Assignment**: Jurisdiction is assigned purely by spatial containment (`ST_Contains` or `ST_Intersects`). AI must never guess or override the jurisdiction.
2. **Explicit Fallbacks**: If coordinates are invalid, missing, or do not fall within any known boundary, the system must explicitly enter a conflict/review state rather than guessing.
3. **Correct Coordinate Ordering**: PostGIS uses `(longitude, latitude)` ordering for geometries. Longitude is X, Latitude is Y.

## Input

The GIS service accepts:
- `latitude` (Float): Decimal degrees, range -90 to 90.
- `longitude` (Float): Decimal degrees, range -180 to 180.

## Output (Structured Result)

The GIS service returns a strongly-typed `JurisdictionResult` containing:

```json
{
  "status": "JURISDICTION_FOUND",
  "jurisdiction_id": "uuid-of-jurisdiction",
  "authority_id": "uuid-of-authority",
  "explanation": "Location falls within City Council Ward 4 boundary, mapped to City Public Works."
}
```

### Status Codes

- `JURISDICTION_FOUND`: A single clear administrative boundary was matched.
- `NO_JURISDICTION`: Coordinates are valid but fall outside all known civic boundaries.
- `JURISDICTION_CONFLICT`: Coordinates fall into overlapping boundaries with conflicting authorities.
- `INVALID_LOCATION`: Coordinates are missing or mathematically invalid (e.g. latitude > 90).

## Database Interaction

The service executes a PostGIS query directly against the `jurisdictions` table:

```sql
SELECT id, name, authority_id 
FROM jurisdictions 
WHERE ST_Contains(
    boundary, 
    ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)
)
```

## Integration Flow

1. An Incident or Evidence is created with a `Location`.
2. The `GISService.resolve_jurisdiction(lat, lng)` is invoked.
3. The result determines the `jurisdiction_id` and `authority_id` for the `Incident`.
4. The database is updated and an `Event` (`JURISDICTION_ASSIGNED` / `AUTHORITY_ASSIGNED` or a failure note) is written to the Incident Timeline.
