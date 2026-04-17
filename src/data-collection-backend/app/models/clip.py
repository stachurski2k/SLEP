from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from app.db.database import Base


class Clip(Base):
    __tablename__ = "clips"

    id: Mapped[int] = mapped_column(primary_key=True)
    start_frame_index: Mapped[int] = mapped_column()
    end_frame_index: Mapped[int] = mapped_column()

    #foreign keys
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"))
    video: Mapped["Video"] = relationship(back_populates="clips")

    gesture_class_id: Mapped[int] = mapped_column(ForeignKey("gesture_classes.id"))
    gesture_class: Mapped["GestureClass"] = relationship(back_populates="clips")

    gesture_type_id: Mapped[int] = mapped_column(ForeignKey("gesture_types.id"))
    gesture_type: Mapped["GestureType"] = relationship(back_populates="clips")


