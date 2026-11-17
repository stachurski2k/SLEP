from sqlalchemy import inspect

from ..domain.entities import Exercise, Lesson, Media, Unit
from ..domain.value_objects import (
    ContentStatus,
    Difficulty,
    ExerciseType,
    MediaType,
)
from .models import ExerciseModel, LessonModel, MediaModel, UnitModel


class LearningMapper:
    """Mapper between domain entities and persistence models."""

    @staticmethod
    def _is_loaded(model: object, attr: str) -> bool:
        try:
            state = inspect(model)
            return attr in state.dict
        except Exception:
            return hasattr(model, attr) and getattr(model, attr) is not None

    @staticmethod
    def unit_to_domain(model: UnitModel) -> Unit:
        lessons = (
            [LearningMapper.lesson_to_domain(l) for l in model.lessons]
            if LearningMapper._is_loaded(model, "lessons") and model.lessons
            else []
        )
        return Unit(
            id=model.id,
            title=model.title,
            order=model.order_no,
            lessons=lessons,
        )

    @staticmethod
    def unit_to_persistence(
        entity: Unit, existing_model: UnitModel | None = None
    ) -> UnitModel:
        if existing_model is None:
            return UnitModel(
                id=entity.id,
                title=entity.title,
                order_no=entity.order,
            )
        existing_model.title = entity.title
        existing_model.order_no = entity.order
        return existing_model

    @staticmethod
    def lesson_to_domain(model: LessonModel) -> Lesson:
        exercises = (
            [LearningMapper.exercise_to_domain(e) for e in model.exercises]
            if LearningMapper._is_loaded(model, "exercises") and model.exercises
            else []
        )
        return Lesson(
            id=model.id,
            unitId=model.unit_id,
            title=model.title,
            description=model.description,
            order=model.order_no,
            status=ContentStatus(model.status),
            exercises=exercises,
        )

    @staticmethod
    def lesson_to_persistence(
        entity: Lesson, existing_model: LessonModel | None = None
    ) -> LessonModel:
        if existing_model is None:
            return LessonModel(
                id=entity.id,
                unit_id=entity.unitId,
                title=entity.title,
                description=entity.description,
                order_no=entity.order,
                status=entity.status.value,
            )
        existing_model.title = entity.title
        existing_model.description = entity.description
        existing_model.order_no = entity.order
        existing_model.status = entity.status.value
        return existing_model

    @staticmethod
    def exercise_to_domain(model: ExerciseModel) -> Exercise:
        media_list = (
            [LearningMapper.media_to_domain(m) for m in model.media]
            if LearningMapper._is_loaded(model, "media") and model.media
            else []
        )
        return Exercise(
            id=model.id,
            lessonId=model.lesson_id,
            type=ExerciseType(model.type),
            difficulty=Difficulty(model.difficulty),
            points=model.points,
            content=model.content,
            answer=model.answer,
            media=media_list,
        )

    @staticmethod
    def exercise_to_persistence(
        entity: Exercise, existing_model: ExerciseModel | None = None
    ) -> ExerciseModel:
        if existing_model is None:
            media_models = [
                MediaModel(
                    id=m.id,
                    exercise_id=entity.id,
                    type=m.type.value,
                    url=m.url,
                )
                for m in entity.media
            ]
            return ExerciseModel(
                id=entity.id,
                lesson_id=entity.lessonId,
                type=entity.type.value,
                difficulty=entity.difficulty.value,
                points=entity.points,
                content=entity.content,
                answer=entity.answer,
                media=media_models,
            )
        existing_model.type = entity.type.value
        existing_model.difficulty = entity.difficulty.value
        existing_model.points = entity.points
        existing_model.content = entity.content
        existing_model.answer = entity.answer
        return existing_model

    @staticmethod
    def media_to_domain(model: MediaModel) -> Media:
        return Media(
            id=model.id,
            exerciseId=model.exercise_id,
            type=MediaType(model.type),
            url=model.url,
        )
