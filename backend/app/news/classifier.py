from typing import Tuple

EVENT_CATEGORIES = [
    "Earnings",
    "Order win",
    "Management change",
    "M&A",
    "Regulatory",
    "Government policy",
    "Legal",
    "Rating change",
    "Dividend",
    "Fund raising",
    "Bankruptcy/default",
    "Product launch",
    "Macro",
    "Commodity",
    "Other"
]

class NewsClassifier:
    """
    Classifies corporate and financial news into 15 domain-specific event categories.
    """

    @classmethod
    def classify_headline(cls, headline: str) -> Tuple[str, str]:
        """
        Returns (event_category, default_impact)
        """
        h = headline.lower()

        # Check Regulatory and Macro first to prevent false positive on words like margin or rate
        if any(w in h for w in ["sebi", "rbi guidelines", "penalty", "inspection", "audit directive", "margin requirement", "compliance", "regulatory"]):
            return "Regulatory", "HIGH"
        elif any(w in h for w in ["gdp", "cpi", "inflation", "gift nifty", "fed rate", "rate cut", "repo rate", "fii", "dii", "monetary policy"]):
            return "Macro", "HIGH"
        elif any(w in h for w in ["net profit", "quarterly profit", "revenue", "quarterly result", "ebitda", "operating margin", "q1", "q2", "q3", "q4", "earnings", "financial results"]):
            return "Earnings", "HIGH"
        elif any(w in h for w in ["order win", "contract", "secures", "bagged", "mega project", "capex", "epc", "order"]) and any(w in h for w in ["order", "contract", "deal", "project", "cr", "crore"]):
            return "Order win", "HIGH"
        elif any(w in h for w in ["acquisition", "merger", "m&a", "stake", "buyout", "takeover"]):
            return "M&A", "HIGH"
        elif any(w in h for w in ["ceo", "cfo", "md", "board", "management change", "resigns", "appoints", "leadership"]):
            return "Management change", "MEDIUM"
        elif any(w in h for w in ["gst", "policy", "cabinet", "ministry", "budget", "tariff", "subsidy", "pli", "government"]):
            return "Government policy", "HIGH"
        elif any(w in h for w in ["court", "nclt", "litigation", "supreme court", "lawsuit", "tribunal", "legal"]):
            return "Legal", "MEDIUM"
        elif any(w in h for w in ["upgrade", "downgrade", "target price", "rating", "brokerage view", "reiterate"]):
            return "Rating change", "MEDIUM"
        elif any(w in h for w in ["dividend", "bonus", "buyback", "split"]):
            return "Dividend", "MEDIUM"
        elif any(w in h for w in ["qip", "ipo", "fpo", "rights issue", "fund raise", "bonds issue", "preferential"]):
            return "Fund raising", "MEDIUM"
        elif any(w in h for w in ["default", "insolvency", "bankruptcy", "npa", "debt resolution", "distress"]):
            return "Bankruptcy/default", "HIGH"
        elif any(w in h for w in ["launch", "unveils", "ev", "partnership", "collaboration", "nvidia", "expansion", "factory", "gigafactory"]):
            return "Product launch", "MEDIUM"
        elif any(w in h for w in ["crude", "brent", "gold", "metal", "oil", "opec", "steel price", "commodity"]):
            return "Commodity", "MEDIUM"
        else:
            return "Other", "LOW"
