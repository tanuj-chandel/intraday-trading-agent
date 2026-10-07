# News Sentiment Intelligence Pipeline

## 1. Overview
The News Sentiment Intelligence Pipeline ingests, normalizes, validates, and evaluates news articles and exchange filings for Indian equities in real-time. It provides sentiment direction, impact scoring, and alpha score adjustments to protect the system from trading against major news catalysts.

---

## 2. Architecture & Data Flow

```
[Official Exchanges & Tier-1 Financial Media]
  ├── NSE / BSE Corporate Announcements (Regulatory Filings)
  ├── Press Information Bureau (PIB India - Macro & RBI)
  ├── Live Financial Media (Moneycontrol, LiveMint, ET, Reuters)
        │
        ▼ (Async RSS / Webhook Ingestion)
[News Aggregator (app/news/aggregator.py)]
  ├── Timestamp Parsing & Validation
  ├── Latency Calculation: (Now - PublishedAt)
  ├── Symbol Entity Extraction (Regex & Keyword Mapping)
        │
        ▼
[Sentiment & Impact Classifier (app/news/classifier.py & scorer.py)]
  ├── Keyword Hit-Rate: Bullish vs Bearish Keywords
  ├── Event Categorization: EARNINGS, ORDER_WIN, REGULATORY, MACRO
  ├── Source Reliability Weighting (NSE/BSE = 1.0, Tier-1 = 0.85)
        │
        ▼
[Freshness Gate (NEWS_MAX_AGE_MINUTES)]
  ├── Discard / Ignore if Age > NEWS_MAX_AGE_MINUTES (Default 120 mins)
        │
        ▼
[Alpha Score Integration (app/scoring/scorer.py)]
  ├── Capped Contribution: NEWS_MAX_ALPHA_WEIGHT (Default 10.0 / 100 points)
```

---

## 3. Data Sources & Source Reliability
Each incoming news item is mapped to a verified source reliability tier:

| Source Tier | Examples | Reliability Score | Description |
|-------------|----------|-------------------|-------------|
| **Exchange Primary** | NSE Corporate Filings, BSE Disclosures | 1.00 | Official statutory disclosures, dividend, order wins |
| **Government / Central Bank** | PIB India, RBI Announcements | 0.95 | Macro policy, GDP data, Repo rate decisions |
| **Tier-1 Financial Media** | Moneycontrol, LiveMint, Reuters | 0.85 | Verified editorial market reports |
| **Broad Market RSS** | Google News Finance Feed | 0.70 | Aggregated web headlines |

---

## 4. Timestamp & Ingestion Latency
1. **Timestamp Extraction**:
   - Primary timestamp is extracted from RFC-822 / ISO-8601 `pubDate` headers.
   - If missing or corrupt, system clock `datetime.datetime.now()` is applied as fallback.
2. **Ingestion Latency**:
   - Latency is calculated as: `Latency_seconds = (Ingestion_Time - Published_Time)`.
   - Items with latency > 300 seconds are flagged as historical rather than breaking.
3. **Freshness Filter (`NEWS_MAX_AGE_MINUTES = 120`)**:
   - Any news published more than `NEWS_MAX_AGE_MINUTES` ago is flagged as `stale`.
   - Stale news returns `sentiment_score = 0.0` and is ignored for live trade signal generation.

---

## 5. Sentiment Scoring Algorithm
1. **Keyword Analysis**:
   - **Bullish keywords**: `surge`, `jumps`, `profit rises`, `order win`, `expands`, `upgraded`, `record revenue`, `dividend`.
   - **Bearish keywords**: `plunges`, `drops`, `profit falls`, `loss`, `fraud`, `penalty`, `sebi ban`, `downgraded`, `default`.
2. **Formula**:
   $$\text{Score} = \begin{cases} 
   \min(+0.90, 0.40 + 0.15 \times \text{BullishHits}) & \text{if BullishHits} > \text{BearishHits} \\
   \max(-0.90, -0.40 - 0.15 \times \text{BearishHits}) & \text{if BearishHits} > \text{BullishHits} \\
   0.00 & \text{otherwise}
   \end{cases}$$
3. **Impact Scorer**:
   Combines sentiment score with event category and source reliability to compute `impact_score` (-100 to +100).

---

## 6. Alpha Score Weight & Capping
- The Multi-Factor Intraday Alpha Scorer (`backend/app/scoring/scorer.py`) ranks trades on a 0 - 100 scale.
- **Configurable Cap**: The maximum contribution of news sentiment is capped at `NEWS_MAX_ALPHA_WEIGHT` (default: **10.0 points**).
- Neutral news provides $0.5 \times \text{NEWS\_MAX\_ALPHA\_WEIGHT} = 5.0$ points.
- Strong positive news adds up to $+5.0$ points (total 10.0 points).
- Strong negative news subtracts up to $-5.0$ points (total 0.0 points).

---

## 7. Trade Protection Gates
- **Adverse News Block**: If `sentiment_score < -0.30`, all new BUY entries for the symbol are blocked.
- **Bullish News Block on Shorting**: If `sentiment_score > +0.30`, all new SELL entries for the symbol are blocked.
