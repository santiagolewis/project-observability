from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models
from fastapi import UploadFile, File, HTTPException
from app.services.profiling import profile_dataset
from app.db.models import DatasetRun, ColumnProfile
from app.services.anomaly_detection import detect_anomalies
from app.db.models import Alert


router = APIRouter()


@router.post("/datasets")
def create_dataset(name: str, description: str = None, db: Session = Depends(get_db)):
    dataset = models.Dataset(
        name=name,
        description=description
    )

    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    return dataset



@router.get("/datasets")
def get_datasets(db: Session = Depends(get_db)):
    datasets = db.query(models.Dataset).all()
    return datasets

@router.post("/datasets/{dataset_id}/upload")
def upload_dataset(
    dataset_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # verificar dataset existe
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # profiling
    profile = profile_dataset(file.file)

    # guardar dataset run
    run = DatasetRun(
        dataset_id=dataset_id,
        row_count=profile["row_count"]
    )

    

    alerts = detect_anomalies(db, dataset_id, run)

    for alert in alerts:
        db.add(Alert(
            dataset_id=dataset_id,
            message=alert["message"],
            severity=alert["severity"]
        ))

    db.commit()

    db.add(run)
    db.commit()
    db.refresh(run)

    # guardar columnas
    for col in profile["columns"]:
        col_profile = ColumnProfile(
            dataset_run_id=run.id,
            column_name=col["column_name"],
            data_type=col["data_type"],
            null_count=col["null_count"],
            mean=col.get("mean"),
            std=col.get("std"),
            min=col.get("min"),
            max=col.get("max"),
        )
        db.add(col_profile)

    db.commit()

    return {
        "message": "Dataset processed",
        "run_id": str(run.id)
    }


@router.get("/datasets/{dataset_id}/alerts")
def get_alerts(dataset_id: str, db: Session = Depends(get_db)):
    alerts = db.query(models.Alert).filter(models.Alert.dataset_id == dataset_id).all()
    return alerts


@router.get("/datasets/{dataset_id}/runs")
def get_runs(dataset_id: str, db: Session = Depends(get_db)):
    runs = db.query(models.DatasetRun).filter(
        models.DatasetRun.dataset_id == dataset_id
    ).all()
    return runs