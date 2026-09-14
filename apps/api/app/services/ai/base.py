"""
Abstract AI Provider interface.
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.schemas.ai import AIAnalysisResult


class AIProvider(ABC):
    """
    Base abstraction for AI perception providers.
    """

    @abstractmethod
    async def analyze_evidence(
        self, description: Optional[str], media_urls: list[str], media_content: Optional[bytes] = None
    ) -> AIAnalysisResult:
        """
        Analyze the given evidence and return a validated structured result.
        
        Raises CivicTraceError subclasses for timeouts, rate limits, or invalid output.
        """
        pass
