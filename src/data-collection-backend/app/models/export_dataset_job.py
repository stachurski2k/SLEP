from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Enum
from app.db.database import Base


class ExportDatasetJobStatusEnum(enum.Enum):
    in_queue = "in_queue"
    processing = "processing"
    done = "done"
    error = "error"

class ExportDatasetJob(Base):
    __tablename__ = "export_dataset_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)

    # properties
    original_dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"))

    # processing properties
    status: Mapped[ExportDatasetJobStatusEnum] = mapped_column(Enum(ExportDatasetJobStatusEnum))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # post-processing properties
    error_message: Mapped[str | None] = mapped_column()
    exported_dataset_id: Mapped[int | None] = mapped_column()








