import pandas as pd

def profile_dataset(file):
    df = pd.read_csv(file, sep=None, engine="python")

    result = {
        "row_count": len(df),
        "columns": []
    }

    for col in df.columns:
        series = df[col]

        col_data = {
            "column_name": col,
            "data_type": str(series.dtype),
            "null_count": int(series.isna().sum())
        }

        if pd.api.types.is_numeric_dtype(series):
            col_data.update({
                "mean": float(series.mean()),
                "std": float(series.std()),
                "min": float(series.min()),
                "max": float(series.max()),
            })

        result["columns"].append(col_data)

    return result