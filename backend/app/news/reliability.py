from enum import Enum
from typing import Dict

class SourceReliability(str, Enum):
    LEVEL_1 = "LEVEL_1"  # Official filing/exchange (NSE, BSE, Company Disclosures)
    LEVEL_2 = "LEVEL_2"  # Reputable financial media (Reuters, ET, Moneycontrol, LiveMint, CNBC-TV18)
    LEVEL_3 = "LEVEL_3"  # Unverified / Blogs / Aggregators / Other

SOURCE_RELIABILITY_MAP: Dict[str, SourceReliability] = {
    "NSE": SourceReliability.LEVEL_1,
    "BSE": SourceReliability.LEVEL_1,
    "SEBI": SourceReliability.LEVEL_1,
    "Company Filing": SourceReliability.LEVEL_1,
    "PIB India": SourceReliability.LEVEL_1,
    "Reuters": SourceReliability.LEVEL_2,
    "Bloomberg": SourceReliability.LEVEL_2,
    "Economic Times": SourceReliability.LEVEL_2,
    "Moneycontrol": SourceReliability.LEVEL_2,
    "LiveMint": SourceReliability.LEVEL_2,
    "CNBC-TV18": SourceReliability.LEVEL_2,
    "Business Standard": SourceReliability.LEVEL_2,
    "NDTV Profit": SourceReliability.LEVEL_2,
    "Financial Express": SourceReliability.LEVEL_2,
}

def get_source_reliability(source_name: str) -> SourceReliability:
    for key, val in SOURCE_RELIABILITY_MAP.items():
        if key.lower() in source_name.lower():
            return val
    return SourceReliability.LEVEL_3
