"""
Hybrid Supplier Risk Predictor
================================
Combines two signals:

1. **Internal Risk** — weighted formula over the supplier's own metrics
   (reliability, defect rate, on-time delivery, lead time, availability).

2. **External Risk** — real-time News API sentiment analysis about the
   supplier name, country, and tariff / trade-policy keywords.

Final risk = 0.50 × Internal + 0.50 × External  (with boost for critical)
Output is on a 0–100 scale with a factor breakdown.
"""

import warnings
from services.news_service import compute_external_risk

# ── Weight configuration ─────────────────────────────────────────────────────
# Internal formula weights (must sum to 1.0)
W_RELIABILITY   = 0.25
W_DEFECT        = 0.25
W_OTD           = 0.25
W_LEAD_TIME     = 0.15
W_AVAILABILITY  = 0.10

# Fusion weights
W_INTERNAL = 0.50
W_EXTERNAL = 0.50

# Maximum expected lead time (for normalization)
MAX_LEAD_TIME_DAYS = 60


# ─────────────────────────────────────────────────────────────────────────────
# 1.  Internal Risk Score  (0.0 – 1.0)
# ─────────────────────────────────────────────────────────────────────────────

def compute_internal_risk(features: dict) -> dict:
    """
    Deterministic, weighted formula over supplier metrics.

    Parameters
    ----------
    features : dict with keys
        availability_score      (0.0 – 1.0)
        reliability_score       (0 – 100)
        defect_rate             (0.0 – 1.0, where 1.0 = 100% defective)
        on_time_delivery_rate   (0 – 100)
        avg_lead_time_days      (integer, days)

    Returns
    -------
    dict with:
        internal_risk_score : float (0.0 – 1.0)
        component_scores    : dict  (individual sub-scores for explainability)
    """
    availability   = float(features.get("availability_score", 0.5))
    reliability    = float(features.get("reliability_score", 50.0))
    defect         = float(features.get("defect_rate", 0.0))
    otd            = float(features.get("on_time_delivery_rate", 50.0))
    lead_time      = float(features.get("avg_lead_time_days", 30.0))

    # Each sub-score is 0.0–1.0 where higher = more risky
    reliability_risk   = 1.0 - (reliability / 100.0)
    defect_risk        = min(defect, 1.0)                          # already 0–1
    otd_risk           = 1.0 - (otd / 100.0)
    lead_time_risk     = min(lead_time / MAX_LEAD_TIME_DAYS, 1.0)
    availability_risk  = 1.0 - availability

    internal_score = (
        W_RELIABILITY  * reliability_risk  +
        W_DEFECT       * defect_risk       +
        W_OTD          * otd_risk          +
        W_LEAD_TIME    * lead_time_risk    +
        W_AVAILABILITY * availability_risk
    )

    internal_score = max(0.0, min(1.0, internal_score))

    return {
        "internal_risk_score": round(internal_score, 4),
        "component_scores": {
            "reliability_risk":  round(reliability_risk, 4),
            "defect_risk":       round(defect_risk, 4),
            "otd_risk":          round(otd_risk, 4),
            "lead_time_risk":    round(lead_time_risk, 4),
            "availability_risk": round(availability_risk, 4),
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Factor Breakdown  (for frontend explainability)
# ─────────────────────────────────────────────────────────────────────────────

def _risk_label(value: float) -> str:
    if value >= 0.75:
        return "CRITICAL"
    if value >= 0.50:
        return "HIGH"
    if value >= 0.25:
        return "MEDIUM"
    return "LOW"


def build_factor_breakdown(
    features: dict,
    internal_result: dict,
    external_result: dict,
) -> list[dict]:
    """
    Produce a ranked list of contributing factors for the UI.
    Each factor has: factor, category, impact (0–100), detail.
    """
    comp = internal_result["component_scores"]
    factors = []

    # ── Internal factors ─────────────────────────────────────────────────────
    reliability = float(features.get("reliability_score", 50.0))
    factors.append({
        "factor": "Supplier Reliability",
        "category": "Performance",
        "impact": round(comp["reliability_risk"] * W_RELIABILITY * 100, 1),
        "detail": f"Reliability score: {reliability:.1f}/100",
        "risk_level": _risk_label(comp["reliability_risk"]),
    })

    defect = float(features.get("defect_rate", 0.0))
    factors.append({
        "factor": "Product Defect Rate",
        "category": "Quality",
        "impact": round(comp["defect_risk"] * W_DEFECT * 100, 1),
        "detail": f"Defect rate: {defect:.2%}",
        "risk_level": _risk_label(comp["defect_risk"]),
    })

    otd = float(features.get("on_time_delivery_rate", 50.0))
    factors.append({
        "factor": "On-Time Delivery",
        "category": "Delivery",
        "impact": round(comp["otd_risk"] * W_OTD * 100, 1),
        "detail": f"OTD rate: {otd:.1f}%",
        "risk_level": _risk_label(comp["otd_risk"]),
    })

    lead = float(features.get("avg_lead_time_days", 30.0))
    factors.append({
        "factor": "Average Lead Time",
        "category": "Delivery",
        "impact": round(comp["lead_time_risk"] * W_LEAD_TIME * 100, 1),
        "detail": f"Lead time: {lead:.0f} days",
        "risk_level": _risk_label(comp["lead_time_risk"]),
    })

    avail = float(features.get("availability_score", 0.5))
    factors.append({
        "factor": "Component Availability",
        "category": "Supply",
        "impact": round(comp["availability_risk"] * W_AVAILABILITY * 100, 1),
        "detail": f"Availability score: {avail:.2f}",
        "risk_level": _risk_label(comp["availability_risk"]),
    })

    # ── External factor (news sentiment) ─────────────────────────────────────
    ext_score = external_result.get("external_risk_score", 0.4)
    sentiment = external_result.get("sentiment_summary", {})
    neg_ratio = sentiment.get("negative_ratio", 0.0)
    article_count = sentiment.get("article_count", 0)

    if article_count > 0:
        detail = f"{int(neg_ratio * article_count)}/{article_count} articles negative (neg ratio: {neg_ratio:.0%})"
    else:
        detail = "No recent news found — mild uncertainty"

    factors.append({
        "factor": "News Sentiment & Tariff Risk",
        "category": "External",
        "impact": round(ext_score * W_EXTERNAL * 100, 1),
        "detail": detail,
        "risk_level": _risk_label(ext_score),
    })

    # Sort by impact descending
    factors.sort(key=lambda f: f["impact"], reverse=True)
    return factors


# ─────────────────────────────────────────────────────────────────────────────
# 3.  Final Fusion  →  risk_score (0–100)
# ─────────────────────────────────────────────────────────────────────────────

def compute_final_risk(
    supplier_name: str,
    country: str,
    features: dict,
) -> dict:
    """
    Main entry point.  Combines internal formula + external news sentiment.

    Returns
    -------
    dict with:
        risk_score          : float (0–100)
        risk_level          : str   (LOW / MEDIUM / HIGH / CRITICAL)
        internal_risk_score : float (0–100)
        external_risk_score : float (0–100)
        factors             : list[dict]
        news_articles       : list[dict]
    """
    # ── Internal ──
    internal_result = compute_internal_risk(features)
    int_score = internal_result["internal_risk_score"]

    # ── External ──
    try:
        external_result = compute_external_risk(supplier_name, country or "Global")
    except Exception as e:
        warnings.warn(f"External risk fetch failed for {supplier_name}: {e}")
        external_result = {
            "external_risk_score": 0.40,
            "sentiment_summary": {
                "avg_compound": 0.0,
                "negative_ratio": 0.0,
                "positive_ratio": 0.0,
                "article_count": 0,
            },
            "news_articles": [],
            "queries_used": {},
        }

    ext_score = external_result["external_risk_score"]

    # ── Fusion ──
    raw_final = W_INTERNAL * int_score + W_EXTERNAL * ext_score

    # Boost: if either signal is very high, nudge final upward
    if int_score > 0.70 or ext_score > 0.70:
        boost = 0.05
        raw_final = min(1.0, raw_final + boost)

    final_score = max(0.0, min(1.0, raw_final))
    final_100 = round(final_score * 100, 2)

    # Risk level
    if final_100 >= 75:
        risk_level = "CRITICAL"
    elif final_100 >= 50:
        risk_level = "HIGH"
    elif final_100 >= 25:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # Factor breakdown
    factors = build_factor_breakdown(features, internal_result, external_result)

    return {
        "risk_score": final_100,
        "risk_level": risk_level,
        "internal_risk_score": round(int_score * 100, 2),
        "external_risk_score": round(ext_score * 100, 2),
        "factors": factors,
        "news_articles": external_result.get("news_articles", []),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4.  Legacy compatibility wrapper
# ─────────────────────────────────────────────────────────────────────────────

def predict_risk(features: list, supplier_name: str = "", country: str = "") -> float:
    """
    Backward-compatible function for code that still passes a flat list.
    Returns a simple float risk_score (0–1 scale) for DB storage.
    """
    features_dict = {
        "availability_score":     features[0] if len(features) > 0 else 0.5,
        "reliability_score":      features[1] if len(features) > 1 else 50.0,
        "defect_rate":            features[2] if len(features) > 2 else 0.0,
        "on_time_delivery_rate":  features[3] if len(features) > 3 else 50.0,
        "avg_lead_time_days":     features[4] if len(features) > 4 else 30.0,
    }

    if supplier_name and country:
        result = compute_final_risk(supplier_name, country, features_dict)
        return result["risk_score"] / 100.0  # return 0–1 for DB column
    else:
        # No supplier context – return internal-only score
        internal = compute_internal_risk(features_dict)
        return internal["internal_risk_score"]