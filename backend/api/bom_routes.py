from fastapi import APIRouter, UploadFile, HTTPException, Depends
from sqlalchemy import text
from db.database import engine
from auth.dependencies import get_current_user_id
from services.bom_parser import parse_bom
from services.receipt_parser import parse_receipts
from services.bom_analysis import analyze_bom
import pandas as pd
from datetime import datetime

router = APIRouter(prefix="/api/analysis")


# ─── Column cleaning ──────────────────────────────────────────────────────────
def clean_columns(df):
    df.columns = df.columns.astype(str).str.strip().str.lower().str.replace(" ", "_", regex=False)
    return df


# ─── Type safety helpers ──────────────────────────────────────────────────────
def _safe_int(row, col):
    try:
        val = row[col] if col in row.index else None
        return int(val) if pd.notna(val) else None
    except Exception:
        return None

def _safe_str(row, col):
    try:
        val = row[col] if col in row.index else None
        return str(val).strip() if pd.notna(val) else None
    except Exception:
        return None

def _safe_bool(row, col):
    try:
        val = row[col] if col in row.index else None
        if pd.isna(val):
            return None
        if isinstance(val, bool):
            return val
        return str(val).strip().lower() in ("true", "1", "yes")
    except Exception:
        return None

def _safe_datetime(row, col):
    try:
        val = row[col] if col in row.index else None
        if pd.isna(val):
            return None
        return pd.to_datetime(val).to_pydatetime()
    except Exception:
        return None


# ─── Fetch valid IDs from DB to avoid FK violations ──────────────────────────
def _get_valid_ids(table: str, id_col: str) -> set:
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(f"SELECT {id_col} FROM {table}")).fetchall()
        return {int(r[0]) for r in rows}
    except Exception:
        return set()


# ─── Generate next upload_id (MAX + 1) ───────────────────────────────────────
def _next_upload_id(table: str) -> int:
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT COALESCE(MAX(upload_id), 0) FROM {table}")
            ).scalar()
        return int(result) + 1
    except Exception:
        return 1


# ─────────────────────────────────────────────────────────────────────────────
# Save BOM rows → bom table
# s.no  : row number starting from 1 for every upload (1,2,3...N)
# upload_id : same for all rows in this file
# ─────────────────────────────────────────────────────────────────────────────
def save_bom_to_db(df: pd.DataFrame, user_id: str) -> tuple[int, int]:
    required = {"component_id", "quantity_required", "project_id"}
    missing  = required - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"BOM file missing required columns: {missing}. "
                   f"Found: {list(df.columns)}"
        )

    valid_project_ids   = _get_valid_ids("projects",   "project_id")
    valid_component_ids = _get_valid_ids("components", "component_id")

    upload_id = _next_upload_id("bom")
    print(f"📋 BOM upload_id={upload_id}  ({len(df)} rows)  s.no will be 1→{len(df)}")

    insert_sql = text("""
        INSERT INTO bom (
            "s.no",
            project_id,
            component_id,
            upload_id,
            quantity_required,
            unit_of_measure,
            reference_designator,
            is_critical,
            notes,
            component_name,
            user_id
        ) VALUES (
            :sno,
            :project_id,
            :component_id,
            :upload_id,
            :quantity_required,
            :unit_of_measure,
            :reference_designator,
            :is_critical,
            :notes,
            :component_name,
            :user_id
        )
        ON CONFLICT (user_id, project_id, component_id) DO UPDATE SET
            "s.no" = EXCLUDED."s.no",
            upload_id = EXCLUDED.upload_id,
            quantity_required = EXCLUDED.quantity_required,
            unit_of_measure = EXCLUDED.unit_of_measure,
            reference_designator = EXCLUDED.reference_designator,
            is_critical = EXCLUDED.is_critical,
            notes = EXCLUDED.notes,
            component_name = EXCLUDED.component_name
    """)

    data_to_insert = []
    sno = 1
    
    for _, row in df.iterrows():
        raw_project_id = _safe_int(row, "project_id")
        if not raw_project_id:
            raise HTTPException(
                status_code=400, 
                detail=f"Row {sno} in BOM is missing a valid 'project_id' (cannot be empty)."
            )
        if raw_project_id not in valid_project_ids:
            raise HTTPException(
                status_code=400, 
                detail=f"Row {sno} in BOM has project_id={raw_project_id}, but this ID does not exist in your registered Projects list!"
            )

        raw_component_id = _safe_int(row, "component_id")
        if not raw_component_id or raw_component_id not in valid_component_ids:
            continue

        data_to_insert.append({
            "sno"                 : sno,
            "project_id"          : raw_project_id,
            "component_id"        : raw_component_id,
            "upload_id"           : upload_id,
            "quantity_required"   : int(row["quantity_required"]),
            "unit_of_measure"     : _safe_str(row, "unit_of_measure"),
            "reference_designator": _safe_str(row, "reference_designator"),
            "is_critical"         : _safe_bool(row, "is_critical"),
            "notes"               : _safe_str(row, "notes"),
            "component_name"      : _safe_str(row, "component_name"),
            "user_id"             : user_id,
        })
        sno += 1

    if data_to_insert:
        with engine.begin() as conn:
            conn.execute(insert_sql, data_to_insert)

    return upload_id, len(data_to_insert)


# ─────────────────────────────────────────────────────────────────────────────
# Save receipt rows → supplier_receipts table
# s.no  : row number starting from 1 for every upload (1,2,3...N)
# upload_id : same for all rows in this file
# ─────────────────────────────────────────────────────────────────────────────
def save_receipts_to_db(df: pd.DataFrame, user_id: str) -> tuple[int, int]:
    required = {"component_name"}
    missing  = required - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Receipt file missing required columns: {missing}. "
                   f"Found: {list(df.columns)}"
        )

    valid_component_ids = _get_valid_ids("components", "component_id")
    valid_supplier_ids  = _get_valid_ids("suppliers",  "supplier_id")
    valid_project_ids   = _get_valid_ids("projects",   "project_id")

    upload_id = _next_upload_id("supplier_receipts")
    print(f"🧾 Receipt upload_id={upload_id}  ({len(df)} rows)  s.no will be 1→{len(df)}")

    insert_sql = text("""
        INSERT INTO supplier_receipts (
            "s.no",
            supplier_id,
            component_id,
            quantity_received,
            received_date,
            project_id,
            component_name,
            upload_id,
            user_id
        ) VALUES (
            :sno,
            :supplier_id,
            :component_id,
            :quantity_received,
            :received_date,
            :project_id,
            :component_name,
            :upload_id,
            :user_id
        )
    """)

    data_to_insert = []
    sno = 1

    for _, row in df.iterrows():
        raw_project_id = _safe_int(row, "project_id")
        if not raw_project_id:
            raise HTTPException(
                status_code=400, 
                detail=f"Row {sno} in Receipts is missing a valid 'project_id' (cannot be empty)."
            )
        if raw_project_id not in valid_project_ids:
            raise HTTPException(
                status_code=400, 
                detail=f"Row {sno} in Receipts has project_id={raw_project_id}, but this ID does not exist in your registered Projects."
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
            "received_date"    : _safe_datetime(row, "received_date"),
            "project_id"       : raw_project_id,
            "component_name"   : str(row["component_name"]),
            "upload_id"        : upload_id,
            "user_id"          : user_id,
        })
        sno += 1

    if data_to_insert:
        with engine.begin() as conn:
            conn.execute(insert_sql, data_to_insert)

    return upload_id, len(data_to_insert)


# ─── Endpoint ─────────────────────────────────────────────────────────────────
@router.post("/bom")
async def analyze_bom_file(
    bom_file    : UploadFile,
    receipt_file: UploadFile,
    user_id     : str = Depends(get_current_user_id),
):
    # 📥 Parse files
    bom_df      = await parse_bom(bom_file)
    receipts_df = await parse_receipts(receipt_file)

    # ✅ Clean column names
    bom_df      = clean_columns(bom_df)
    receipts_df = clean_columns(receipts_df)

    print("BOM Columns     :", bom_df.columns.tolist())
    print("Receipts Columns:", receipts_df.columns.tolist())

    # 💾 Save BOM
    try:
        bom_upload_id, bom_saved = save_bom_to_db(bom_df, user_id)
        print(f"✅ BOM saved — upload_id={bom_upload_id}, rows={bom_saved}")
    except HTTPException:
        raise
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to save BOM to DB: {str(e)}")

    # 💾 Save Receipts
    try:
        receipt_upload_id, receipt_saved = save_receipts_to_db(receipts_df, user_id)
        print(f"✅ Receipts saved — upload_id={receipt_upload_id}, rows={receipt_saved}")
    except HTTPException:
        raise
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to save receipts to DB: {str(e)}")

    # 🧠 Analyze
    result = analyze_bom(bom_df, receipts_df, user_id)

    return {
        "saved": {
            "bom_upload_id"     : bom_upload_id,
            "bom_rows_saved"    : bom_saved,
            "receipt_upload_id" : receipt_upload_id,
            "receipt_rows_saved": receipt_saved,
        },
        "analysis": result
    }