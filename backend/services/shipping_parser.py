import pandas as pd
from io import BytesIO

async def parse_shipments(file):

    contents = await file.read()

    if file.filename.endswith(".csv"):
        df = pd.read_csv(BytesIO(contents))
    else:
        df = pd.read_excel(BytesIO(contents))

    df.columns = df.columns.astype(str).str.strip().str.lower().str.replace(" ", "_", regex=False)

    return df
