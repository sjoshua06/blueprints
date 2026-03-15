from fastapi import APIRouter, UploadFile, HTTPException
from sqlalchemy import text
import pandas as pd

from db.database import engine
from utils.excel_parser import read_excel
from services.setup_pipeline import run_setup_pipeline

router = APIRouter(prefix="/setup")


# ================================
# Upload Components
# ================================
@router.post("/components")
async def upload_components(file: UploadFile):

    try:
        df = read_excel(file)

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
async def upload_component_specs(file: UploadFile):

    try:
        df = read_excel(file)

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
async def upload_suppliers(file: UploadFile):

    try:
        df = read_excel(file)

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
async def upload_supplier_components(file: UploadFile):

    try:
        df = read_excel(file)

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
async def upload_inventory(file: UploadFile):

    try:
        df = read_excel(file)

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
# Build FAISS Indexes
# ================================
@router.post("/build-indexes")
def build_indexes():

    try:
        result = run_setup_pipeline()

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