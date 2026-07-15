import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Phase 1: ownership & governance metadata
    owner = Column(String, nullable=True)
    team = Column(String, nullable=True)
    domain = Column(String, nullable=True)
    criticality = Column(String, nullable=False, default="medium")  # low/medium/high/critical

    # Phase 1: freshness expectations (how often the dataset should be updated)
    expected_freshness_hours = Column(Integer, nullable=True)

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
    distinct_count = Column(Integer, nullable=True)

    mean = Column(Float, nullable=True)
    std = Column(Float, nullable=True)
    min = Column(Float, nullable=True)
    max = Column(Float, nullable=True)

    dataset_run = relationship("DatasetRun", back_populates="column_profiles")


class DatasetRule(Base):
    """A configurable data-quality expectation for a dataset or column.

    ``rule_type`` determines how ``config`` is interpreted:
      - column_required : column_name must exist            (config: {})
      - not_null        : null rate must be 0 (or <= max_null_pct)
                          (config: {"max_null_pct": float})
      - min_value       : numeric min >= value              (config: {"value": float})
      - max_value       : numeric max <= value              (config: {"value": float})
      - accepted_values : every value within a set          (config: {"values": [...]})
      - unique          : column has no duplicates          (config: {})
      - regex           : every string matches a pattern    (config: {"pattern": str})
    """

    __tablename__ = "dataset_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"))

    column_name = Column(String, nullable=True)  # null => dataset-level rule
    rule_type = Column(String, nullable=False)
    config = Column(JSONB, nullable=False, default=dict)
    severity = Column(String, nullable=False, default="high")  # medium/high
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)


class Incident(Base):
    """An operational problem that groups one or more related alerts."""

    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"))

    title = Column(String, nullable=False)
    status = Column(String, nullable=False, default="open")  # open/acknowledged/resolved/muted
    severity = Column(String, nullable=False, default="medium")  # medium/high
    assignee = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    alerts = relationship("Alert", back_populates="incident")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"))
    dataset_run_id = Column(UUID(as_uuid=True), ForeignKey("dataset_runs.id"), nullable=True)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=True)

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

    incident = relationship("Incident", back_populates="alerts")
