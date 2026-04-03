from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import text
from db.database import engine
from auth.dependencies import get_current_user_id
from services.shipping_risk_service import calculate_shipping_delay
from services.shipping_parser import parse_shipments
from api.bom_routes import clean_columns, _get_valid_ids, _next_upload_id, _safe_int, _safe_str, _safe_datetime
import pandas as pd

router = APIRouter(prefix="/api/shipping", tags=["Shipping"])

@router.get("/dashboard")
async def get_shipping_dashboard(user_id: str = Depends(get_current_user_id)):
    """Fetch shipments with supplier origin info and calculate per-route transportation delays"""
    
    # 1. Get destination port for this user
    port_query = text("SELECT destination_port FROM profiles WHERE user_id = :user_id")
    with engine.connect() as conn:
        res = conn.execute(port_query, {"user_id": user_id}).fetchone()
        destination_port = res[0] if res and res[0] else "Unknown"

    # 2. Get shipments JOIN with suppliers to get origin country per shipment
    shipments_query = text("""
        SELECT 
            s.*,
            sup.supplier_name,
            sup.country AS supplier_country
        FROM shipments s
        LEFT JOIN suppliers sup ON s.supplier_id = sup.supplier_id
        WHERE s.user_id = :user_id
        ORDER BY s.estimated_date ASC
    """)
    with engine.connect() as conn:
        result = conn.execute(shipments_query, {"user_id": user_id})
        shipments = [dict(row._mapping) for row in result.fetchall()]
        
    # 3. Calculate per-shipment delays using origin + destination risk analysis
    analyzed_shipments = await calculate_shipping_delay(shipments, destination_port)
    
    return {
        "destination_port": destination_port,
        "total_shipments": len(shipments),
        "shipments": analyzed_shipments
    }


# ─────────────────────────────────────────────────────────────────────────────
# Save shipment rows → shipments table
# s.no  : row number starting from 1 for every upload (1,2,3...N)
# upload_id : same for all rows in this file
# ─────────────────────────────────────────────────────────────────────────────
def save_shipments_to_db(df: pd.DataFrame, user_id: str) -> tuple[int, int]:
    required = {"component_name"}
    missing  = required - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Shipments file missing required columns: {missing}. "
                   f"Found: {list(df.columns)}"
        )

    valid_component_ids = _get_valid_ids("components", "component_id")
    valid_supplier_ids  = _get_valid_ids("suppliers",  "supplier_id")
    valid_project_ids   = _get_valid_ids("projects",   "project_id")

    upload_id = _next_upload_id("shipments")
    print(f"📦 Shipments upload_id={upload_id}  ({len(df)} rows)  s.no will be 1→{len(df)}")

    insert_sql = text("""
        INSERT INTO shipments (
            "s.no",
            supplier_id,
            component_id,
            quantity_received,
            estimated_date,
            project_id,
            component_name,
            upload_id,
            user_id,
            dispatched_date,
            mode,
            mode_details
        ) VALUES (
            :sno,
            :supplier_id,
            :component_id,
            :quantity_received,
            :estimated_date,
            :project_id,
            :component_name,
            :upload_id,
            :user_id,
            :dispatched_date,
            :mode,
            :mode_details
        )
    """)

    data_to_insert = []
    sno = 1

    for _, row in df.iterrows():
        raw_project_id = _safe_int(row, "project_id")
        if not raw_project_id:
            raise HTTPException(
                status_code=400, 
                detail=f"Row {sno} in Shipments is missing a valid 'project_id' (cannot be empty)."
            )
        if raw_project_id not in valid_project_ids:
            raise HTTPException(
                status_code=400, 
                detail=f"Row {sno} in Shipments has project_id={raw_project_id}, but this ID does not exist in your registered Projects."
            )

        raw_supplier_id = _safe_int(row, "supplier_id")
        if raw_supplier_id and raw_supplier_id not in valid_supplier_ids:
            raw_supplier_id = None

        raw_component_id = _safe_int(row, "component_id")
        if raw_component_id and raw_component_id not in valid_component_ids:
            raw_component_id = None

        data_to_insert.append({
            "sno"              : sno,
            "supplier_id"      : raw_supplier_id,
            "component_id"     : raw_component_id,
            "quantity_received": _safe_int(row, "quantity_received"),
            "estimated_date"   : _safe_datetime(row, "estimated_date"),
            "project_id"       : raw_project_id,
            "component_name"   : str(row["component_name"]),
            "upload_id"        : upload_id,
            "user_id"          : user_id,
            "dispatched_date"  : _safe_datetime(row, "dispatched_date"),
            "mode"             : _safe_str(row, "mode"),
            "mode_details"     : _safe_str(row, "mode_details"),
        })
        sno += 1

    if data_to_insert:
        with engine.begin() as conn:
            conn.execute(insert_sql, data_to_insert)

    return upload_id, len(data_to_insert)


@router.post("/upload")
async def upload_shipments(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id)
):
    """Uploads an Excel file of shipments and inserts into the shipments table"""
    if not file.filename.endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload Excel or CSV.")
        
    try:
        # 1. Parse File
        shipments_df = await parse_shipments(file)
        
        # 2. Clean Columns
        shipments_df = clean_columns(shipments_df)
        
        # 3. Save to DB
        upload_id, rows_saved = save_shipments_to_db(shipments_df, user_id)
        
        return {
            "upload_id": upload_id, 
            "rows_inserted": rows_saved,
            "message": f"Successfully processed {rows_saved} shipments."
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
