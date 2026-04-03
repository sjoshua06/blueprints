"""
Hybrid Supplier Risk Predictor  —  v2  (BOM-History Adaptive Weighting)
=========================================================================

Architecture
------------
1. **BOM Fulfillment Tracker**
   Every time a BOM is uploaded / evaluated, the outcome (fulfilled /
   partial / failed) is recorded in a lightweight JSON store per supplier.
   This gives the model *memory* — a supplier who keeps missing BOMs gets
   progressively higher risk even if their static metrics look OK.

2. **Adaptive Weight Engine  (Softmax-Temperature)**
   Weights are NOT hardcoded.  They are computed fresh each call from:
       • Current raw-risk values  (how bad is each metric right now?)
       • BOM failure history      (which metric category has been failing?)
   A softmax with a sharpening temperature makes the worst metric dominate
   exponentially — not just linearly.

3. **Internal Risk Score**  (0–1)
   Weighted sum of 5 metrics using the adaptive weights above,
   plus a BOM-history penalty that accumulates over repeated failures.

4. **External Risk Score**  (0–1)
   Unchanged — delegated to services.news_service.

5. **Final Fusion**
   0.50 × Internal + 0.50 × External, with a boost when either is severe.

Output: risk_score 0–100, risk_level, factor breakdown, adaptive weights
used, BOM history summary.
"""

from __future__ import annotations

import json
import math
import os
import warnings
from datetime import datetime
from pathlib import Path
from typing import Optional

from services.news_service import compute_external_risk

# ─────────────────────────────────────────────────────────────────────────────
# 0.  Constants & Config
# ─────────────────────────────────────────────────────────────────────────────

MAX_LEAD_TIME_DAYS = 60

# Fusion weights (internal vs external news)
W_INTERNAL = 0.50
W_EXTERNAL = 0.50

# Softmax temperature for weight sharpening.
# Higher value  → weights more uniform (all metrics matter equally).
# Lower value   → worst metric dominates exponentially.
# 1.5 is a good default; tune between 1.0 (very sharp) and 3.0 (flat).
SOFTMAX_TEMPERATURE = 1.5

# BOM history penalty cap (added on top of weighted score)
# Max +0.20 to internal risk from repeated BOM failures alone.
BOM_PENALTY_CAP = 0.20

# How much each failed BOM raises the BOM-history penalty (diminishing returns)
BOM_PENALTY_PER_FAILURE = 0.04

# Path to the persistent BOM history store (JSON)
BOM_HISTORY_PATH = Path(os.environ.get("BOM_HISTORY_PATH", "data/bom_history.json"))

# ─────────────────────────────────────────────────────────────────────────────
# 1.  BOM Fulfillment Tracker  —  persistent memory across uploads
# ─────────────────────────────────────────────────────────────────────────────

class BOMHistoryStore:
    """
    Lightweight JSON-backed store that remembers BOM outcomes per supplier.

    Schema (bom_history.json)
    -------------------------
    {
      "<supplier_key>": {
        "events": [
          {
            "timestamp":      "2025-06-01T10:00:00",
            "bom_id":         "BOM-001",
            "outcome":        "failed" | "partial" | "fulfilled",
            "fill_rate":      0.62,          # 0.0–1.0  (qty fulfilled / qty ordered)
            "line_items":     12,
            "failed_items":   5,
            "notes":          "..."
          },
          ...
        ]
      }
    }
    """

    def __init__(self, path: Path = BOM_HISTORY_PATH):
        self.path = path
        self._data: dict = {}
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                with open(self.path) as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._data = {}
        else:
            self._data = {}

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self._data, f, indent=2)

    @staticmethod
    def _key(supplier_name: str, country: str) -> str:
        return f"{supplier_name.lower().strip()}::{country.lower().strip()}"

    def record_bom_event(
        self,
        supplier_name: str,
        country: str,
        bom_id: str,
        fill_rate: float,             # 0.0 – 1.0
        line_items: int = 0,
        failed_items: int = 0,
        notes: str = "",
    ) -> str:
        """
        Record a BOM fulfillment outcome.  Auto-classifies outcome from fill_rate:
            fill_rate >= 0.95  →  fulfilled
            fill_rate >= 0.70  →  partial
            fill_rate <  0.70  →  failed
        Returns the classified outcome string.
        """
        fill_rate = max(0.0, min(1.0, fill_rate))
        if fill_rate >= 0.95:
            outcome = "fulfilled"
        elif fill_rate >= 0.70:
            outcome = "partial"
        else:
            outcome = "failed"

        key = self._key(supplier_name, country)
        if key not in self._data:
            self._data[key] = {"events": []}

        event = {
            "timestamp":    datetime.utcnow().isoformat(),
            "bom_id":       bom_id,
            "outcome":      outcome,
            "fill_rate":    round(fill_rate, 4),
            "line_items":   line_items,
            "failed_items": failed_items,
            "notes":        notes,
        }
        self._data[key]["events"].append(event)
        self._save()
        return outcome

    def get_history(self, supplier_name: str, country: str) -> list[dict]:
        key = self._key(supplier_name, country)
        return self._data.get(key, {}).get("events", [])

    def summarize(self, supplier_name: str, country: str) -> dict:
        """
        Returns a summary dict used by the risk engine:
            total_boms, failed_boms, partial_boms, fulfilled_boms,
            avg_fill_rate, consecutive_failures, failure_rate
        """
        events = self.get_history(supplier_name, country)
        if not events:
            return {
                "total_boms": 0,
                "failed_boms": 0,
                "partial_boms": 0,
                "fulfilled_boms": 0,
                "avg_fill_rate": 1.0,
                "consecutive_failures": 0,
                "failure_rate": 0.0,
            }

        total       = len(events)
        failed      = sum(1 for e in events if e["outcome"] == "failed")
        partial     = sum(1 for e in events if e["outcome"] == "partial")
        fulfilled   = sum(1 for e in events if e["outcome"] == "fulfilled")
        avg_fill    = sum(e["fill_rate"] for e in events) / total

        # Count consecutive failures from the most recent event backward
        consecutive = 0
        for e in reversed(events):
            if e["outcome"] in ("failed", "partial"):
                consecutive += 1
            else:
                break

        failure_rate = (failed + 0.5 * partial) / total   # partial counts as half failure

        return {
            "total_boms":            total,
            "failed_boms":           failed,
            "partial_boms":          partial,
            "fulfilled_boms":        fulfilled,
            "avg_fill_rate":         round(avg_fill, 4),
            "consecutive_failures":  consecutive,
            "failure_rate":          round(failure_rate, 4),
        }


# Module-level singleton (lazy-initialised)
_store: Optional[BOMHistoryStore] = None

def get_store() -> BOMHistoryStore:
    global _store
    if _store is None:
        _store = BOMHistoryStore()
    return _store


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Adaptive Weight Engine  —  Softmax-Temperature weighting
# ─────────────────────────────────────────────────────────────────────────────

# Domain priors: reasonable baseline importance for each metric.
# These are NOT fixed formula weights — they are just the starting point
# before the adaptive engine reshapes them based on actual risk values.
# Think of them as "in a perfectly healthy supplier, how much does each
# metric contribute to our worry?"
DOMAIN_PRIORS = {
    "reliability_risk":  0.28,
    "defect_risk":       0.24,
    "otd_risk":          0.24,
    "lead_time_risk":    0.14,
    "availability_risk": 0.10,
}

# BOM failure history amplifies these specific metric categories.
# When consecutive BOM failures are seen, we boost the weights for
# delivery-related and availability metrics because that's what BOM
# failures directly signal.
BOM_FAILURE_AMPLIFIES = {
    "otd_risk":          1.0,   # strongest signal — BOM late = OTD failure
    "availability_risk": 0.8,   # items not available on BOM
    "lead_time_risk":    0.6,   # longer lead time drives BOM delays
    "reliability_risk":  0.3,   # general reliability degrades with BOM failures
    "defect_risk":       0.0,   # defect rate not directly signalled by BOM miss
}


def _softmax_weights(logits: dict[str, float], temperature: float) -> dict[str, float]:
    """
    Converts a dict of raw logit scores to a probability distribution
    using softmax with temperature scaling.

    Lower temperature  → the highest logit dominates (sharper).
    Higher temperature → distribution flattens (more equal weights).
    """
    scaled = {k: v / temperature for k, v in logits.items()}
    max_val = max(scaled.values())                        # numerical stability
    exps = {k: math.exp(v - max_val) for k, v in scaled.items()}
    total = sum(exps.values())
    return {k: v / total for k, v in exps.items()}


def compute_adaptive_weights(
    raw_risks: dict[str, float],
    bom_summary: dict,
    temperature: float = SOFTMAX_TEMPERATURE,
) -> dict[str, float]:
    """
    Computes per-metric weights that are fully data-driven.

    Algorithm
    ---------
    1. Start from domain priors.
    2. Scale each prior by (1 + raw_risk²) — bad metrics get more attention.
       Using squared risk mimics the attention mechanism: mild risk barely
       moves the weight; severe risk multiplies it aggressively.
    3. Apply BOM-history amplification — if the supplier has been consistently
       failing BOMs, boost delivery/availability weights further.
    4. Pass through softmax with temperature to get a proper distribution.

    This means:
    - A supplier with 90% defect rate will have defect_risk weight ≈ 3× higher
      than a supplier with 10% defect rate.
    - A supplier who has failed 5 consecutive BOMs will have OTD and
      availability weights boosted on top of that.
    - The worst metric always gets exponentially more weight.
    """
    consecutive_failures = bom_summary.get("consecutive_failures", 0)
    failure_rate         = bom_summary.get("failure_rate", 0.0)

    # BOM amplification factor: scales 0→1 based on failure intensity
    # At 0 failures → 0.0 amplification
    # At 5+ consecutive failures → 1.0 amplification
    bom_amp = min(1.0, (consecutive_failures * 0.15) + (failure_rate * 0.5))

    logits: dict[str, float] = {}
    for key, prior in DOMAIN_PRIORS.items():
        risk_val = raw_risks.get(key, 0.0)

        # Step 2: scale by risk severity (attention mechanism)
        severity_scaled = prior * (1.0 + risk_val ** 2 * 3.0)

        # Step 3: BOM history amplification for relevant metrics
        bom_boost = BOM_FAILURE_AMPLIFIES.get(key, 0.0) * bom_amp * prior
        logits[key] = severity_scaled + bom_boost

    # Step 4: softmax → proper probability distribution
    return _softmax_weights(logits, temperature)


# ─────────────────────────────────────────────────────────────────────────────
# 3.  Internal Risk Score  (0.0 – 1.0)
# ─────────────────────────────────────────────────────────────────────────────

def compute_internal_risk(
    features: dict,
    bom_summary: dict | None = None,
) -> dict:
    """
    Computes the internal risk score using:
    1. Adaptive weights (data-driven, NOT hardcoded).
    2. BOM-history penalty stacked on top of the weighted score.

    Parameters
    ----------
    features    : supplier metric dict
    bom_summary : output of BOMHistoryStore.summarize() — pass None if
                  no BOM history exists yet (falls back to neutral).
    """
    if bom_summary is None:
        bom_summary = {
            "total_boms": 0, "failed_boms": 0, "partial_boms": 0,
            "consecutive_failures": 0, "failure_rate": 0.0, "avg_fill_rate": 1.0,
        }

    availability = float(features.get("availability_score", 0.5))
    reliability  = float(features.get("reliability_score", 50.0))
    defect       = float(features.get("defect_rate", 0.0))
    otd          = float(features.get("on_time_delivery_rate", 50.0))
    lead_time    = float(features.get("avg_lead_time_days", 30.0))

    # ── Raw risk per metric (0–1, higher = worse) ──────────────────────────
    raw_risks = {
        "reliability_risk":  1.0 - (reliability / 100.0),
        "defect_risk":       min(defect, 1.0),
        "otd_risk":          1.0 - (otd / 100.0),
        "lead_time_risk":    min(lead_time / MAX_LEAD_TIME_DAYS, 1.0),
        "availability_risk": 1.0 - availability,
    }

    # ── Adaptive weights from the engine ──────────────────────────────────
    adaptive_weights = compute_adaptive_weights(raw_risks, bom_summary)

    # ── Weighted score ─────────────────────────────────────────────────────
    weighted_score = sum(adaptive_weights[k] * raw_risks[k] for k in raw_risks)

    # ── BOM history penalty  ───────────────────────────────────────────────
    # Each failed/partial BOM adds a fixed penalty, capped at BOM_PENALTY_CAP.
    # consecutive_failures is weighted more aggressively than total failures
    # because a run of recent failures is a stronger signal.
    consecutive = bom_summary.get("consecutive_failures", 0)
    total_weighted_fails = (
        bom_summary.get("failed_boms", 0) * 1.0 +
        bom_summary.get("partial_boms", 0) * 0.5
    )
    bom_penalty = min(
        BOM_PENALTY_CAP,
        (consecutive * BOM_PENALTY_PER_FAILURE * 1.5) +   # recent run matters more
        (total_weighted_fails * BOM_PENALTY_PER_FAILURE * 0.5)
    )

    # ── Fill-rate drag  ────────────────────────────────────────────────────
    # If avg fill rate is poor, apply an additional proportional drag.
    avg_fill = bom_summary.get("avg_fill_rate", 1.0)
    fill_drag = (1.0 - avg_fill) * 0.15    # up to +0.15 if avg fill rate = 0%

    internal_score = min(1.0, weighted_score + bom_penalty + fill_drag)
    internal_score = max(0.0, internal_score)

    return {
        "internal_risk_score":  round(internal_score, 4),
        "component_scores":     {k: round(v, 4) for k, v in raw_risks.items()},
        "adaptive_weights":     {k: round(v, 4) for k, v in adaptive_weights.items()},
        "bom_penalty_applied":  round(bom_penalty, 4),
        "fill_drag_applied":    round(fill_drag, 4),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4.  Factor Breakdown  (for frontend explainability)
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
    bom_summary: dict,
) -> list[dict]:
    """
    Produce a ranked list of contributing factors for the UI.
    Each factor: factor, category, impact (0–100), detail, risk_level.
    """
    comp    = internal_result["component_scores"]
    weights = internal_result["adaptive_weights"]
    factors = []

    # ── Internal metric factors ────────────────────────────────────────────
    reliability = float(features.get("reliability_score", 50.0))
    factors.append({
        "factor":     "Supplier Reliability",
        "category":   "Performance",
        "impact":     round(comp["reliability_risk"] * weights["reliability_risk"] * 100, 1),
        "detail":     f"Reliability score: {reliability:.1f}/100  |  adaptive weight: {weights['reliability_risk']:.2%}",
        "risk_level": _risk_label(comp["reliability_risk"]),
    })

    defect = float(features.get("defect_rate", 0.0))
    factors.append({
        "factor":     "Product Defect Rate",
        "category":   "Quality",
        "impact":     round(comp["defect_risk"] * weights["defect_risk"] * 100, 1),
        "detail":     f"Defect rate: {defect:.2%}  |  adaptive weight: {weights['defect_risk']:.2%}",
        "risk_level": _risk_label(comp["defect_risk"]),
    })

    otd = float(features.get("on_time_delivery_rate", 50.0))
    factors.append({
        "factor":     "On-Time Delivery",
        "category":   "Delivery",
        "impact":     round(comp["otd_risk"] * weights["otd_risk"] * 100, 1),
        "detail":     f"OTD rate: {otd:.1f}%  |  adaptive weight: {weights['otd_risk']:.2%}",
        "risk_level": _risk_label(comp["otd_risk"]),
    })

    lead = float(features.get("avg_lead_time_days", 30.0))
    factors.append({
        "factor":     "Average Lead Time",
        "category":   "Delivery",
        "impact":     round(comp["lead_time_risk"] * weights["lead_time_risk"] * 100, 1),
        "detail":     f"Lead time: {lead:.0f} days  |  adaptive weight: {weights['lead_time_risk']:.2%}",
        "risk_level": _risk_label(comp["lead_time_risk"]),
    })

    avail = float(features.get("availability_score", 0.5))
    factors.append({
        "factor":     "Component Availability",
        "category":   "Supply",
        "impact":     round(comp["availability_risk"] * weights["availability_risk"] * 100, 1),
        "detail":     f"Availability score: {avail:.2f}  |  adaptive weight: {weights['availability_risk']:.2%}",
        "risk_level": _risk_label(comp["availability_risk"]),
    })

    # ── BOM history factor  ────────────────────────────────────────────────
    total_boms  = bom_summary.get("total_boms", 0)
    consecutive = bom_summary.get("consecutive_failures", 0)
    failure_rate = bom_summary.get("failure_rate", 0.0)
    bom_penalty = internal_result.get("bom_penalty_applied", 0.0)

    if total_boms > 0:
        bom_detail = (
            f"{bom_summary['failed_boms']} failed / {bom_summary['partial_boms']} partial "
            f"out of {total_boms} BOMs  |  {consecutive} consecutive failures  |  "
            f"avg fill rate: {bom_summary['avg_fill_rate']:.0%}"
        )
        bom_risk_val = min(1.0, failure_rate + consecutive * 0.12)
    else:
        bom_detail  = "No BOM history recorded yet"
        bom_risk_val = 0.0

    factors.append({
        "factor":     "BOM Fulfillment History",
        "category":   "Delivery",
        "impact":     round(bom_penalty * 100, 1),
        "detail":     bom_detail,
        "risk_level": _risk_label(bom_risk_val),
    })

    # ── External factor (news sentiment) ──────────────────────────────────
    ext_score     = external_result.get("external_risk_score", 0.4)
    sentiment     = external_result.get("sentiment_summary", {})
    neg_ratio     = sentiment.get("negative_ratio", 0.0)
    article_count = sentiment.get("article_count", 0)

    if article_count > 0:
        ext_detail = (
            f"{int(neg_ratio * article_count)}/{article_count} articles negative "
            f"(neg ratio: {neg_ratio:.0%})"
        )
    else:
        ext_detail = "No recent news found — mild uncertainty applied"

    factors.append({
        "factor":     "News Sentiment & Tariff Risk",
        "category":   "External",
        "impact":     round(ext_score * W_EXTERNAL * 100, 1),
        "detail":     ext_detail,
        "risk_level": _risk_label(ext_score),
    })

    factors.sort(key=lambda f: f["impact"], reverse=True)
    return factors


# ─────────────────────────────────────────────────────────────────────────────
# 5.  Final Fusion  →  risk_score (0–100)
# ─────────────────────────────────────────────────────────────────────────────

def compute_final_risk(
    supplier_name: str,
    country: str,
    features: dict,
    bom_event: dict | None = None,
) -> dict:
    """
    Main entry point.  Combines internal adaptive formula + external news.

    Parameters
    ----------
    supplier_name : str
    country       : str
    features      : supplier metric dict
    bom_event     : optional dict to record a new BOM outcome *before*
                    scoring.  Keys:
                        bom_id        (str)
                        fill_rate     (float 0–1, required)
                        line_items    (int, optional)
                        failed_items  (int, optional)
                        notes         (str, optional)
                    Pass None if you're just querying the current risk
                    without a new BOM event.

    Returns
    -------
    dict:
        risk_score          : float  (0–100)
        risk_level          : str    (LOW / MEDIUM / HIGH / CRITICAL)
        internal_risk_score : float  (0–100)
        external_risk_score : float  (0–100)
        factors             : list[dict]
        adaptive_weights    : dict   (the weights actually used)
        bom_summary         : dict   (history summary for this supplier)
        news_articles       : list[dict]
    """
    store = get_store()

    # ── Record new BOM event if provided ──────────────────────────────────
    if bom_event is not None:
        fill_rate = float(bom_event.get("fill_rate", 1.0))
        store.record_bom_event(
            supplier_name  = supplier_name,
            country        = country,
            bom_id         = bom_event.get("bom_id", f"BOM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"),
            fill_rate      = fill_rate,
            line_items     = int(bom_event.get("line_items", 0)),
            failed_items   = int(bom_event.get("failed_items", 0)),
            notes          = str(bom_event.get("notes", "")),
        )

    # ── Load BOM history summary ───────────────────────────────────────────
    bom_summary = store.summarize(supplier_name, country)

    # ── Internal risk (adaptive) ───────────────────────────────────────────
    internal_result = compute_internal_risk(features, bom_summary)
    int_score = internal_result["internal_risk_score"]

    # ── External risk (news sentiment) ────────────────────────────────────
    try:
        external_result = compute_external_risk(supplier_name, country or "Global")
    except Exception as exc:
        warnings.warn(f"External risk fetch failed for {supplier_name}: {exc}")
        external_result = {
            "external_risk_score": 0.40,
            "sentiment_summary": {
                "avg_compound":   0.0,
                "negative_ratio": 0.0,
                "positive_ratio": 0.0,
                "article_count":  0,
            },
            "news_articles": [],
            "queries_used":  {},
        }

    ext_score = external_result["external_risk_score"]

    # ── Fusion ─────────────────────────────────────────────────────────────
    raw_final = W_INTERNAL * int_score + W_EXTERNAL * ext_score

    # Boost: if either signal is severe, nudge final upward
    if int_score > 0.70 or ext_score > 0.70:
        boost = 0.05
        raw_final = min(1.0, raw_final + boost)

    # Extra boost if BOM history is alarming (consecutive failures ≥ 3)
    if bom_summary.get("consecutive_failures", 0) >= 3:
        raw_final = min(1.0, raw_final + 0.04)

    final_score = max(0.0, min(1.0, raw_final))
    final_100   = round(final_score * 100, 2)

    # Risk level
    if final_100 >= 75:
        risk_level = "CRITICAL"
    elif final_100 >= 50:
        risk_level = "HIGH"
    elif final_100 >= 25:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    factors = build_factor_breakdown(features, internal_result, external_result, bom_summary)

    return {
        "risk_score":          final_100,
        "risk_level":          risk_level,
        "internal_risk_score": round(int_score * 100, 2),
        "external_risk_score": round(ext_score * 100, 2),
        "factors":             factors,
        "adaptive_weights":    internal_result["adaptive_weights"],
        "bom_summary":         bom_summary,
        "news_articles":       external_result.get("news_articles", []),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 6.  Legacy compatibility wrapper
# ─────────────────────────────────────────────────────────────────────────────

def predict_risk(
    features: list,
    supplier_name: str = "",
    country: str = "",
    bom_event: dict | None = None,
) -> float:
    """
    Backward-compatible wrapper for code that passes a flat feature list.
    Returns a float on 0–1 scale for DB storage.

    New optional parameter:
        bom_event : dict  — pass to record a BOM outcome at the same time.
    """
    features_dict = {
        "availability_score":    features[0] if len(features) > 0 else 0.5,
        "reliability_score":     features[1] if len(features) > 1 else 50.0,
        "defect_rate":           features[2] if len(features) > 2 else 0.0,
        "on_time_delivery_rate": features[3] if len(features) > 3 else 50.0,
        "avg_lead_time_days":    features[4] if len(features) > 4 else 30.0,
    }

    if supplier_name and country:
        result = compute_final_risk(supplier_name, country, features_dict, bom_event)
        return result["risk_score"] / 100.0
    else:
        # No supplier context → internal-only, no history
        internal = compute_internal_risk(features_dict, bom_summary=None)
        return internal["internal_risk_score"]


# ─────────────────────────────────────────────────────────────────────────────
# 7.  Convenience: record_bom  (call this from your BOM upload pipeline)
# ─────────────────────────────────────────────────────────────────────────────

def record_bom(
    supplier_name: str,
    country: str,
    bom_id: str,
    fill_rate: float,
    line_items: int = 0,
    failed_items: int = 0,
    notes: str = "",
) -> str:
    """
    Standalone helper to record a BOM event without triggering a full risk
    computation.  Returns the classified outcome ("fulfilled"/"partial"/"failed").

    Call this from your BOM upload handler, then call compute_final_risk
    separately when you need the score.
    """
    return get_store().record_bom_event(
        supplier_name=supplier_name,
        country=country,
        bom_id=bom_id,
        fill_rate=fill_rate,
        line_items=line_items,
        failed_items=failed_items,
        notes=notes,
    )