from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Double
from app.db.database import Base
from app.models.dataset import Dataset


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(primary_key=True)

    # user defined properties
    name: Mapped[str] = mapped_column(String, index=True)
    filepath: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String, default="", server_default="")

    # backend processed properties
    fps: Mapped[int] = mapped_column(Integer, default=0,server_default="0")
    total_length_seconds: Mapped[float] = mapped_column(Double, default=0,server_default="0")

    landmarks: Mapped[list["Landmark"]] = relationship(back_populates="video")
    clips: Mapped[list["Clip"]] = relationship(back_populates="video")

    dataset_id: Mapped[int | None] = mapped_column(ForeignKey("datasets.id", ondelete="SET NULL"))
    dataset: Mapped["Dataset | None"] = relationship(back_populates='videos')



