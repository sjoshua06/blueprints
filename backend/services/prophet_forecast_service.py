import pandas as pd
from datetime import datetime
from prophet import Prophet
import sys
import os

from db.supabase_client import supabase

def get_data():
    print("Fetching inventory and receipts...")
    inventory_res = supabase.table("inventory").select("*").execute()
    receipts_res = supabase.table("supplier_receipts").select("*").execute()
    
    df_inventory = pd.DataFrame(inventory_res.data)
    df_receipts = pd.DataFrame(receipts_res.data)
    
    return df_inventory, df_receipts

def forecast_component_stock(component_id, df_receipts, df_inventory_row, forecast_days=90):
    comp_receipts = df_receipts[df_receipts["component_id"] == component_id].copy()
    if comp_receipts.empty:
        return None
        
    comp_receipts["received_date"] = pd.to_datetime(comp_receipts["received_date"]).dt.normalize()
    comp_receipts = comp_receipts.sort_values("received_date")

    if len(comp_receipts) < 5:
        return None

    current_stock     = float(df_inventory_row["stock_quantity"])
    daily_consumption = float(df_inventory_row.get("daily_consumption", 2.5))

    # Vectorized historical stock calculation
    start_date = comp_receipts["received_date"].min()
    end_date = pd.Timestamp.now().normalize()
    date_range = pd.date_range(start=start_date, end=end_date, freq="D")
    
    # 1. Sum receipts by date
    daily_receipts = comp_receipts.groupby("received_date")["quantity_received"].sum().reindex(date_range, fill_value=0)
    
    # 2. Calculate stock backwards using vectorized cumsum
    # Stock[i] = Stock[i+1] + consumption - receipts[i]
    diffs = (daily_consumption - daily_receipts)
    
    # We want to sum diffs from i to N-1 (excluding index N/today)
    diffs_to_add = diffs.iloc[:-1].iloc[::-1].cumsum().iloc[::-1].reindex(date_range, fill_value=0)
    
    stock_values = (current_stock + diffs_to_add).clip(lower=0)
    
    prophet_df = pd.DataFrame({"ds": date_range, "y": stock_values.values}).dropna()

    # Faster Prophet configuration
    model = Prophet(
        daily_seasonality=False, 
        weekly_seasonality=True,
        yearly_seasonality=False, 
        changepoint_prior_scale=0.05,
        interval_width=0.80
    )
    model.fit(prophet_df)

    future          = model.make_future_dataframe(periods=forecast_days)
    forecast        = model.predict(future)
    
    # Extract results
    future_forecast = forecast[forecast["ds"] > end_date]
    stockout_rows   = future_forecast[future_forecast["yhat"] <= 0]
    
    reorder_val     = float(df_inventory_row.get("reorder_level", 0)) if not pd.isna(df_inventory_row.get("reorder_level")) else 0
    reorder_rows    = future_forecast[future_forecast["yhat"] <= reorder_val]

    return {
        "component_id":            component_id,
        "forecast":                forecast,
        "predicted_stockout_date": stockout_rows["ds"].min() if not stockout_rows.empty else None,
        "predicted_reorder_date":  reorder_rows["ds"].min()  if not reorder_rows.empty  else None,
        "forecast_90d_min_stock":  round(future_forecast["yhat"].min(), 1) if not future_forecast.empty else 0
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

def run_prophet_pipeline():
    df_inventory, df_receipts = get_data()
    if df_inventory.empty or df_receipts.empty:
        return {"status": "error", "message": "No inventory or receipts data found."}
        
    # Filter receipts count per component
    receipt_counts = df_receipts.groupby("component_id").size()
    eligible_cids = receipt_counts[receipt_counts >= 5].index.tolist()

    # Prepare tasks for parallel execution
    tasks = []
    for cid in eligible_cids:
        inv_rows = df_inventory[df_inventory["component_id"] == cid]
        if not inv_rows.empty:
            tasks.append((cid, df_receipts, inv_rows.iloc[0]))

    forecast_results = []
    
    # Run in parallel (Prophet is CPU intensive)
    max_workers = min(os.cpu_count() or 4, len(tasks))
    if tasks:
        print(f"🚀 Starting parallel forecasting for {len(tasks)} components with {max_workers} workers...")
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Note: We pass the entire df_receipts which might be large. 
            # In a production system, we'd only pass relevant slices.
            results = list(executor.map(_forecast_worker, tasks))
            forecast_results = [r for r in results if r is not None]

    updates = []
    now_str = datetime.now().isoformat()
    
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
        # Supabase upsert handles batching naturally
        supabase.table("internal_risk_predictions").upsert(updates).execute()
        return {"status": "success", "forecasted": len(updates), "eligible": len(eligible_cids)}
    else:
        return {"status": "success", "forecasted": 0, "eligible": len(eligible_cids), "message": "No new predictions added."}

def get_prophet_plot_data(component_id: int):
    df_inventory, df_receipts = get_data()
    if df_inventory.empty or df_receipts.empty:
        return {"status": "error", "message": "No inventory or receipts data found."}
        
    inv_rows = df_inventory[df_inventory["component_id"] == component_id]
    if inv_rows.empty:
        return {"status": "error", "message": "Component not found in inventory."}
        
    inv_row = inv_rows.iloc[0]
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
        
    reorder_val = inv_row["reorder_level"] if "reorder_level" in inv_row and not pd.isna(inv_row["reorder_level"]) else 0
    return {
        "status": "success",
        "component_id": component_id,
        "reorder_level": float(reorder_val),
        "timeseries": timeseries
    }

if __name__ == "__main__":
    print(run_prophet_pipeline())
