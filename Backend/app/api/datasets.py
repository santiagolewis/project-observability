from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.schemas import (
    AlertOut,
    DatasetCreate,
    DatasetOut,
    DatasetRunDetailOut,
    DatasetRunOut,
    DatasetStatusOut,
    DatasetSummaryOut,
    DatasetTrendsOut,
    DatasetUpdate,
    IncidentDetailOut,
    IncidentOut,
    IncidentUpdate,
    RuleCreate,
    RuleOut,
    RuleUpdate,
)
from app.db import models
from app.db.database import get_db
from app.db.models import Alert, ColumnProfile, DatasetRun
from app.services.anomaly_detection import detect_anomalies
from app.services.incidents import VALID_STATUSES, assign_incident, update_incident
from app.services.kpi import (
    build_dataset_summary,
    build_dataset_trends,
    get_ordered_runs,
    resolve_dataset_status,
)
from app.services.profiling import (
    UnsupportedFileError,
    profile_dataframe,
    read_dataframe,
)
from app.services.rules import RULE_TYPES, evaluate_rules

router = APIRouter()


def _get_dataset_or_404(db: Session, dataset_id: str) -> models.Dataset:
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


def _get_run_or_404(db: Session, dataset_id: str, run_id: str) -> DatasetRun:
    run = (
        db.query(DatasetRun)
        .filter(DatasetRun.id == run_id, DatasetRun.dataset_id == dataset_id)
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


# ---------------------------------------------------------------------------
# Datasets
# ---------------------------------------------------------------------------
@router.get("/datasets", response_model=list[DatasetOut])
def get_datasets(db: Session = Depends(get_db)):
    return db.query(models.Dataset).order_by(models.Dataset.created_at.desc()).all()


@router.post("/datasets", response_model=DatasetOut)
def create_dataset(payload: DatasetCreate, db: Session = Depends(get_db)):
    dataset = models.Dataset(
        name=payload.name,
        description=payload.description,
        owner=payload.owner,
        team=payload.team,
        domain=payload.domain,
        criticality=payload.criticality or "medium",
        expected_freshness_hours=payload.expected_freshness_hours,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


@router.get("/datasets/{dataset_id}", response_model=DatasetOut)
def get_dataset(dataset_id: str, db: Session = Depends(get_db)):
    return _get_dataset_or_404(db, dataset_id)


@router.patch("/datasets/{dataset_id}", response_model=DatasetOut)
def update_dataset(
    dataset_id: str,
    payload: DatasetUpdate,
    db: Session = Depends(get_db),
):
    dataset = _get_dataset_or_404(db, dataset_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(dataset, field, value)
    db.commit()
    db.refresh(dataset)
    return dataset


@router.get("/datasets/{dataset_id}/status", response_model=DatasetStatusOut)
def get_dataset_status(dataset_id: str, db: Session = Depends(get_db)):
    _get_dataset_or_404(db, dataset_id)
    return resolve_dataset_status(db, dataset_id)


@router.get("/datasets/{dataset_id}/summary", response_model=DatasetSummaryOut)
def get_dataset_summary(dataset_id: str, db: Session = Depends(get_db)):
    _get_dataset_or_404(db, dataset_id)
    return build_dataset_summary(db, dataset_id)


@router.get("/datasets/{dataset_id}/trends", response_model=DatasetTrendsOut)
def get_dataset_trends(dataset_id: str, db: Session = Depends(get_db)):
    _get_dataset_or_404(db, dataset_id)
    return build_dataset_trends(db, dataset_id)


# ---------------------------------------------------------------------------
# Upload / ingestion
# ---------------------------------------------------------------------------
@router.post("/datasets/{dataset_id}/upload")
def upload_dataset(
    dataset_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    _get_dataset_or_404(db, dataset_id)

    try:
        df = read_dataframe(file.file, filename=file.filename)
    except UnsupportedFileError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    profile = profile_dataframe(df)

    run = DatasetRun(
        dataset_id=dataset_id,
        row_count=profile["row_count"],
    )

    # Anomalies (run-over-run) + configurable rule violations (value-level).
    alert_payloads = detect_anomalies(db, dataset_id, run, profile)
    alert_payloads += evaluate_rules(db, dataset_id, df)

    try:
        db.add(run)
        db.flush()

        for col in profile["columns"]:
            db.add(
                ColumnProfile(
                    dataset_run_id=run.id,
                    column_name=col["column_name"],
                    data_type=col["data_type"],
                    null_count=col["null_count"],
                    null_pct=col["null_pct"],
                    distinct_count=col.get("distinct_count"),
                    mean=col.get("mean"),
                    std=col.get("std"),
                    min=col.get("min"),
                    max=col.get("max"),
                )
            )

        incident = assign_incident(db, dataset_id, alert_payloads, run_id=run.id)

        for alert in alert_payloads:
            db.add(
                Alert(
                    dataset_id=dataset_id,
                    dataset_run_id=run.id,
                    incident_id=incident.id if incident else None,
                    message=alert["message"],
                    severity=alert["severity"],
                    column_name=alert.get("column_name"),
                    metric=alert.get("metric"),
                    previous_value=alert.get("previous_value"),
                    current_value=alert.get("current_value"),
                )
            )

        db.commit()
        db.refresh(run)
    except Exception:
        db.rollback()
        raise

    return {
        "message": "Dataset processed",
        "run_id": str(run.id),
        "alerts_created": len(alert_payloads),
        "incident_id": str(incident.id) if incident else None,
    }


# ---------------------------------------------------------------------------
# Alerts / runs
# ---------------------------------------------------------------------------
@router.get("/datasets/{dataset_id}/alerts", response_model=list[AlertOut])
def get_alerts(dataset_id: str, db: Session = Depends(get_db)):
    _get_dataset_or_404(db, dataset_id)
    return (
        db.query(models.Alert)
        .filter(models.Alert.dataset_id == dataset_id)
        .order_by(models.Alert.created_at.desc())
        .all()
    )


@router.get("/datasets/{dataset_id}/runs", response_model=list[DatasetRunOut])
def get_runs(dataset_id: str, db: Session = Depends(get_db)):
    _get_dataset_or_404(db, dataset_id)
    return get_ordered_runs(db, dataset_id)


@router.get(
    "/datasets/{dataset_id}/runs/{run_id}",
    response_model=DatasetRunDetailOut,
)
def get_run_detail(
    dataset_id: str,
    run_id: UUID,
    db: Session = Depends(get_db),
):
    _get_dataset_or_404(db, dataset_id)
    run = _get_run_or_404(db, dataset_id, str(run_id))
    columns = (
        db.query(ColumnProfile)
        .filter(ColumnProfile.dataset_run_id == run.id)
        .order_by(ColumnProfile.column_name)
        .all()
    )
    return {"run": run, "columns": columns}


# ---------------------------------------------------------------------------
# Configurable rules
# ---------------------------------------------------------------------------
@router.get("/datasets/{dataset_id}/rules", response_model=list[RuleOut])
def get_rules(dataset_id: str, db: Session = Depends(get_db)):
    _get_dataset_or_404(db, dataset_id)
    return (
        db.query(models.DatasetRule)
        .filter(models.DatasetRule.dataset_id == dataset_id)
        .order_by(models.DatasetRule.created_at.desc())
        .all()
    )


@router.post("/datasets/{dataset_id}/rules", response_model=RuleOut)
def create_rule(dataset_id: str, payload: RuleCreate, db: Session = Depends(get_db)):
    _get_dataset_or_404(db, dataset_id)
    if payload.rule_type not in RULE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid rule_type. Must be one of: {', '.join(sorted(RULE_TYPES))}",
        )
    rule = models.DatasetRule(
        dataset_id=dataset_id,
        column_name=payload.column_name,
        rule_type=payload.rule_type,
        config=payload.config or {},
        severity=payload.severity or "high",
        is_active=payload.is_active,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.patch("/datasets/{dataset_id}/rules/{rule_id}", response_model=RuleOut)
def update_rule(
    dataset_id: str,
    rule_id: UUID,
    payload: RuleUpdate,
    db: Session = Depends(get_db),
):
    _get_dataset_or_404(db, dataset_id)
    rule = (
        db.query(models.DatasetRule)
        .filter(
            models.DatasetRule.id == rule_id,
            models.DatasetRule.dataset_id == dataset_id,
        )
        .first()
    )
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    data = payload.model_dump(exclude_unset=True)
    if "rule_type" in data and data["rule_type"] not in RULE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid rule_type")
    for field, value in data.items():
        setattr(rule, field, value)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/datasets/{dataset_id}/rules/{rule_id}")
def delete_rule(dataset_id: str, rule_id: UUID, db: Session = Depends(get_db)):
    _get_dataset_or_404(db, dataset_id)
    rule = (
        db.query(models.DatasetRule)
        .filter(
            models.DatasetRule.id == rule_id,
            models.DatasetRule.dataset_id == dataset_id,
        )
        .first()
    )
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
    return {"message": "Rule deleted"}


# ---------------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------------
@router.get("/datasets/{dataset_id}/incidents", response_model=list[IncidentOut])
def get_incidents(dataset_id: str, db: Session = Depends(get_db)):
    _get_dataset_or_404(db, dataset_id)
    return (
        db.query(models.Incident)
        .filter(models.Incident.dataset_id == dataset_id)
        .order_by(models.Incident.updated_at.desc())
        .all()
    )


@router.get(
    "/datasets/{dataset_id}/incidents/{incident_id}",
    response_model=IncidentDetailOut,
)
def get_incident_detail(
    dataset_id: str,
    incident_id: UUID,
    db: Session = Depends(get_db),
):
    _get_dataset_or_404(db, dataset_id)
    incident = (
        db.query(models.Incident)
        .filter(
            models.Incident.id == incident_id,
            models.Incident.dataset_id == dataset_id,
        )
        .first()
    )
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    alerts = (
        db.query(models.Alert)
        .filter(models.Alert.incident_id == incident.id)
        .order_by(models.Alert.created_at.desc())
        .all()
    )
    return IncidentDetailOut(
        **IncidentOut.model_validate(incident).model_dump(),
        alerts=[AlertOut.model_validate(a) for a in alerts],
    )


@router.patch(
    "/datasets/{dataset_id}/incidents/{incident_id}",
    response_model=IncidentOut,
)
def patch_incident(
    dataset_id: str,
    incident_id: UUID,
    payload: IncidentUpdate,
    db: Session = Depends(get_db),
):
    _get_dataset_or_404(db, dataset_id)
    incident = (
        db.query(models.Incident)
        .filter(
            models.Incident.id == incident_id,
            models.Incident.dataset_id == dataset_id,
        )
        .first()
    )
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if payload.status is not None and payload.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}",
        )
    try:
        return update_incident(
            db, incident, status=payload.status, assignee=payload.assignee
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
