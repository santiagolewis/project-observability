import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class DatasetRun(Base):
    __tablename__ = "dataset_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    row_count = Column(Integer)

    dataset = relationship("Dataset")
    column_profiles = relationship("ColumnProfile", back_populates="dataset_run")


class ColumnProfile(Base):
    __tablename__ = "column_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_run_id = Column(UUID(as_uuid=True), ForeignKey("dataset_runs.id"))

    column_name = Column(String)
    data_type = Column(String)
    null_count = Column(Integer)
    null_pct = Column(Float, nullable=True)

    mean = Column(Float, nullable=True)
    std = Column(Float, nullable=True)
    min = Column(Float, nullable=True)
    max = Column(Float, nullable=True)

    dataset_run = relationship("DatasetRun", back_populates="column_profiles")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"))
    dataset_run_id = Column(UUID(as_uuid=True), ForeignKey("dataset_runs.id"), nullable=True)

    message = Column(String)
    severity = Column(String)  # low, medium, high

    column_name = Column(String, nullable=True)
    metric = Column(String, nullable=True)
    previous_value = Column(String, nullable=True)
    current_value = Column(String, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
