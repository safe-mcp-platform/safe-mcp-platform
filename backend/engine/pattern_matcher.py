"""
Pattern Matching Engine
Regex-based detection with confidence scoring
"""

import re
from typing import List
import structlog

from utils.types import PatternResult

logger = structlog.get_logger()


class PatternMatcher:
    """Pattern matching engine using regex."""
    
    def __init__(self):
        self.pattern_cache = {}  # Cache compiled regexes
    
    def match(
        self,
        text: str,
        patterns: List[str],
        case_sensitive: bool = False
    ) -> PatternResult:
        """
        Match text against patterns.
        
        Args:
            text: Text to analyze
            patterns: List of regex patterns
            case_sensitive: Whether matching is case-sensitive
        
        Returns:
            PatternResult with matches and confidence
        """
        if not patterns:
            return PatternResult(triggered=False, confidence=0.0)
        
        matched_patterns = []
        
        for pattern in patterns:
            try:
                # Compile and cache regex
                cache_key = f"{pattern}_{case_sensitive}"
                if cache_key not in self.pattern_cache:
                    flags = 0 if case_sensitive else re.IGNORECASE
                    self.pattern_cache[cache_key] = re.compile(pattern, flags)
                
                regex = self.pattern_cache[cache_key]
                
                # Check for match
                if regex.search(text):
                    matched_patterns.append(pattern)
                    
            except re.error as e:
                logger.warning(f"Invalid regex pattern: {pattern}", error=str(e))
                continue
        
        # Calculate confidence based on number of matches
        if not matched_patterns:
            return PatternResult(
                triggered=False,
                confidence=0.0,
                patterns_matched=[]
            )
        
        # Confidence increases with more matches, caps at 1.0
        # Base: 1.0 for critical patterns (T1102, T1105), 0.8+ for others
        # This ensures patterns alone can trigger blocking
        confidence = min(0.95 + (len(matched_patterns) - 1) * 0.05, 1.0)
        
        return PatternResult(
            triggered=True,
            confidence=confidence,
            patterns_matched=matched_patterns
        )
    
    def clear_cache(self):
        """Clear regex compilation cache."""
        self.pattern_cache.clear()
        logger.debug("Pattern cache cleared")


# Global instance
_pattern_matcher = None


def get_pattern_matcher() -> PatternMatcher:
    """Get global pattern matcher instance."""
    global _pattern_matcher
    if _pattern_matcher is None:
        _pattern_matcher = PatternMatcher()
    return _pattern_matcher

