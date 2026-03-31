"""
News API integration + VADER sentiment analysis for external supplier risk.

Fetches articles about a supplier (by name, country, and tariff keywords),
runs VADER sentiment on each headline+description, and produces an
external risk score between 0.0 and 1.0.
"""

import os
import time
import requests
import warnings
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ── VADER setup ──────────────────────────────────────────────────────────────
from nltk.sentiment.vader import SentimentIntensityAnalyzer

_sia = SentimentIntensityAnalyzer()

# ── Config ───────────────────────────────────────────────────────────────────
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
NEWS_API_BASE = "https://newsapi.org/v2/everything"
CACHE_TTL_SECONDS = 24 * 60 * 60  # 24-hour cache per supplier

# ── In-memory cache  ────────────────────────────────────────────────────────
# Key: "supplier_name|country"  →  { "timestamp": epoch, "result": {...} }
_news_cache: dict = {}


# ─────────────────────────────────────────────────────────────────────────────
# 1.  Fetch articles from NewsAPI
# ─────────────────────────────────────────────────────────────────────────────

def _call_news_api(query: str, page_size: int = 10) -> list[dict]:
    """Call newsapi.org/v2/everything and return a list of article dicts."""
    if not NEWS_API_KEY:
        warnings.warn("NEWS_API_KEY not set – skipping news fetch")
        return []

    from_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

    try:
        resp = requests.get(
            NEWS_API_BASE,
            params={
                "q": query,
                "from": from_date,
                "sortBy": "relevancy",
                "pageSize": page_size,
                "language": "en",
                "apiKey": NEWS_API_KEY,
            },
            timeout=10,
        )
        if resp.status_code != 200:
            warnings.warn(f"NewsAPI returned {resp.status_code}: {resp.text[:200]}")
            return []

        data = resp.json()
        return data.get("articles", [])
    except Exception as e:
        warnings.warn(f"NewsAPI request failed: {e}")
        return []


def fetch_supplier_news(supplier_name: str, country: str) -> dict:
    """
    Fetch news articles using 3 targeted queries:
    1. Direct supplier mentions
    2. Country + supply chain disruption
    3. Country + tariff / trade policy

    Returns:
        {
            "supplier_articles": [...],
            "country_articles": [...],
            "tariff_articles": [...],
            "all_articles": [...]   ← deduplicated union
        }
    """
    # Query 1 – supplier name
    q_supplier = f'"{supplier_name}" supply chain'
    supplier_articles = _call_news_api(q_supplier, page_size=5)

    # Query 2 – country disruptions
    q_country = f'"{country}" supply chain disruption OR shortage OR delay'
    country_articles = _call_news_api(q_country, page_size=5)

    # Query 3 – tariffs & trade policy
    q_tariff = f'"{country}" tariff OR trade war OR sanctions OR import duty'
    tariff_articles = _call_news_api(q_tariff, page_size=5)

    # Deduplicate by URL
    seen_urls = set()
    all_articles = []
    for art in supplier_articles + country_articles + tariff_articles:
        url = art.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            all_articles.append(art)

    return {
        "supplier_articles": supplier_articles,
        "country_articles": country_articles,
        "tariff_articles": tariff_articles,
        "all_articles": all_articles,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Sentiment analysis with VADER
# ─────────────────────────────────────────────────────────────────────────────

def _label_from_compound(compound: float) -> str:
    if compound >= 0.05:
        return "POSITIVE"
    elif compound <= -0.05:
        return "NEGATIVE"
    return "NEUTRAL"


def analyze_sentiment(articles: list[dict]) -> dict:
    """
    Run VADER on each article's title+description.

    Returns:
        {
            "avg_compound": float,      # average VADER compound  (-1 … +1)
            "negative_ratio": float,    # fraction of articles scored NEGATIVE
            "positive_ratio": float,
            "neutral_ratio": float,
            "article_count": int,
            "scored_articles": [
                {
                    "title": str,
                    "source": str,
                    "url": str,
                    "published_at": str,
                    "compound": float,
                    "sentiment": "POSITIVE" | "NEGATIVE" | "NEUTRAL"
                }
            ]
        }
    """
    if not articles:
        return {
            "avg_compound": 0.0,
            "negative_ratio": 0.0,
            "positive_ratio": 0.0,
            "neutral_ratio": 1.0,
            "article_count": 0,
            "scored_articles": [],
        }

    scored = []
    compounds = []

    for art in articles:
        title = art.get("title") or ""
        desc = art.get("description") or ""
        text = f"{title}. {desc}"

        scores = _sia.polarity_scores(text)
        compound = scores["compound"]
        compounds.append(compound)

        scored.append({
            "title": title,
            "source": (art.get("source") or {}).get("name", "Unknown"),
            "url": art.get("url", ""),
            "published_at": art.get("publishedAt", ""),
            "compound": round(compound, 3),
            "sentiment": _label_from_compound(compound),
        })

    n = len(compounds)
    neg_count = sum(1 for c in compounds if c <= -0.05)
    pos_count = sum(1 for c in compounds if c >= 0.05)
    neu_count = n - neg_count - pos_count

    return {
        "avg_compound": round(sum(compounds) / n, 3),
        "negative_ratio": round(neg_count / n, 3),
        "positive_ratio": round(pos_count / n, 3),
        "neutral_ratio": round(neu_count / n, 3),
        "article_count": n,
        "scored_articles": scored,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3.  External risk score  (0.0 – 1.0)
# ─────────────────────────────────────────────────────────────────────────────

def compute_external_risk(supplier_name: str, country: str) -> dict:
    """
    Orchestrator: fetch news → sentiment → risk score.

    Risk mapping:
        negative_ratio ≥ 0.60  →  0.85 – 1.0   (CRITICAL)
        negative_ratio ≥ 0.40  →  0.60 – 0.85   (HIGH)
        negative_ratio ≥ 0.20  →  0.35 – 0.60   (MEDIUM)
        negative_ratio <  0.20  →  0.10 – 0.35   (LOW)
        no articles at all     →  0.40           (UNKNOWN — mild risk)

    Returns:
        {
            "external_risk_score": float (0.0 – 1.0),
            "sentiment_summary": { ... },
            "news_articles": [ ... ],
            "queries_used": { ... }
        }
    """
    # ── Check cache ──
    cache_key = f"{supplier_name.lower().strip()}|{country.lower().strip()}"
    cached = _news_cache.get(cache_key)
    if cached and (time.time() - cached["timestamp"]) < CACHE_TTL_SECONDS:
        return cached["result"]

    # ── Fetch & analyse ──
    news_data = fetch_supplier_news(supplier_name, country)
    all_articles = news_data["all_articles"]
    sentiment = analyze_sentiment(all_articles)

    # ── Convert to risk score ──
    if sentiment["article_count"] == 0:
        # No news = mild uncertainty risk
        risk_score = 0.40
    else:
        neg_ratio = sentiment["negative_ratio"]
        avg_compound = sentiment["avg_compound"]

        # Primary driver: negative article ratio
        # Secondary driver: how negative the compound is (adds nuance)
        base_risk = neg_ratio  # 0.0 – 1.0

        # Compound adjustment: very negative compound text pushes risk up
        # avg_compound ranges from -1 to +1; invert and normalize to 0–1
        compound_factor = (1 - avg_compound) / 2  # -1→1.0, 0→0.5, +1→0.0

        risk_score = 0.65 * base_risk + 0.35 * compound_factor

        # Clamp to a reasonable floor / ceiling
        risk_score = max(0.05, min(0.95, risk_score))

    result = {
        "external_risk_score": round(risk_score, 4),
        "sentiment_summary": {
            "avg_compound": sentiment["avg_compound"],
            "negative_ratio": sentiment["negative_ratio"],
            "positive_ratio": sentiment["positive_ratio"],
            "article_count": sentiment["article_count"],
        },
        "news_articles": sentiment["scored_articles"][:8],  # top 8
        "queries_used": {
            "supplier_query": f'"{supplier_name}" supply chain',
            "country_query": f'"{country}" supply chain disruption',
            "tariff_query": f'"{country}" tariff OR trade war OR sanctions',
        },
    }

    # ── Cache ──
    _news_cache[cache_key] = {"timestamp": time.time(), "result": result}

    return result
