"""
AI perception normalization layer for CivicTrace.
Decouples CivicTrace-specific civic domain vocabulary and category mapping
from the underlying raw AI providers (Azure Computer Vision, Azure AI Language).
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.models.enums import IssueType
from app.schemas.ai import LanguagePerceptionResult

logger = logging.getLogger(__name__)

# CivicTrace domain vocabulary rules for text normalization
CIVIC_TEXT_CATEGORY_RULES: dict[IssueType, list[str]] = {
    IssueType.POTHOLE: [
        "pothole", "potholes", "crater", "gaddha", "gaddhe", "cavity", "road hole"
    ],
    IssueType.ROAD_DAMAGE: [
        "broken road", "asphalt", "road depression", "sinkhole", "uneven road",
        "tar", "road crack", "caved road", "road damage"
    ],
    IssueType.ILLEGAL_DUMPING: [
        "garbage", "trash", "waste", "dumping", "rubbish", "kachra", "debris",
        "litter", "overflowing bin", "dump yard", "plastic waste", "filth", "dump"
    ],
    IssueType.WATER_LEAK: [
        "pipe burst", "water leak", "water pipe", "pipeline", "water gushing",
        "drinking water", "water supply", "broken pipe", "leakage", "water waste"
    ],
    IssueType.SEWAGE_OVERFLOW: [
        "sewer", "sewage", "gutter", "drain", "overflowing drain", "blocked drain",
        "nallah", "foul smell", "stagnant water", "manhole overflow", "backflow"
    ],
    IssueType.FLOODING: [
        "flooding", "waterlogging", "submerged", "water logged", "inundated"
    ],
    IssueType.BROKEN_STREETLIGHT: [
        "streetlight", "street light", "lamp post", "light not working",
        "flickering light", "dark road", "street lamp", "pole light", "dark spot",
        "bulb broken", "no light"
    ],
    IssueType.DAMAGED_SIGNAGE: [
        "traffic sign", "broken sign", "signboard", "damaged board", "sign post"
    ],
    IssueType.OVERGROWN_VEGETATION: [
        "fallen tree", "tree branch", "tree collapse", "uprooted tree",
        "blocking road tree", "fallen branch", "broken tree", "overgrown bushes", "weed"
    ],
    IssueType.GRAFFITI: [
        "graffiti", "defaced wall", "illegal poster", "wall vandalism"
    ],
    IssueType.ABANDONED_VEHICLE: [
        "abandoned car", "abandoned vehicle", "junk car", "broken vehicle"
    ],
    IssueType.NOISE_COMPLAINT: [
        "loud noise", "loudspeaker", "noise pollution", "blaring horn"
    ],
    IssueType.OTHER: [
        "hazard", "exposed wire", "electric wire", "live wire", "sparking",
        "transformer", "high voltage", "open manhole"
    ],
}

CIVIC_TEXT_SAFETY_HAZARDS = [
    "exposed wire", "electric shock", "live wire", "sparking", "high voltage",
    "open manhole", "deep ditch", "sinkhole", "gas leak", "collapse risk",
    "danger", "hazardous", "dangerous", "risk to life", "accident risk"
]

CIVIC_TEXT_IMPACT_TERMS = [
    "traffic jam", "traffic block", "school bus", "school", "pedestrian",
    "flooding", "water entering house", "accident", "injuries", "hospital",
    "foul smell", "disease", "mosquitos", "dark road", "rain", "children"
]


def normalize_language_perception(
    raw_result: LanguagePerceptionResult,
    text: str,
) -> LanguagePerceptionResult:
    """
    Applies CivicTrace domain vocabulary normalization over genuine key phrases
    and text received from Azure AI Language.
    Leaves confidence untouched (None) as Azure Language does not provide scalar confidence.
    """
    if raw_result.status != "success":
        return raw_result

    searchable_corpus = f"{text} {' '.join(raw_result.key_phrases)}".lower()

    # 1. Match civic category and issue terms
    detected_category: Optional[IssueType] = None
    matched_issue_terms: list[str] = []

    best_match_count = 0
    for issue_type, keywords in CIVIC_TEXT_CATEGORY_RULES.items():
        count = sum(1 for kw in keywords if kw in searchable_corpus)
        if count > 0:
            matched_terms = [kw for kw in keywords if kw in searchable_corpus]
            matched_issue_terms.extend(matched_terms)
            if count > best_match_count:
                best_match_count = count
                detected_category = issue_type

    # 2. Extract impact phrases
    matched_impact_phrases: list[str] = [
        term for term in CIVIC_TEXT_IMPACT_TERMS if term in searchable_corpus
    ]

    # 3. Detect safety hazards
    safety_risk = any(hazard in searchable_corpus for hazard in CIVIC_TEXT_SAFETY_HAZARDS)

    # 4. Generate summary
    cat_name = detected_category.value.upper() if detected_category else "UNCATEGORIZED"
    summary = f"Citizen briefing normalized to {cat_name}: \"{text.strip()}\""

    return LanguagePerceptionResult(
        status="success",
        detected_category=detected_category,
        issue_terms=list(dict.fromkeys(matched_issue_terms))[:10],
        key_phrases=raw_result.key_phrases,
        entities=raw_result.entities,
        impact_phrases=list(dict.fromkeys(matched_impact_phrases))[:10],
        safety_risk_detected=safety_risk,
        confidence=None,  # Confidence is not fabricated for key phrase extraction
        summary=summary,
        provider=raw_result.provider,
    )
