from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None


class DatasetRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dataset_id: UUID
    created_at: Optional[datetime] = None
    row_count: Optional[int] = None


class ColumnProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    column_name: str
    data_type: Optional[str] = None
    null_count: Optional[int] = None
    null_pct: Optional[float] = None
    mean: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None


class DatasetRunDetailOut(BaseModel):
    run: DatasetRunOut
    columns: list[ColumnProfileOut]


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dataset_id: UUID
    dataset_run_id: Optional[UUID] = None
    message: str
    severity: str
    column_name: Optional[str] = None
    metric: Optional[str] = None
    previous_value: Optional[str] = None
    current_value: Optional[str] = None
    created_at: Optional[datetime] = None


class DatasetStatusOut(BaseModel):
    status: str
    message: Optional[str] = None
    last_run_at: Optional[datetime] = None
    alerts_last_24h: int = 0
    row_count: Optional[int] = None
    row_count_vs_avg_pct: Optional[float] = None
    high_severity_alerts_24h: int = 0


class ColumnKpiDelta(BaseModel):
    column_name: str
    null_pct: float
    null_pct_delta: Optional[float] = None
    data_type: Optional[str] = None


class DatasetSummaryOut(BaseModel):
    dataset_id: UUID
    run_count: int
    latest_run: Optional[DatasetRunOut] = None
    previous_run: Optional[DatasetRunOut] = None
    row_count_delta: Optional[int] = None
    row_count_delta_pct: Optional[float] = None
    column_count: Optional[int] = None
    avg_null_pct: Optional[float] = None
    avg_null_pct_delta: Optional[float] = None
    columns_with_null_increase: int = 0
    alerts_total: int = 0
    alerts_last_24h: int = 0
    status: str
    top_column_deltas: list[ColumnKpiDelta] = []
