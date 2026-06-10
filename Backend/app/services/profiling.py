import io
import math
from typing import Optional

import pandas as pd

# Encodings we attempt (in order) when reading delimited text files.
# Latin-1 / cp1252 cover the vast majority of non-UTF-8 spreadsheet exports.
_TEXT_ENCODINGS = ("utf-8-sig", "utf-8", "latin-1", "cp1252")

_EXCEL_EXTENSIONS = (".xlsx", ".xls", ".xlsm", ".xlsb")


class UnsupportedFileError(Exception):
    """Raised when an uploaded file cannot be parsed into a dataset."""


def _clean_number(value) -> Optional[float]:
    """Convert a numpy/pandas number to a JSON-safe float (NaN/inf -> None)."""
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _null_pct(null_count: int, row_count: int) -> float:
    if row_count <= 0:
        return 0.0
    return round(null_count / row_count, 6)


def _read_excel(raw: bytes) -> pd.DataFrame:
    return pd.read_excel(io.BytesIO(raw))


def _read_csv(raw: bytes) -> pd.DataFrame:
    last_error: Optional[Exception] = None
    for encoding in _TEXT_ENCODINGS:
        try:
            text = raw.decode(encoding)
        except (UnicodeDecodeError, LookupError) as exc:
            last_error = exc
            continue

        # Let pandas sniff the delimiter, but fall back to a comma if the
        # sniffer can't decide (e.g. single-column files).
        try:
            return pd.read_csv(io.StringIO(text), sep=None, engine="python")
        except Exception as exc:  # pragma: no cover - depends on file content
            last_error = exc
            try:
                return pd.read_csv(io.StringIO(text))
            except Exception as exc2:
                last_error = exc2
                continue

    raise UnsupportedFileError(
        "Could not parse the file as CSV. Make sure it is a valid CSV "
        f"(UTF-8 or Latin-1 encoded). Underlying error: {last_error}"
    )


def _load_dataframe(raw: bytes, filename: Optional[str]) -> pd.DataFrame:
    name = (filename or "").lower()

    if name.endswith(_EXCEL_EXTENSIONS):
        try:
            return _read_excel(raw)
        except Exception as exc:
            raise UnsupportedFileError(
                f"Could not read the Excel file '{filename}'. "
                f"Underlying error: {exc}"
            ) from exc

    # Default to CSV/text parsing for .csv, .txt, .tsv and unknown extensions.
    return _read_csv(raw)


def profile_dataset(file, filename: Optional[str] = None):
    """Profile an uploaded dataset.

    ``file`` may be a file-like object (e.g. ``UploadFile.file``) or raw bytes.
    ``filename`` is used to decide how to parse the file (CSV vs Excel).
    """
    if isinstance(file, (bytes, bytearray)):
        raw = bytes(file)
    else:
        raw = file.read()
        if isinstance(raw, str):
            raw = raw.encode("utf-8")

    if not raw or not raw.strip():
        raise UnsupportedFileError("The uploaded file is empty.")

    df = _load_dataframe(raw, filename)

    if df.shape[1] == 0:
        raise UnsupportedFileError("The file does not contain any columns.")

    row_count = int(len(df))

    result = {
        "row_count": row_count,
        "columns": [],
    }

    for col in df.columns:
        series = df[col]
        null_count = int(series.isna().sum())

        col_data = {
            "column_name": str(col),
            "data_type": str(series.dtype),
            "null_count": null_count,
            "null_pct": _null_pct(null_count, row_count),
        }

        if pd.api.types.is_numeric_dtype(series):
            col_data.update({
                "mean": _clean_number(series.mean()),
                "std": _clean_number(series.std()),
                "min": _clean_number(series.min()),
                "max": _clean_number(series.max()),
            })

        result["columns"].append(col_data)

    return result
