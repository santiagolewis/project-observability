import uuid
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from .database import Base
from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import Float


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




class ColumnProfile(Base):
    __tablename__ = "column_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_run_id = Column(UUID(as_uuid=True), ForeignKey("dataset_runs.id"))

    column_name = Column(String)
    data_type = Column(String)
    null_count = Column(Integer)

    mean = Column(Float, nullable=True)
    std = Column(Float, nullable=True)
    min = Column(Float, nullable=True)
    max = Column(Float, nullable=True)

    dataset_run = relationship("DatasetRun")