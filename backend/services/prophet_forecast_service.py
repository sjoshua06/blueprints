import pandas as pd
from datetime import datetime
from prophet import Prophet
import sys
import os

from db.supabase_client import supabase

def get_data(user_id: str):
    print(f"Fetching inventory and receipts for user {user_id}...")
    inventory_res = supabase.table("inventory").select("*").eq("user_id", user_id).execute()
    receipts_res = supabase.table("supplier_receipts").select("*").eq("user_id", user_id).execute()
    components_res = supabase.table("components").select("*").eq("user_id", user_id).execute()
    
    df_inventory = pd.DataFrame(inventory_res.data)
    df_receipts = pd.DataFrame(receipts_res.data)
    df_components = pd.DataFrame(components_res.data)
    
    return df_inventory, df_receipts, df_components

def forecast_component_stock(component_id, df_receipts, df_inventory_row, forecast_days=90):
    comp_receipts = df_receipts[df_receipts["component_id"] == component_id].copy()
    
    current_stock     = float(df_inventory_row.get("stock_quantity", 0))
    daily_consumption = float(df_inventory_row.get("daily_consumption", 2.5))
    reorder_val       = float(df_inventory_row.get("reorder_level", 0)) if pd.notna(df_inventory_row.get("reorder_level", 0)) else 0
    end_date          = pd.Timestamp.now().normalize()
    
    # === Prophet Time Series Forecasting ===
    if not comp_receipts.empty and len(comp_receipts) >= 5:
        comp_receipts["received_date"] = pd.to_datetime(comp_receipts["received_date"]).dt.normalize()
        comp_receipts = comp_receipts.sort_values("received_date")

        start_date = comp_receipts["received_date"].min()
        date_range = pd.date_range(start=start_date, end=end_date, freq="D")
        
        daily_receipts = comp_receipts.groupby("received_date")["quantity_received"].sum().reindex(date_range, fill_value=0)
        diffs = (daily_consumption - daily_receipts)
        diffs_to_add = diffs.iloc[:-1].iloc[::-1].cumsum().iloc[::-1].reindex(date_range, fill_value=0)
        stock_values = (current_stock + diffs_to_add).clip(lower=0)
        
        prophet_df = pd.DataFrame({"ds": date_range, "y": stock_values.values}).dropna()

        model = Prophet(
            daily_seasonality=False, 
            weekly_seasonality=True,
            yearly_seasonality=False, 
            changepoint_prior_scale=0.05,
            interval_width=0.80
        )
        model.fit(prophet_df)
        future   = model.make_future_dataframe(periods=forecast_days)
        forecast = model.predict(future)
        
        future_forecast = forecast[forecast["ds"] > end_date]
        stockout_rows   = future_forecast[future_forecast["yhat"] <= 0]
        reorder_rows    = future_forecast[future_forecast["yhat"] <= reorder_val]

        return {
            "component_id":            component_id,
            "forecast":                forecast,
            "predicted_stockout_date": stockout_rows["ds"].min() if not stockout_rows.empty else None,
            "predicted_reorder_date":  reorder_rows["ds"].min()  if not reorder_rows.empty  else None,
            "forecast_90d_min_stock":  round(future_forecast["yhat"].min(), 1) if not future_forecast.empty else 0,
            "confidence":              min(0.95, 0.5 + (len(comp_receipts) / 100))
        }

    # === Fallback Linear Deterministic Forecasting (for insufficient data) ===
    # Project straight line from current_stock downwards by daily_consumption
    start_date = end_date - pd.Timedelta(days=7) # simulate 7 days of past stability
    date_range = pd.date_range(start=start_date, end=end_date + pd.Timedelta(days=forecast_days), freq="D")
    
    preds = []
    for d in date_range:
        if d <= end_date:
            preds.append(current_stock)
        else:
            days_out = (d - end_date).days
            projected = current_stock - (daily_consumption * days_out)
            preds.append(projected)
            
    forecast = pd.DataFrame({
        "ds": date_range,
        "yhat": preds,
        "yhat_lower": [p * 0.9 for p in preds],
        "yhat_upper": [p * 1.1 for p in preds]
    })
    
    future_forecast = forecast[forecast["ds"] > end_date]
    stockout_rows   = future_forecast[future_forecast["yhat"] <= 0]
    reorder_rows    = future_forecast[future_forecast["yhat"] <= reorder_val]

    return {
        "component_id":            component_id,
        "forecast":                forecast,
        "predicted_stockout_date": stockout_rows["ds"].min() if not stockout_rows.empty else None,
        "predicted_reorder_date":  reorder_rows["ds"].min()  if not reorder_rows.empty  else None,
        "forecast_90d_min_stock":  round(future_forecast["yhat"].min(), 1) if not future_forecast.empty else 0,
        "confidence":              0.2  # low confidence due to fallback
    }

from concurrent.futures import ProcessPoolExecutor, as_completed

def _forecast_worker(args):
    """Worker function for parallel forecasting"""
    cid, df_receipts, inv_row = args
    try:
        return forecast_component_stock(cid, df_receipts, inv_row)
    except Exception as e:
        print(f"Error forecasting for component {cid}: {e}")
        return None

def _build_default_inventory_row(component_row):
    """Build a default inventory-like Series for components not in inventory table."""
    return pd.Series({
        "component_id": component_row["component_id"],
        "stock_quantity": 0,
        "daily_consumption": 2.5,
        "reorder_level": 0,
    })

def run_prophet_pipeline(user_id: str):
    df_inventory, df_receipts, df_components = get_data(user_id)
    if df_receipts.empty:
        return {"status": "error", "message": "No receipts data found."}
    if df_components.empty:
        return {"status": "error", "message": "No components found for this user."}

    # Use ALL component IDs from the components table
    all_component_ids = df_components["component_id"].unique().tolist()
    
    # Prepare tasks — use inventory if available, otherwise use defaults
    tasks = []
    for cid in all_component_ids:
        if not df_inventory.empty:
            inv_rows = df_inventory[df_inventory["component_id"] == cid]
        else:
            inv_rows = pd.DataFrame()
        
        if not inv_rows.empty:
            tasks.append((cid, df_receipts, inv_rows.iloc[0]))
        else:
            # Component has receipts but no inventory entry — use defaults
            comp_rows = df_components[df_components["component_id"] == cid]
            if not comp_rows.empty:
                default_row = _build_default_inventory_row(comp_rows.iloc[0])
                tasks.append((cid, df_receipts, default_row))

    forecast_results = []
    
    # Run in parallel (Prophet is CPU intensive)
    max_workers = min(os.cpu_count() or 4, max(len(tasks), 1))
    if tasks:
        print(f"🚀 Starting parallel forecasting for {len(tasks)} components with {max_workers} workers...")
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Note: We pass the entire df_receipts which might be large. 
            # In a production system, we'd only pass relevant slices.
            results = list(executor.map(_forecast_worker, tasks))
            forecast_results = [r for r in results if r is not None]

    updates = []
    now_str = datetime.now().isoformat()
    
    # Track which components got a prophet forecast so we don't duplicate
    forecasted_cids = set()

    for res in forecast_results:
        cid = res["component_id"]
        so_date = res["predicted_stockout_date"]
        ro_date = res["predicted_reorder_date"]
        
        days_until = -1
        if so_date:
            days_until = (pd.to_datetime(so_date) - pd.Timestamp.now()).days
            
        risk_level = "LOW"
        if days_until != -1 and days_until < 14:
            risk_level = "HIGH"
        elif days_until != -1 and days_until < 30:
            risk_level = "MEDIUM"
            
        impact = "Critical" if risk_level == "HIGH" else ("High" if risk_level == "MEDIUM" else "Moderate")
        cost = 15000 if risk_level == "HIGH" else (5000 if risk_level == "MEDIUM" else 1000)
        
        # Confidence based on historical data points
        hist_count = len(df_receipts[df_receipts["component_id"] == cid])
        confidence = min(0.95, 0.5 + (hist_count / 100))
        
        updates.append({
            "component_id": int(cid),
            "user_id": user_id,
            "risk_level": risk_level,
            "confidence": confidence,
            "days_until_stockout": days_until if days_until != -1 else 999,
            "production_impact": impact,
            "prophet_stockout_date": so_date.strftime("%Y-%m-%d") if so_date else "Beyond 90 days",
            "prophet_reorder_date": ro_date.strftime("%Y-%m-%d") if ro_date else "Not needed",
            "total_risk_cost": cost,
            "predicted_at": now_str
        })
        
    if updates:
        # Delete old scoped predictions to bypass 409 unique constraint errors during upsert
        try:
            supabase.table("internal_risk_predictions").delete().eq("user_id", user_id).execute()
        except Exception:
            pass
        
        supabase.table("internal_risk_predictions").upsert(updates).execute()
        return {
            "status": "success",
            "forecasted": len(updates),
            "total_components": len(df_components)
        }
    else:
        return {"status": "success", "forecasted": 0, "message": "No new predictions added."}

def get_prophet_plot_data(component_id: int, user_id: str):
    df_inventory, df_receipts, df_components = get_data(user_id)
    if df_receipts.empty:
        return {"status": "error", "message": "No receipts data found."}

    # Try inventory first, fall back to defaults from components table
    inv_row = None
    if not df_inventory.empty:
        inv_rows = df_inventory[df_inventory["component_id"] == component_id]
        if not inv_rows.empty:
            inv_row = inv_rows.iloc[0]
    
    if inv_row is None:
        comp_rows = df_components[df_components["component_id"] == component_id]
        if comp_rows.empty:
            return {"status": "error", "message": "Component not found."}
        inv_row = _build_default_inventory_row(comp_rows.iloc[0])

    result = forecast_component_stock(component_id, df_receipts, inv_row)
    
    if not result:
        return {"status": "error", "message": "Not enough historic data (receipts < 5) to generate Prophet forecast."}
        
    forecast = result["forecast"]
    
    # We want to extract dates from today to 90 days out, plus some history if available.
    # Let's extract the recent 30 days of history and 90 days of future.
    start_date = pd.Timestamp.now() - pd.Timedelta(days=30)
    filtered = forecast[forecast["ds"] >= start_date]
    
    timeseries = []
    for _, row in filtered.iterrows():
        timeseries.append({
            "date": row["ds"].strftime("%Y-%m-%d"),
            "predicted_stock": round(max(0, row["yhat"]), 2),
            "lower_bound": round(max(0, row["yhat_lower"]), 2),
            "upper_bound": round(max(0, row["yhat_upper"]), 2)
        })
        
    reorder_val = inv_row.get("reorder_level", 0)
    reorder_val = float(reorder_val) if pd.notna(reorder_val) else 0.0
    return {
        "status": "success",
        "component_id": component_id,
        "reorder_level": reorder_val,
        "timeseries": timeseries
    }

if __name__ == "__main__":
    print(run_prophet_pipeline("test_user"))
