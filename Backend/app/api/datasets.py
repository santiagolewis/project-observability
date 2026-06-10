from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.schemas import (
    AlertOut,
    DatasetOut,
    DatasetRunDetailOut,
    DatasetRunOut,
    DatasetStatusOut,
    DatasetSummaryOut,
)
from app.db import models
from app.db.database import get_db
from app.db.models import Alert, ColumnProfile, DatasetRun
from app.services.anomaly_detection import detect_anomalies
from app.services.kpi import build_dataset_summary, get_ordered_runs, resolve_dataset_status
from app.services.profiling import UnsupportedFileError, profile_dataset

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


@router.get("/datasets/{dataset_id}/status", response_model=DatasetStatusOut)
def get_dataset_status(dataset_id: str, db: Session = Depends(get_db)):
    _get_dataset_or_404(db, dataset_id)
    return resolve_dataset_status(db, dataset_id)


@router.get("/datasets/{dataset_id}/summary", response_model=DatasetSummaryOut)
def get_dataset_summary(dataset_id: str, db: Session = Depends(get_db)):
    _get_dataset_or_404(db, dataset_id)
    return build_dataset_summary(db, dataset_id)


@router.post("/datasets", response_model=DatasetOut)
def create_dataset(
    name: str,
    description: str | None = None,
    db: Session = Depends(get_db),
):
    dataset = models.Dataset(name=name, description=description)
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


@router.get("/datasets", response_model=list[DatasetOut])
def get_datasets(db: Session = Depends(get_db)):
    return db.query(models.Dataset).all()


@router.post("/datasets/{dataset_id}/upload")
def upload_dataset(
    dataset_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    _get_dataset_or_404(db, dataset_id)

    try:
        profile = profile_dataset(file.file, filename=file.filename)
    except UnsupportedFileError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    run = DatasetRun(
        dataset_id=dataset_id,
        row_count=profile["row_count"],
    )

    alert_payloads = detect_anomalies(db, dataset_id, run, profile)

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
                    mean=col.get("mean"),
                    std=col.get("std"),
                    min=col.get("min"),
                    max=col.get("max"),
                )
            )

        for alert in alert_payloads:
            db.add(
                Alert(
                    dataset_id=dataset_id,
                    dataset_run_id=run.id,
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
    }


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
