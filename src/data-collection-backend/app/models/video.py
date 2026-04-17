from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from app.db.database import Base

class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True)
    filepath: Mapped[str] = mapped_column(String)

    landmarks: Mapped[list["Landmark"]] = relationship(back_populates="video")
    clips: Mapped[list["Clip"]] = relationship(back_populates="video")



