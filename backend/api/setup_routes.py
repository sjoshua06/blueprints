from fastapi import APIRouter, UploadFile, HTTPException, Depends
from sqlalchemy import text
import pandas as pd
from typing import List
from db.database import engine
from utils.excel_parser import read_excel
from services.setup_pipeline import run_setup_pipeline
from io import BytesIO
from schemas.project_schema import ProjectCreate, ProjectResponse
router = APIRouter(prefix="/setup")


from auth.dependencies import get_current_user_id

# ================================
# Upload Components
# ================================
@router.post("/components")
async def upload_components(file: UploadFile, user_id: str = Depends(get_current_user_id)):

    try:
        contents = await file.read()              # read uploaded file
        df = pd.read_excel(BytesIO(contents))     # load into pandas
        
        df["user_id"] = user_id                   # inject user_id from JWT

        with engine.begin() as conn:
            df.to_sql(
                "components",
                conn,
                if_exists="append",
                index=False
            )

        return {"message": "components uploaded"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================================
# Upload Component Specifications
# ================================
@router.post("/component-specs")
async def upload_component_specs(file: UploadFile, user_id: str = Depends(get_current_user_id)):

    try:
        contents = await file.read()              # read uploaded file
        df = pd.read_excel(BytesIO(contents))     # load into pandas
        
        df["user_id"] = user_id                   # inject user_id from JWT

        with engine.begin() as conn:
            df.to_sql(
                "component_specifications",
                conn,
                if_exists="append",
                index=False
            )

        return {"message": "component specs uploaded"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================================
# Upload Suppliers
# ================================


@router.post("/suppliers")
async def upload_suppliers(file: UploadFile, user_id: str = Depends(get_current_user_id)):

    try:
        contents = await file.read()              # read uploaded file
        df = pd.read_excel(BytesIO(contents))     # load into pandas
        
        df["user_id"] = user_id                   # inject user_id from JWT

        with engine.begin() as conn:
            df.to_sql(
                "suppliers",
                conn,
                if_exists="append",
                index=False
            )

        return {"message": "suppliers uploaded"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# Upload Supplier Components
# ================================
@router.post("/supplier-components")
async def upload_supplier_components(file: UploadFile, user_id: str = Depends(get_current_user_id)):

    try:
        contents = await file.read()              # read uploaded file
        df = pd.read_excel(BytesIO(contents))     # load into pandas
        
        df["user_id"] = user_id                   # inject user_id from JWT

        with engine.begin() as conn:
            df.to_sql(
                "supplier_components",
                conn,
                if_exists="append",
                index=False
            )

        return {"message": "supplier components uploaded"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================================
# Upload Inventory
# ================================
@router.post("/inventory")
async def upload_inventory(file: UploadFile, user_id: str = Depends(get_current_user_id)):

    try:
        contents = await file.read()              # read uploaded file
        df = pd.read_excel(BytesIO(contents))     # load into pandas
        
        df["user_id"] = user_id                   # inject user_id from JWT

        with engine.begin() as conn:
            df.to_sql(
                "inventory",
                conn,
                if_exists="append",
                index=False
            )

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
            df.to_sql("projects", conn, if_exists="append", index=False)

        return {"message": "projects uploaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================================
# Upload All Sheets (Master Excel)
# ================================
@router.post("/upload-all")
async def upload_all(file: UploadFile, user_id: str = Depends(get_current_user_id)):
    """
    Parse a single master Excel file with multiple sheets: 
    inventory, projects, components, component_specifications, suppliers, supplier_components.
    Injects user_id into each and writes to DB.
    """
    try:
        contents = await file.read()
        # sheet_name=None reads all sheets into a dict of DataFrames
        excel_data = pd.read_excel(BytesIO(contents), sheet_name=None)
        
        expected_tables = {
            "inventory", 
            "projects", 
            "components", 
            "component_specifications", 
            "suppliers", 
            "supplier_components"
        }
        
        processed_sheets = []

        with engine.begin() as conn:
            for sheet_name, df in excel_data.items():
                norm_sheet_name = str(sheet_name).strip().lower()
                
                # If sheet name matches one of our expected tables, process it
                if norm_sheet_name in expected_tables:
                    df["user_id"] = user_id
                    
                    df.to_sql(
                        norm_sheet_name,
                        conn,
                        if_exists="append",
                        index=False
                    )
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


