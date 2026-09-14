# AI Perception Contract

The AI Perception subsystem is responsible for extracting structured data from raw civic issue evidence (images and text) using the Gemini API.

## Core Rules

1. **Perception Only**: AI identifies physical attributes, categorizes issues, and assesses visible severity/safety.
2. **No Authority Assignment**: AI must *never* determine who is responsible (e.g. City vs State).
3. **No GIS Inference**: AI must *never* guess the jurisdiction boundaries.
4. **Ambiguity Over Fabrication**: If an image is blurry or evidence is insufficient, the AI must explicitly flag it as ambiguous rather than inventing facts.

## Input (To AI Provider)

The AI provider requires:
- `evidence_id`: UUID of the evidence being analyzed.
- `description`: User-provided description of the issue.
- `media_urls`: (Optional) List of presigned URLs or base64 images if local. For MVP, we pass text descriptions and image references if available.

## Output (Structured Output from AI)

The AI model is instructed to return a strictly typed JSON response matching the `AIAnalysisResult` Pydantic schema:

```json
{
  "civic_issue_category": "pothole",
  "confidence": 0.85,
  "severity_assessment": "medium",
  "safety_risk_detected": false,
  "ambiguity_flag": false,
  "ambiguity_reason": null,
  "extracted_attributes": {
    "approximate_size": "2 feet wide",
    "surface_type": "asphalt"
  },
  "explanation": "Image clearly shows a moderately sized pothole on an asphalt road."
}
```

## Validation & Confidence

- **Categories**: Must map to known `IssueType` (or unmapped strings depending on exact design, but mapped is better).
- **Confidence**: Must be a float between `0.0` and `1.0`.
- **Ambiguity**: If `ambiguity_flag` is `true`, `ambiguity_reason` should be populated and `confidence` may be low.

## Integration Flow

1. Evidence is submitted via POST `/api/v1/incidents/{id}/evidence`.
2. Status is set to `PENDING`.
3. Background task / async process invokes `AIService.analyze_evidence(evidence_id)`.
4. Status changes to `PROCESSING`.
5. `GeminiAIProvider` calls the Gemini API with the system prompt and JSON schema.
6. Result is validated via Pydantic.
7. Database fields on `Evidence` are updated (`ai_category`, `ai_confidence`, `ai_severity_raw`, `ai_safety_risk`, `ai_perception_payload`, `ai_ambiguity_flag`, `ai_ambiguity_reason`).
8. Status changes to `PROCESSED` (or `FAILED` if validation or network error occurs).

## Caching (Development & MVP)

To prevent redundant Gemini calls during E2E testing or demos, the provider implements a deterministic cache based on a hash of the input parameters.
