from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime
from app.db.database import Base

class ExportedDataset(Base):
    __tablename__ = "exported_datasets"

    id: Mapped[int] = mapped_column(primary_key=True)
    filepath: Mapped[str] = mapped_column(String)
    videos_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    original_dataset_id: Mapped[int] = mapped_column(Integer, index=True)
    original_dataset_name: Mapped[str] = mapped_column(String, index=True)
    original_dataset_description: Mapped[str] = mapped_column(String)




