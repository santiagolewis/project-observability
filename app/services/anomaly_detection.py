from app.db import models

def detect_anomalies(db, dataset_id, current_run):
    alerts = []

    # buscar run anterior
    previous_run = (
        db.query(models.DatasetRun)
        .filter(models.DatasetRun.dataset_id == dataset_id)
        .order_by(models.DatasetRun.created_at.desc())
        .offset(1)
        .first()
    )

    if not previous_run:
        return alerts

    # comparar row_count
    if current_run.row_count < previous_run.row_count * 0.8:
        alerts.append({
            "message": "Row count dropped significantly",
            "severity": "high"
        })

    return alerts