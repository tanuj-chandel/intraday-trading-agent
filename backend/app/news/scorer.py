from typing import Dict, Any
from app.news.reliability import SourceReliability

class NewsImpactScorer:
    """
    Computes an explainable News Impact Score and sentiment confidence weighting.
    """

    @classmethod
    def calculate_impact(
        cls,
        sentiment_score: float,  # -1.0 to +1.0
        event_category: str,
        reliability: SourceReliability
    ) -> Dict[str, Any]:
        # Reliability Multiplier
        if reliability == SourceReliability.LEVEL_1:
            rel_weight = 1.0  # Official Exchange filing has 100% confidence weight
            confidence = 0.95
        elif reliability == SourceReliability.LEVEL_2:
            rel_weight = 0.85
            confidence = 0.80
        else:
            rel_weight = 0.60
            confidence = 0.60

        # Event Weighting
        high_impact_events = ["Earnings", "Order win", "M&A", "Regulatory", "Bankruptcy/default", "Government policy"]
        event_weight = 1.2 if event_category in high_impact_events else 0.9

        # Raw Impact Score (-100 to +100)
        raw_impact = sentiment_score * 100.0 * rel_weight * event_weight
        clamped_impact = round(min(100.0, max(-100.0, raw_impact)), 1)

        # 0 to 100 normalized score
        normalized_0_100 = round(50.0 + (clamped_impact * 0.5), 1)

        direction = "BULLISH" if clamped_impact > 15.0 else ("BEARISH" if clamped_impact < -15.0 else "NEUTRAL")

        return {
            "impact_score": normalized_0_100,
            "net_directional_impact": clamped_impact,
            "direction": direction,
            "confidence": confidence,
            "reliability_weight": rel_weight
        }
