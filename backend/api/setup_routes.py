from fastapi import APIRouter, UploadFile, HTTPException, Depends
from sqlalchemy import text
import pandas as pd
from typing import List
from db.database import engine
from utils.excel_parser import read_excel
from services.setup_pipeline import run_setup_pipeline
from io import BytesIO
from schemas.project_schema import ProjectCreate, ProjectResponse
router = APIRouter(prefix="/api/setup")


from auth.dependencies import get_current_user_id
import numpy as np
import uuid

def generic_upsert(table_name: str, df: pd.DataFrame, conn, conflict_columns: list[str]):
    """Batched UPSERT for better performance using a staging table."""
    if df.empty:
        return

    # 1. Choose a unique staging table name
    u_suffix = uuid.uuid4().hex
    staging_table = f"staging_{table_name}_{u_suffix[:8]}"

    # 2. Get columns (exclude computed ones)
    columns = [str(c) for c in df.columns if c not in ['created_at', 'last_updated']]
    df_staging = df[columns].copy()

    # 3. Create staging table structure from target
    # Handle the fact that df[columns] might contain NaNs that to_sql handles
    df_staging.to_sql(staging_table, conn, if_exists="replace", index=False)

    # 4. Perform the bulk UPSERT from staging to real table
    col_names = ", ".join(columns)
    # Special handling for UUID columns which often need casting from TEXT staging
    select_cols = ", ".join([f"{c}::uuid" if c == "user_id" or c == "uploaded_by" else c for c in columns])
    conflict_cols_str = ", ".join(conflict_columns)
    excluded_set = ", ".join([f"{c} = EXCLUDED.{c}" for c in columns if c not in conflict_columns])

    upsert_query = text(f"""
        INSERT INTO {table_name} ({col_names})
        SELECT {select_cols} FROM {staging_table}
        ON CONFLICT ({conflict_cols_str}) DO UPDATE SET
        {excluded_set}
    """)

    conn.execute(upsert_query)

    # 5. Clean up
    conn.execute(text(f"DROP TABLE {staging_table}"))

# ================================
# Upload Components
# ================================
@router.post("/components")
async def upload_components(file: UploadFile, user_id: str = Depends(get_current_user_id)):
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        df["user_id"] = user_id
        
        with engine.begin() as conn:
            generic_upsert("components", df, conn, ["user_id", "component_id"])

        return {"message": "components uploaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# Upload Component Specifications
# ================================
@router.post("/component-specs")
async def upload_component_specs(file: UploadFile, user_id: str = Depends(get_current_user_id)):
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        df["user_id"] = user_id
        
        with engine.begin() as conn:
            # spec_id is usually auto-generated if not in Excel. 
            # If not in Excel, we use to_sql append. If in Excel, we upsert.
            if "spec_id" in df.columns:
                generic_upsert("component_specifications", df, conn, ["user_id", "spec_id"])
            else:
                df.to_sql("component_specifications", conn, if_exists="append", index=False)

        return {"message": "component specs uploaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# Upload Suppliers
# ================================
@router.post("/suppliers")
async def upload_suppliers(file: UploadFile, user_id: str = Depends(get_current_user_id)):
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        df["user_id"] = user_id
        
        with engine.begin() as conn:
            generic_upsert("suppliers", df, conn, ["user_id", "supplier_id"])

        return {"message": "suppliers uploaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# Upload Supplier Components
# ================================
@router.post("/supplier-components")
async def upload_supplier_components(file: UploadFile, user_id: str = Depends(get_current_user_id)):
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        df["user_id"] = user_id
        
        with engine.begin() as conn:
            if "supplier_component_id" in df.columns:
                generic_upsert("supplier_components", df, conn, ["user_id", "supplier_component_id"])
            else:
                df.to_sql("supplier_components", conn, if_exists="append", index=False)

        return {"message": "supplier components uploaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# Upload Inventory
# ================================
@router.post("/inventory")
async def upload_inventory(file: UploadFile, user_id: str = Depends(get_current_user_id)):
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        df["user_id"] = user_id
        
        with engine.begin() as conn:
            if "inventory_id" in df.columns:
                generic_upsert("inventory", df, conn, ["user_id", "inventory_id"])
            else:
                df.to_sql("inventory", conn, if_exists="append", index=False)

        return {"message": "inventory uploaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# Upload Projects
# ================================
@router.post("/projects")
async def upload_projects(file: UploadFile, user_id: str = Depends(get_current_user_id)):
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        df["user_id"] = user_id

        with engine.begin() as conn:
            generic_upsert("projects", df, conn, ["user_id", "project_id"])

        return {"message": "projects uploaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# Upload All Sheets (Master Excel)
# ================================
@router.post("/upload-all")
async def upload_all(file: UploadFile, user_id: str = Depends(get_current_user_id)):
    try:
        contents = await file.read()
        excel_data = pd.read_excel(BytesIO(contents), sheet_name=None)
        
        # Table -> PK mapping
        table_pks = {
            "inventory": "inventory_id", 
            "projects": "project_id", 
            "components": "component_id", 
            "component_specifications": "spec_id", 
            "suppliers": "supplier_id", 
            "supplier_components": "supplier_component_id"
        }
        
        processed_sheets = []
        with engine.begin() as conn:
            for sheet_name, df in excel_data.items():
                norm_sheet_name = str(sheet_name).strip().lower()
                
                if norm_sheet_name in table_pks:
                    df["user_id"] = user_id
                    pk = table_pks[norm_sheet_name]
                    
                    if pk in df.columns:
                        generic_upsert(norm_sheet_name, df, conn, ["user_id", pk])
                    else:
                        df.to_sql(norm_sheet_name, conn, if_exists="append", index=False)
                    processed_sheets.append(norm_sheet_name)

        return {
            "message": "Master Excel uploaded successfully", 
            "processed_sheets": processed_sheets
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================================
# Build FAISS Indexes
# ================================
@router.post("/build-indexes")
def build_indexes(user_id: str = Depends(get_current_user_id)):

    try:
        result = run_setup_pipeline(user_id)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================================
# Setup Status
# ================================
@router.get("/status")
def setup_status():

    try:
        query = text("SELECT COUNT(*) FROM components")

        with engine.connect() as conn:
            result = conn.execute(query)
            count = result.scalar()

        return {
            "components_loaded": count > 0,
            "component_count": count
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# projects 
# # ================================
@router.post("/project", response_model=dict)
def create_project(project: ProjectCreate):

    query = text("""
        INSERT INTO projects
        (user_id, project_name, project_description, industry_type)
        VALUES
        (:user_id, :project_name, :project_description, :industry_type)
        RETURNING project_id
    """)

    try:

        with engine.begin() as conn:

            result = conn.execute(query, project.model_dump())

            project_id = result.scalar()

        return {
            "message": "project created",
            "project_id": project_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


