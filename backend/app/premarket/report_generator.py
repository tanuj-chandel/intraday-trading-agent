import datetime
from typing import Dict, Any, List

class PreMarketReportGenerator:
    """
    Generates a formatted, publication-ready Indian Pre-Market Intelligence Report.
    """

    @classmethod
    def generate_report(
        cls,
        market_overview: str,
        global_cues: Dict[str, Any],
        gift_nifty: Dict[str, Any],
        indices: Dict[str, Any],
        sector_strengths: Dict[str, float],
        top_longs: List[Dict[str, Any]],
        top_shorts: List[Dict[str, Any]],
        high_impact_news: List[Dict[str, Any]],
        market_regime: str,
        risk_level: str = "MODERATE"
    ) -> str:
        date_str = datetime.datetime.now().strftime("%A, %d %B %Y - %H:%M IST")
        
        strongest_sectors = sorted(sector_strengths.items(), key=lambda x: x[1], reverse=True)[:3]
        weakest_sectors = sorted(sector_strengths.items(), key=lambda x: x[1])[:2]

        lines = [
            "=" * 70,
            "               INDIAN MARKET PRE-MARKET INTELLIGENCE REPORT",
            "=" * 70,
            f"Date: {date_str}",
            "Operational Mode: PAPER TRADING / SIMULATION ONLY",
            f"Market Regime: {market_regime.replace('_', ' ')}",
            f"Overall Risk Level: {risk_level}",
            "-" * 70,
            "",
            "1. GLOBAL CUES & GIFT NIFTY STANCE",
            f" - Global Score: {global_cues.get('global_market_score', 0.0):+0.1f}/100 ({global_cues.get('sentiment', 'NEUTRAL')})",
            f" - US Equities: {global_cues.get('us_trend', 'POSITIVE')} | Asian Equities: {global_cues.get('asia_trend', 'MIXED')}",
            f" - Crude Oil (Brent): {global_cues.get('crude_oil_stance', 'STABLE')}",
            f" - GIFT NIFTY: {gift_nifty.get('gift_nifty_price', 0.0):,.2f} ({gift_nifty.get('gap_points', 0.0):+0.2f} pts / {gift_nifty.get('gap_pct', 0.0):+0.2f}%) [{gift_nifty.get('gap_direction', 'FLAT')} - {gift_nifty.get('gap_magnitude', 'MODERATE')}]",
            f"   (Data Source: {gift_nifty.get('source', 'MOCK')})",
            "",
            "2. DOMESTIC BENCHMARKS & VOLATILITY",
        ]

        for sym, data in indices.items():
            if sym == "INDIA VIX":
                lines.append(f" - INDIA VIX: {data.get('current_price', 13.5):.2f} ({data.get('change_pct', 0.0):+0.2f}%) -> {data.get('volatility_stance', 'NORMAL')}")
            else:
                lines.append(f" - {sym}: ₹{data.get('current_price', 0.0):,.2f} ({data.get('change_pct', 0.0):+0.2f}%)")

        lines.extend([
            "",
            "3. SECTOR ROTATION & RELATIVE STRENGTH",
            f" - Outperforming Sectors: {', '.join([f'{s[0]} ({s[1]:.0f}/100)' for s in strongest_sectors])}",
            f" - Underperforming Sectors: {', '.join([f'{s[0]} ({s[1]:.0f}/100)' for s in weakest_sectors])}",
            "",
            "4. HIGH-IMPACT CORPORATE & REGULATORY NEWS",
        ])

        for n in high_impact_news[:4]:
            lines.append(f" - [{n.get('source_reliability', 'LEVEL_2')} | {n.get('source')}] {n.get('headline')} (Impact: {n.get('sentiment')})")

        lines.extend([
            "",
            "5. TOP RECOMMENDED LONG CANDIDATES (BULLISH ALIGNMENT)",
        ])
        for idx, s in enumerate(top_longs[:5], start=1):
            lines.append(
                f" {idx}. {s['symbol']} ({s['sector']}) | Score: {s['total_score']:.1f}/100 | CMP: ₹{s['current_price']:,.2f}\n"
                f"    Zone: {s['entry_zone']} | SL: ₹{s['stop_loss']:,.2f} | TGT: ₹{s['target']:,.2f} | R:R 1:{s['risk_reward_ratio']:.1f}\n"
                f"    Setup: {s['reason']}"
            )

        lines.extend([
            "",
            "6. TOP RECOMMENDED SHORT CANDIDATES (BEARISH ALIGNMENT)",
        ])
        for idx, s in enumerate(top_shorts[:5], start=1):
            lines.append(
                f" {idx}. {s['symbol']} ({s['sector']}) | Score: {s['total_score']:.1f}/100 | CMP: ₹{s['current_price']:,.2f}\n"
                f"    Zone: {s['entry_zone']} | SL: ₹{s['stop_loss']:,.2f} | TGT: ₹{s['target']:,.2f} | R:R 1:{s['risk_reward_ratio']:.1f}\n"
                f"    Setup: {s['reason']}"
            )

        lines.extend([
            "",
            "7. OPERATIONAL GUARDRAILS",
            " - No automated trade execution will occur without operator human approval.",
            " - Strictly Paper Trading simulation mode active.",
            " - Hard daily loss cutoff at 15:15 IST.",
            "=" * 70
        ])

        return "\n".join(lines)
