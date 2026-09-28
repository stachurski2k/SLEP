import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class CourseModel(Base):
    """Persistence model for language courses."""
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    language: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    units: Mapped[list["UnitModel"]] = relationship(
        "UnitModel",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="UnitModel.order_no",
    )


class UnitModel(Base):
    """Persistence model for course thematic units."""
    __tablename__ = "units"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    order_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    course: Mapped["CourseModel"] = relationship("CourseModel", back_populates="units")
    lessons: Mapped[list["LessonModel"]] = relationship(
        "LessonModel",
        back_populates="unit",
        cascade="all, delete-orphan",
        order_by="LessonModel.order_no",
    )


class LessonModel(Base):
    """Persistence model for unit lessons."""
    __tablename__ = "lessons"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    order_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)

    unit: Mapped["UnitModel"] = relationship("UnitModel", back_populates="lessons")
    exercises: Mapped[list["ExerciseModel"]] = relationship(
        "ExerciseModel",
        back_populates="lesson",
        cascade="all, delete-orphan",
    )


class ExerciseModel(Base):
    """Persistence model for interactive skills-first exercises."""
    __tablename__ = "exercises"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # "single" / "sentence"
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)

    lesson: Mapped["LessonModel"] = relationship("LessonModel", back_populates="exercises")
    media: Mapped[list["MediaModel"]] = relationship(
        "MediaModel",
        back_populates="exercise",
        cascade="all, delete-orphan",
    )


class MediaModel(Base):
    """Persistence model for exercise media assets."""
    __tablename__ = "exercise_media"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exercises.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # "video" / "image"
    url: Mapped[str] = mapped_column(String(500), nullable=False)

    exercise: Mapped["ExerciseModel"] = relationship("ExerciseModel", back_populates="media")
