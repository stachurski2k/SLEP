from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from app.db.database import Base

class GestureClass(Base):
    __tablename__ = "gesture_classes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column("name")

    clips: Mapped["Clip"] = relationship(back_populates="gesture_class")


