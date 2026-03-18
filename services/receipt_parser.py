import pandas as pd
from io import BytesIO

async def parse_receipts(file):

    contents = await file.read()

    df = pd.read_excel(BytesIO(contents))

    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    return df