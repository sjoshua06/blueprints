import pandas as pd
from io import BytesIO

async def parse_bom(file):

    contents = await file.read()   # ✅ read file as bytes

    df = pd.read_excel(BytesIO(contents))   # ✅ FIX

    # normalize column names (VERY IMPORTANT)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    
    return df
