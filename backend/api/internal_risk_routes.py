from fastapi import APIRouter, HTTPException, Depends
from db.supabase_client import supabase
from services.internal_risk_service import (
    get_all_predictions,
    get_prediction_by_component,
    get_high_risk_components,
    get_risk_summary
)
from services.prophet_forecast_service import run_prophet_pipeline, get_prophet_plot_data
from auth.dependencies import get_current_user_id

router = APIRouter(prefix="/api/risk", tags=["Internal Risk"])


@router.get("/predictions")
async def all_predictions(user_id: str = Depends(get_current_user_id)):
    try:
        data = get_all_predictions(supabase, user_id)
        return {"status": "success", "count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictions/{component_id}")
async def component_prediction(component_id: int, user_id: str = Depends(get_current_user_id)):
    try:
        data = get_prediction_by_component(supabase, component_id, user_id)
        if not data:
            raise HTTPException(status_code=404, detail=f"No prediction for component {component_id}")
        return {"status": "success", "data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/high-risk")
async def high_risk(user_id: str = Depends(get_current_user_id)):
    try:
        data = get_high_risk_components(supabase, user_id)
        return {"status": "success", "count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def risk_summary(user_id: str = Depends(get_current_user_id)):
    try:
        summary = get_risk_summary(supabase, user_id)
        return {"status": "success", "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-prophet")
async def trigger_prophet_pipeline(user_id: str = Depends(get_current_user_id)):
    try:
        result = run_prophet_pipeline(user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecast/{component_id}")
async def get_forecast_chart(component_id: int, user_id: str = Depends(get_current_user_id)):
    try:
        result = get_prophet_plot_data(component_id, user_id)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
