from app.db import models
from app.services import thresholds as t


def _fmt_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _load_previous_columns(db, previous_run_id):
    profiles = (
        db.query(models.ColumnProfile)
        .filter(models.ColumnProfile.dataset_run_id == previous_run_id)
        .all()
    )
    return {p.column_name: p for p in profiles}


def _profile_columns_map(profile):
    return {c["column_name"]: c for c in profile["columns"]}


def detect_anomalies(db, dataset_id, current_run, current_profile):
    alerts = []

    previous_run = (
        db.query(models.DatasetRun)
        .filter(models.DatasetRun.dataset_id == dataset_id)
        .order_by(models.DatasetRun.created_at.desc())
        .first()
    )

    if not previous_run:
        return alerts

    prev_cols = _load_previous_columns(db, previous_run.id)
    curr_cols = _profile_columns_map(current_profile)

    if current_run.row_count < previous_run.row_count * t.ROW_COUNT_WARNING_RATIO:
        severity = (
            "high"
            if current_run.row_count < previous_run.row_count * t.ROW_COUNT_CRITICAL_RATIO
            else "medium"
        )
        alerts.append({
            "message": "Row count dropped significantly compared to previous run",
            "severity": severity,
            "metric": "row_count",
            "previous_value": str(previous_run.row_count),
            "current_value": str(current_run.row_count),
        })

    for name, curr in curr_cols.items():
        if name not in prev_cols:
            alerts.append({
                "message": f"New column detected: '{name}'",
                "severity": "medium",
                "column_name": name,
                "metric": "schema",
                "previous_value": None,
                "current_value": curr.get("data_type"),
            })
            continue

        prev = prev_cols[name]
        prev_null_pct = prev.null_pct if prev.null_pct is not None else 0.0
        curr_null_pct = curr.get("null_pct", 0.0)
        null_increase = curr_null_pct - prev_null_pct

        if null_increase >= t.NULL_RATE_MIN_DELTA:
            if prev_null_pct > 0:
                relative = null_increase / prev_null_pct
            else:
                relative = float("inf") if curr_null_pct > 0 else 0.0

            if relative >= t.NULL_RATE_CRITICAL_INCREASE or (
                prev_null_pct == 0 and curr_null_pct >= t.NULL_RATE_MIN_DELTA
            ):
                severity = "high"
            elif relative >= t.NULL_RATE_WARNING_INCREASE:
                severity = "medium"
            else:
                severity = None

            if severity:
                alerts.append({
                    "message": (
                        f"Null rate increased for column '{name}' "
                        f"({_fmt_pct(prev_null_pct)} → {_fmt_pct(curr_null_pct)})"
                    ),
                    "severity": severity,
                    "column_name": name,
                    "metric": "null_rate",
                    "previous_value": _fmt_pct(prev_null_pct),
                    "current_value": _fmt_pct(curr_null_pct),
                })

        if prev.data_type != curr.get("data_type"):
            alerts.append({
                "message": f"Data type changed for column '{name}'",
                "severity": "high",
                "column_name": name,
                "metric": "schema",
                "previous_value": prev.data_type,
                "current_value": curr.get("data_type"),
            })

        curr_mean = curr.get("mean")
        if curr_mean is not None and prev.mean is not None and prev.std is not None:
            std = max(prev.std, t.MEAN_MIN_STD)
            shift = abs(curr_mean - prev.mean)
            if shift > t.MEAN_SHIFT_STD_MULTIPLIER * std:
                alerts.append({
                    "message": (
                        f"Mean shifted significantly for column '{name}' "
                        f"({prev.mean:.4g} → {curr_mean:.4g})"
                    ),
                    "severity": "medium",
                    "column_name": name,
                    "metric": "mean",
                    "previous_value": f"{prev.mean:.6g}",
                    "current_value": f"{curr_mean:.6g}",
                })

    for name, prev in prev_cols.items():
        if name not in curr_cols:
            alerts.append({
                "message": f"Column removed: '{name}'",
                "severity": "high",
                "column_name": name,
                "metric": "schema",
                "previous_value": prev.data_type,
                "current_value": None,
            })

    return alerts
