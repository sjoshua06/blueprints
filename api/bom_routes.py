from fastapi import APIRouter, UploadFile
from services.bom_parser import parse_bom
from services.receipt_parser import parse_receipts
from services.bom_analysis import analyze_bom

router = APIRouter(prefix="/analysis")


@router.post("/bom")

async def analyze_bom_file(
    bom_file: UploadFile,
    receipt_file: UploadFile
):

    bom_df = parse_bom(bom_file)

    receipts_df = parse_receipts(receipt_file)

    result = analyze_bom(bom_df, receipts_df)

    return result