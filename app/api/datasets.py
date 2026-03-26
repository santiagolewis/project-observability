from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models
from fastapi import UploadFile, File, HTTPException
from app.services.profiling import profile_dataset
from app.db.models import DatasetRun, ColumnProfile



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