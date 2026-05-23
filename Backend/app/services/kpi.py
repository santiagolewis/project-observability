from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.db import models
from app.services import thresholds as t


def _avg_null_pct(columns) -> Optional[float]:
    if not columns:
        return None
    values = [c.null_pct for c in columns if c.null_pct is not None]
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def get_ordered_runs(db: Session, dataset_id: str) -> list[models.DatasetRun]:
    return (
        db.query(models.DatasetRun)
        .filter(models.DatasetRun.dataset_id == dataset_id)
        .order_by(models.DatasetRun.created_at.desc())
        .all()
    )


def get_run_columns(db: Session, run_id) -> list[models.ColumnProfile]:
    return (
        db.query(models.ColumnProfile)
        .filter(models.ColumnProfile.dataset_run_id == run_id)
        .order_by(models.ColumnProfile.column_name)
        .all()
    )


def count_recent_alerts(
    db: Session,
    dataset_id: str,
    since: datetime,
    severity: Optional[str] = None,
) -> int:
    q = db.query(models.Alert).filter(
        models.Alert.dataset_id == dataset_id,
        models.Alert.created_at >= since,
    )
    if severity:
        q = q.filter(models.Alert.severity == severity)
    return q.count()


def compute_row_status(latest_row_count: int, avg_row_count: float) -> Optional[str]:
    if latest_row_count < avg_row_count * t.ROW_COUNT_CRITICAL_RATIO:
        return "critical"
    if latest_row_count < avg_row_count * t.ROW_COUNT_WARNING_RATIO:
        return "warning"
    return None


def resolve_dataset_status(
    db: Session,
    dataset_id: str,
    runs: Optional[list[models.DatasetRun]] = None,
) -> dict:
    runs = runs if runs is not None else get_ordered_runs(db, dataset_id)
    now = datetime.now(timezone.utc)
    last_24h = now - timedelta(hours=24)

    alerts_24h = count_recent_alerts(db, dataset_id, last_24h)
    high_alerts_24h = count_recent_alerts(db, dataset_id, last_24h, severity="high")

    if len(runs) < 2:
        return {
            "status": "learning",
            "message": "Not enough runs to establish a baseline (need at least 2)",
            "last_run_at": runs[0].created_at if runs else None,
            "alerts_last_24h": alerts_24h,
            "row_count": runs[0].row_count if runs else None,
            "row_count_vs_avg_pct": None,
            "high_severity_alerts_24h": high_alerts_24h,
        }

    last_run = runs[0]
    previous_runs = runs[1:]
    avg_row_count = sum(r.row_count for r in previous_runs) / len(previous_runs)
    row_vs_avg = (
        round((last_run.row_count / avg_row_count) * 100, 2)
        if avg_row_count
        else None
    )

    row_status = compute_row_status(last_run.row_count, avg_row_count)

    if high_alerts_24h > 0 or row_status == "critical":
        status = "critical"
    elif alerts_24h > 0 or row_status == "warning":
        status = "warning"
    else:
        status = "healthy"

    return {
        "status": status,
        "message": None,
        "last_run_at": last_run.created_at,
        "alerts_last_24h": alerts_24h,
        "row_count": last_run.row_count,
        "row_count_vs_avg_pct": row_vs_avg,
        "high_severity_alerts_24h": high_alerts_24h,
    }


def build_dataset_summary(db: Session, dataset_id: str) -> dict:
    runs = get_ordered_runs(db, dataset_id)
    status_data = resolve_dataset_status(db, dataset_id, runs=runs)

    latest = runs[0] if runs else None
    previous = runs[1] if len(runs) > 1 else None

    latest_cols = get_run_columns(db, latest.id) if latest else []
    previous_cols = get_run_columns(db, previous.id) if previous else []

    prev_by_name = {c.column_name: c for c in previous_cols}
    column_deltas = []
    null_increase_count = 0

    for col in latest_cols:
        delta = None
        prev = prev_by_name.get(col.column_name)
        if prev and col.null_pct is not None and prev.null_pct is not None:
            delta = round(col.null_pct - prev.null_pct, 6)
            if delta > 0:
                null_increase_count += 1
        column_deltas.append({
            "column_name": col.column_name,
            "null_pct": col.null_pct or 0.0,
            "null_pct_delta": delta,
            "data_type": col.data_type,
        })

    column_deltas.sort(
        key=lambda c: c["null_pct_delta"] if c["null_pct_delta"] is not None else 0,
        reverse=True,
    )

    row_delta = None
    row_delta_pct = None
    if latest and previous and previous.row_count:
        row_delta = latest.row_count - previous.row_count
        row_delta_pct = round((row_delta / previous.row_count) * 100, 2)

    avg_null = _avg_null_pct(latest_cols)
    prev_avg_null = _avg_null_pct(previous_cols)
    avg_null_delta = None
    if avg_null is not None and prev_avg_null is not None:
        avg_null_delta = round(avg_null - prev_avg_null, 6)

    alerts_total = (
        db.query(models.Alert)
        .filter(models.Alert.dataset_id == dataset_id)
        .count()
    )

    return {
        "dataset_id": dataset_id,
        "run_count": len(runs),
        "latest_run": latest,
        "previous_run": previous,
        "row_count_delta": row_delta,
        "row_count_delta_pct": row_delta_pct,
        "column_count": len(latest_cols) if latest_cols else None,
        "avg_null_pct": avg_null,
        "avg_null_pct_delta": avg_null_delta,
        "columns_with_null_increase": null_increase_count,
        "alerts_total": alerts_total,
        "alerts_last_24h": status_data["alerts_last_24h"],
        "status": status_data["status"],
        "top_column_deltas": column_deltas[:10],
    }
