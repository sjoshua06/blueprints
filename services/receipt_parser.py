import pandas as pd


def parse_receipts(file):

    df = pd.read_excel(file.file)

    df.columns = df.columns.str.lower()

    return df