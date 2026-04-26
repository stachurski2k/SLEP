from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from app.db.database import Base

class GestureType(Base):
    __tablename__ = "gesture_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()

    clips: Mapped["Clip"] = relationship(back_populates="gesture_type")
