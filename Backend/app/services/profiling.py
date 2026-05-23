import pandas as pd


def _null_pct(null_count: int, row_count: int) -> float:
    if row_count <= 0:
        return 0.0
    return round(null_count / row_count, 6)


def profile_dataset(file):
    df = pd.read_csv(file, sep=None, engine="python")
    row_count = len(df)

    result = {
        "row_count": row_count,
        "columns": [],
    }

    for col in df.columns:
        series = df[col]
        null_count = int(series.isna().sum())

        col_data = {
            "column_name": col,
            "data_type": str(series.dtype),
            "null_count": null_count,
            "null_pct": _null_pct(null_count, row_count),
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
