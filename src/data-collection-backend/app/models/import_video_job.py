from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime
from app.db.database import Base
import enum
from sqlalchemy import Column, Enum
from datetime import datetime, date

class ImportVideoJobStatusEnum(enum.Enum):
    in_queue = "in_queue"
    processing = "processing"
    done = "done"
    error = "error"

class ImportVideoJob(Base):
    __tablename__ = "import_video_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)

    # processing properties
    status: Mapped[ImportVideoJobStatusEnum] = mapped_column(Enum(ImportVideoJobStatusEnum))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # future video entity properties
    video_name: Mapped[str] = mapped_column()
    video_filepath: Mapped[str] = mapped_column()
    video_description: Mapped[str] = mapped_column()
    dataset_id: Mapped[int | None] = mapped_column()

    # post-processing properties
    # they will be set after the video is imported to the system
    error_message: Mapped[str | None] = mapped_column()
    video_id: Mapped[int | None] = mapped_column()



