# GIS Jurisdiction Contract

The GIS service determines which jurisdiction is responsible for an incident based on geographic location.

## Input (To GIS Service)
Coordinates from the reported evidence.

```json
{
  "latitude": 34.0522,
  "longitude": -118.2437
}
```

## Output (From GIS Service)
The GIS service returns the closest or exactly overlapping jurisdiction.

```json
{
  "jurisdiction_id": "jur_la_dot",
  "name": "Los Angeles Department of Transportation",
  "sla_tier": "standard",
  "boundary_distance_meters": 0,
  "is_exact_match": true
}
```
*Note: If `is_exact_match` is false, `boundary_distance_meters` indicates distance to the nearest mapped jurisdiction.*
