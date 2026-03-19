import pandas as pd

def read_excel(file):

    df = pd.read_excel(file.file)

    df.columns = df.columns.str.lower()

    return df