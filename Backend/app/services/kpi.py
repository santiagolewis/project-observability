from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.db import models
from app.services import thresholds as t
from app.services.incidents import LIVE_STATUSES

_SEVERITY_RANK = {"healthy": 0, "warning": 1, "critical": 2}


def _worst(*statuses: Optional[str]) -> str:
    best = "healthy"
    for s in statuses:
        if s and _SEVERITY_RANK.get(s, 0) > _SEVERITY_RANK.get(best, 0):
            best = s
    return best


def _as_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


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
    """Count recent alerts, excluding those belonging to muted/resolved incidents."""
    q = db.query(models.Alert).filter(
        models.Alert.dataset_id == dataset_id,
        models.Alert.created_at >= since,
    )
    if severity:
        q = q.filter(models.Alert.severity == severity)

    # Suppress alerts that have been muted/resolved via their incident.
    q = q.outerjoin(models.Incident, models.Alert.incident_id == models.Incident.id).filter(
        (models.Alert.incident_id.is_(None))
        | (models.Incident.status.in_(LIVE_STATUSES))
    )
    return q.count()


def compute_row_status(latest_row_count: int, avg_row_count: float) -> Optional[str]:
    if latest_row_count < avg_row_count * t.ROW_COUNT_CRITICAL_RATIO:
        return "critical"
    if latest_row_count < avg_row_count * t.ROW_COUNT_WARNING_RATIO:
        return "warning"
    return None


def compute_freshness(dataset, last_run_at: Optional[datetime]) -> dict:
    """Evaluate whether a dataset is updated within its expected window.

    Note: this is evaluated on read. Without a scheduler (Phase 2) we cannot
    proactively alert on staleness, but we surface it in status and summary.
    """
    expected = getattr(dataset, "expected_freshness_hours", None)
    last_run_at = _as_utc(last_run_at)

    result = {
        "expected_freshness_hours": expected,
        "last_run_at": last_run_at,
        "age_hours": None,
        "is_stale": False,
        "freshness_status": None,  # None when not monitored, else healthy/warning/critical
    }

    if not expected or last_run_at is None:
        return result

    now = datetime.now(timezone.utc)
    age_hours = (now - last_run_at).total_seconds() / 3600.0
    result["age_hours"] = round(age_hours, 2)

    if age_hours > expected * t.FRESHNESS_CRITICAL_MULTIPLIER:
        result["freshness_status"] = "critical"
        result["is_stale"] = True
    elif age_hours > expected:
        result["freshness_status"] = "warning"
        result["is_stale"] = True
    else:
        result["freshness_status"] = "healthy"

    return result


def resolve_dataset_status(
    db: Session,
    dataset_id: str,
    runs: Optional[list[models.DatasetRun]] = None,
    dataset: Optional[models.Dataset] = None,
) -> dict:
    runs = runs if runs is not None else get_ordered_runs(db, dataset_id)
    if dataset is None:
        dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()

    now = datetime.now(timezone.utc)
    last_24h = now - timedelta(hours=24)

    alerts_24h = count_recent_alerts(db, dataset_id, last_24h)
    high_alerts_24h = count_recent_alerts(db, dataset_id, last_24h, severity="high")

    last_run_at = runs[0].created_at if runs else None
    freshness = compute_freshness(dataset, last_run_at)

    base = {
        "last_run_at": last_run_at,
        "alerts_last_24h": alerts_24h,
        "high_severity_alerts_24h": high_alerts_24h,
        "freshness_status": freshness["freshness_status"],
        "expected_freshness_hours": freshness["expected_freshness_hours"],
        "age_hours": freshness["age_hours"],
        "is_stale": freshness["is_stale"],
    }

    if len(runs) < 2:
        # Even while learning, a stale dataset is worth surfacing.
        status = "learning"
        if freshness["freshness_status"] in ("warning", "critical"):
            status = freshness["freshness_status"]
        return {
            **base,
            "status": status,
            "message": "Not enough runs to establish a baseline (need at least 2)"
            if status == "learning"
            else "Dataset is overdue for an update",
            "row_count": runs[0].row_count if runs else None,
            "row_count_vs_avg_pct": None,
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

    alert_status = None
    if high_alerts_24h > 0:
        alert_status = "critical"
    elif alerts_24h > 0:
        alert_status = "warning"

    status = _worst(row_status, alert_status, freshness["freshness_status"])
    if status == "healthy":
        message = None
    elif freshness["is_stale"] and status == freshness["freshness_status"]:
        message = "Dataset is overdue for an update"
    else:
        message = None

    return {
        **base,
        "status": status,
        "message": message,
        "row_count": last_run.row_count,
        "row_count_vs_avg_pct": row_vs_avg,
    }


def build_dataset_summary(db: Session, dataset_id: str) -> dict:
    runs = get_ordered_runs(db, dataset_id)
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    status_data = resolve_dataset_status(db, dataset_id, runs=runs, dataset=dataset)

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

    open_incidents = (
        db.query(models.Incident)
        .filter(
            models.Incident.dataset_id == dataset_id,
            models.Incident.status.in_(LIVE_STATUSES),
        )
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
        "open_incidents": open_incidents,
        "status": status_data["status"],
        "freshness_status": status_data["freshness_status"],
        "age_hours": status_data["age_hours"],
        "expected_freshness_hours": status_data["expected_freshness_hours"],
        "top_column_deltas": column_deltas[:10],
    }


def build_dataset_trends(db: Session, dataset_id: str) -> dict:
    """Return per-run time series for historical trend visualisations."""
    runs = (
        db.query(models.DatasetRun)
        .filter(models.DatasetRun.dataset_id == dataset_id)
        .order_by(models.DatasetRun.created_at.asc())
        .all()
    )

    points = []
    for run in runs:
        cols = get_run_columns(db, run.id)
        alert_count = (
            db.query(models.Alert)
            .filter(models.Alert.dataset_run_id == run.id)
            .count()
        )
        points.append({
            "run_id": run.id,
            "created_at": run.created_at,
            "row_count": run.row_count,
            "column_count": len(cols),
            "avg_null_pct": _avg_null_pct(cols),
            "alert_count": alert_count,
        })

    return {"dataset_id": dataset_id, "points": points}
