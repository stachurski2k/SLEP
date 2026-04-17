from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from app.db.database import Base

class Landmark(Base):
    __tablename__ = 'landmarks'

    id: Mapped[int] = mapped_column(primary_key=True)
    filepath: Mapped[str] = mapped_column()

    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"))
    video: Mapped["Video"] = relationship(back_populates="landmarks")
