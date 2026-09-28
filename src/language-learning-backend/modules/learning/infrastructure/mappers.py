from ..domain.entities import Course, Exercise, Lesson, Media, Unit
from ..domain.value_objects import (
    ContentStatus,
    Difficulty,
    ExerciseType,
    MediaType,
    SignLanguage,
)
from .models import CourseModel, ExerciseModel, LessonModel, MediaModel, UnitModel


class LearningMapper:
    """Mapper between domain entities and persistence models."""

    @staticmethod
    def course_to_domain(model: CourseModel) -> Course:
        units = [LearningMapper.unit_to_domain(u) for u in model.units] if model.units else []
        return Course(
            id=model.id,
            title=model.title,
            description=model.description,
            difficulty=Difficulty(model.difficulty),
            language=SignLanguage(model.language),
            status=ContentStatus(model.status),
            createdAt=model.created_at,
            units=units,
        )

    @staticmethod
    def course_to_persistence(
        entity: Course, existing_model: CourseModel | None = None
    ) -> CourseModel:
        if existing_model is None:
            return CourseModel(
                id=entity.id,
                title=entity.title,
                description=entity.description,
                difficulty=entity.difficulty.value,
                language=entity.language.value,
                status=entity.status.value,
                created_at=entity.createdAt,
            )
        existing_model.title = entity.title
        existing_model.description = entity.description
        existing_model.difficulty = entity.difficulty.value
        existing_model.language = entity.language.value
        existing_model.status = entity.status.value
        return existing_model

    @staticmethod
    def unit_to_domain(model: UnitModel) -> Unit:
        lessons = [LearningMapper.lesson_to_domain(l) for l in model.lessons] if model.lessons else []
        return Unit(
            id=model.id,
            courseId=model.course_id,
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
                course_id=entity.courseId,
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
            if model.exercises
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
            if model.media
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
