import math

def clean(val, default=0):
    try:
        if val is None:
            return default
        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
            return default
        return val
    except:
        return default


def _build_component_name_map(supabase):
    """Fetch all components and return a {component_id: component_name} dict."""
    rows = supabase.table("components").select("component_id,component_name").execute().data
    return {r["component_id"]: r["component_name"] for r in rows}


def _enrich(prediction, name_map):
    """Add component_name to a prediction dict based on component_id."""
    enriched = dict(prediction)
    cid = enriched.get("component_id")
    enriched["component_name"] = name_map.get(cid, f"Unknown (ID {cid})")
    return enriched


def get_all_predictions(supabase):
    response = supabase.table("internal_risk_predictions").select("*").execute()
    name_map = _build_component_name_map(supabase)
    return [_enrich(r, name_map) for r in response.data]

def get_prediction_by_component(supabase, component_id: int):
    response = (
        supabase.table("internal_risk_predictions")
        .select("*")
        .eq("component_id", component_id)
        .execute()
    )
    if not response.data:
        return None
    name_map = _build_component_name_map(supabase)
    return _enrich(response.data[0], name_map)

def get_high_risk_components(supabase):
    response = (
        supabase.table("internal_risk_predictions")
        .select("*")
        .eq("risk_level", "HIGH")
        .order("days_until_stockout", desc=False)
        .execute()
    )
    name_map = _build_component_name_map(supabase)
    return [_enrich(r, name_map) for r in response.data]

def get_risk_summary(supabase):
    data   = supabase.table("internal_risk_predictions").select("*").execute().data
    high   = [r for r in data if r["risk_level"] == "HIGH"]
    medium = [r for r in data if r["risk_level"] == "MEDIUM"]
    low    = [r for r in data if r["risk_level"] == "LOW"]

    total_exposure = sum(
        float(r["total_risk_cost"] or 0)
        for r in data
        if r["risk_level"] in ["HIGH", "MEDIUM"]
    )

    return {
        "total_components":  len(data),
        "high_risk_count":   len(high),
        "medium_risk_count": len(medium),
        "low_risk_count":    len(low),
        "total_exposure":    round(total_exposure, 2),
        "last_predicted_at": data[0]["predicted_at"] if data else None
    }