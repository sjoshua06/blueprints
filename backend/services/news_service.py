"""
NewsData.io integration + VADER sentiment analysis for external supplier risk.

Fetches articles about a supplier's country (supply chain disruptions, tariffs),
runs VADER sentiment on each headline+description, and produces an
external risk score between 0.0 and 1.0. Cached at the country level to prevent API exhaustion.
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
# Use the explicit key provided by the user as default fallback
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "pub_bb013016d1aa493b8f45fec0fd1ab971")
NEWS_API_BASE = "https://newsdata.io/api/1/news"
CACHE_TTL_SECONDS = 24 * 60 * 60  # 24-hour cache per country

# ── In-memory cache  ────────────────────────────────────────────────────────
# Key: "country"  →  { "timestamp": epoch, "articles": [...] }
_news_cache: dict = {}


# ─────────────────────────────────────────────────────────────────────────────
# 1.  Fetch articles from NewsData.io
# ─────────────────────────────────────────────────────────────────────────────

def _call_news_api(query: str, size: int = 10) -> list[dict]:
    """Call newsdata.io and return a list of article dicts."""
    if not NEWS_API_KEY:
        warnings.warn("NEWS_API_KEY not set – skipping news fetch")
        return []

    try:
        resp = requests.get(
            NEWS_API_BASE,
            params={
                "q": query,
                "language": "en",
                "apikey": NEWS_API_KEY,
                "size": size,
            },
            timeout=10,
        )
        if resp.status_code != 200:
            warnings.warn(f"NewsData returned {resp.status_code}: {resp.text[:200]}")
            return []

        data = resp.json()
        return data.get("results", [])
    except Exception as e:
        warnings.warn(f"NewsData request failed: {e}")
        return []


def fetch_country_news(country: str) -> list[dict]:
    """
    Fetch news articles using 1 targeted query per country:
    This prevents exhausting API limits when checking 500 suppliers.
    """
    # Query – country disruptions & tariffs
    q_country = f'"{country}" AND ("supply chain" OR "tariff" OR "shortage" OR "disruption" OR "trade")'
    articles = _call_news_api(q_country, size=10)
    
    # Deduplicate by link
    seen_urls = set()
    all_articles = []
    for art in articles:
        url = art.get("link", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            all_articles.append(art)
            
    return all_articles


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

        # Handle NewsData.io structure mappings directly
        source_id = art.get("source_id", "Unknown")
        
        scored.append({
            "title": title,
            "source": source_id,
            "url": art.get("link", ""),
            "published_at": art.get("pubDate", ""),
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
    Orchestrator: fetch country news → sentiment → risk score.
    """
    # ── Check cache BY COUNTRY to drop API calls from 500 -> ~10 ──
    cache_key = country.lower().strip()
    
    cached = _news_cache.get(cache_key)
    if cached and (time.time() - cached["timestamp"]) < CACHE_TTL_SECONDS:
        all_articles = cached["articles"]
    else:
        all_articles = fetch_country_news(country)
        # ── Cache immediately ──
        _news_cache[cache_key] = {"timestamp": time.time(), "articles": all_articles}

    sentiment = analyze_sentiment(all_articles)

    # ── Convert to risk score ──
    if sentiment["article_count"] == 0:
        # No news = mild uncertainty risk
        risk_score = 0.40
    else:
        neg_ratio = sentiment["negative_ratio"]
        avg_compound = sentiment["avg_compound"]

        base_risk = neg_ratio  # 0.0 – 1.0

        # Compound adjustment: very negative compound text pushes risk up
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
            "country_query": f'"{country}" AND ("supply chain" OR "tariff" OR "shortage" OR "disruption" OR "trade")',
        },
    }

    return result
