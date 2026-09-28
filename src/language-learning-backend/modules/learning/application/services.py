from datetime import datetime, timezone
from uuid import UUID, uuid4

from ..domain.entities import Course, Exercise, Lesson, Media, Unit
from ..domain.exceptions import (
    CourseNotFoundError,
    ExerciseNotFoundError,
    LessonNotFoundError,
    UnitNotFoundError,
)
from ..domain.repositories import (
    CourseRepository,
    ExerciseRepository,
    LessonRepository,
    UnitRepository,
)
from ..domain.value_objects import (
    ContentStatus,
    Difficulty,
    ExerciseType,
    MediaType,
    SignLanguage,
)
from .commands import (
    CreateCourseCommand,
    CreateExerciseCommand,
    CreateLessonCommand,
    CreateUnitCommand,
    UpdateCourseCommand,
    UpdateExerciseCommand,
    UpdateLessonCommand,
    UpdateUnitCommand,
    ValidateAnswerCommand,
)
from .dtos import (
    CourseDetailsDTO,
    CourseDTO,
    ExerciseDTO,
    ExercisePublicDTO,
    LessonDetailsDTO,
    LessonDTO,
    MediaDTO,
    UnitDetailsDTO,
    UnitDTO,
    ValidationResultDTO,
)
from .interfaces import (
    CourseApplicationService,
    ExerciseApplicationService,
    LessonApplicationService,
    UnitApplicationService,
)


class CourseApplicationServiceImpl(CourseApplicationService):
    """Implementation of CourseApplicationService handling course lifecycle."""

    def __init__(
        self,
        course_repository: CourseRepository,
        unit_repository: UnitRepository,
        lesson_repository: LessonRepository,
    ) -> None:
        self._course_repo = course_repository
        self._unit_repo = unit_repository
        self._lesson_repo = lesson_repository

    async def createCourse(self, command: CreateCourseCommand) -> CourseDTO:
        difficulty_vo = Difficulty(command.difficulty)
        language_vo = SignLanguage(command.language)

        course = Course(
            id=uuid4(),
            title=command.title.strip(),
            description=command.description.strip(),
            difficulty=difficulty_vo,
            language=language_vo,
            status=ContentStatus.DRAFT,
            createdAt=datetime.now(timezone.utc),
        )
        await self._course_repo.save(course)
        return self._to_dto(course)

    async def updateCourse(self, command: UpdateCourseCommand) -> CourseDTO:
        course = await self._course_repo.get_by_id(command.courseId)
        if course is None:
            raise CourseNotFoundError(f"Course with ID '{command.courseId}' not found.")

        difficulty_vo = Difficulty(command.difficulty)
        language_vo = SignLanguage(command.language)

        course.update_info(
            title=command.title.strip(),
            description=command.description.strip(),
            difficulty=difficulty_vo,
            language=language_vo,
        )
        await self._course_repo.save(course)
        return self._to_dto(course)

    async def publishCourse(self, course_id: UUID) -> CourseDTO:
        course = await self._course_repo.get_by_id(course_id)
        if course is None:
            raise CourseNotFoundError(f"Course with ID '{course_id}' not found.")

        course.publish()
        await self._course_repo.save(course)
        return self._to_dto(course)

    async def archiveCourse(self, course_id: UUID) -> CourseDTO:
        course = await self._course_repo.get_by_id(course_id)
        if course is None:
            raise CourseNotFoundError(f"Course with ID '{course_id}' not found.")

        course.archive()
        await self._course_repo.save(course)
        return self._to_dto(course)

    async def deleteCourse(self, course_id: UUID) -> None:
        course = await self._course_repo.get_by_id(course_id)
        if course is None:
            raise CourseNotFoundError(f"Course with ID '{course_id}' not found.")
        await self._course_repo.delete(course_id)

    async def getCourse(self, course_id: UUID) -> CourseDTO | None:
        course = await self._course_repo.get_by_id(course_id)
        return self._to_dto(course) if course else None

    async def getCourseDetails(self, course_id: UUID) -> CourseDetailsDTO | None:
        course = await self._course_repo.get_by_id(course_id)
        if course is None:
            return None

        units = await self._unit_repo.list_by_course(course.id)
        units_dto: list[UnitDetailsDTO] = []
        for unit in units:
            lessons = await self._lesson_repo.list_by_unit(unit.id)
            lessons_dto = [
                LessonDTO(
                    id=l.id,
                    unitId=l.unitId,
                    title=l.title,
                    description=l.description,
                    order=l.order,
                    status=l.status.value,
                )
                for l in lessons
            ]
            units_dto.append(
                UnitDetailsDTO(
                    id=unit.id,
                    courseId=unit.courseId,
                    title=unit.title,
                    order=unit.order,
                    lessons=lessons_dto,
                )
            )

        return CourseDetailsDTO(
            id=course.id,
            title=course.title,
            description=course.description,
            difficulty=course.difficulty.value,
            language=course.language.value,
            status=course.status.value,
            createdAt=course.createdAt,
            units=units_dto,
        )

    async def listCourses(
        self,
        language: str | None = None,
        difficulty: str | None = None,
        status: str | None = None,
    ) -> list[CourseDTO]:
        lang_vo = SignLanguage(language) if language else None
        diff_vo = Difficulty(difficulty) if difficulty else None
        stat_vo = ContentStatus(status) if status else None

        courses = await self._course_repo.list_all(
            language=lang_vo,
            difficulty=diff_vo,
            status=stat_vo,
        )
        return [self._to_dto(c) for c in courses]

    @staticmethod
    def _to_dto(course: Course) -> CourseDTO:
        return CourseDTO(
            id=course.id,
            title=course.title,
            description=course.description,
            difficulty=course.difficulty.value,
            language=course.language.value,
            status=course.status.value,
            createdAt=course.createdAt,
        )


class UnitApplicationServiceImpl(UnitApplicationService):
    """Implementation of UnitApplicationService."""

    def __init__(
        self,
        unit_repository: UnitRepository,
        course_repository: CourseRepository,
    ) -> None:
        self._unit_repo = unit_repository
        self._course_repo = course_repository

    async def createUnit(self, command: CreateUnitCommand) -> UnitDTO:
        course = await self._course_repo.get_by_id(command.courseId)
        if course is None:
            raise CourseNotFoundError(f"Course with ID '{command.courseId}' not found.")

        unit = Unit(
            id=uuid4(),
            courseId=command.courseId,
            title=command.title.strip(),
            order=command.order,
        )
        await self._unit_repo.save(unit)
        return self._to_dto(unit)

    async def updateUnit(self, command: UpdateUnitCommand) -> UnitDTO:
        unit = await self._unit_repo.get_by_id(command.unitId)
        if unit is None:
            raise UnitNotFoundError(f"Unit with ID '{command.unitId}' not found.")

        unit.title = command.title.strip()
        unit.reorder(command.order)
        await self._unit_repo.save(unit)
        return self._to_dto(unit)

    async def deleteUnit(self, unit_id: UUID) -> None:
        unit = await self._unit_repo.get_by_id(unit_id)
        if unit is None:
            raise UnitNotFoundError(f"Unit with ID '{unit_id}' not found.")
        await self._unit_repo.delete(unit_id)

    async def getUnit(self, unit_id: UUID) -> UnitDTO | None:
        unit = await self._unit_repo.get_by_id(unit_id)
        return self._to_dto(unit) if unit else None

    async def getUnitsByCourse(self, course_id: UUID) -> list[UnitDTO]:
        units = await self._unit_repo.list_by_course(course_id)
        return [self._to_dto(u) for u in units]

    @staticmethod
    def _to_dto(unit: Unit) -> UnitDTO:
        return UnitDTO(
            id=unit.id,
            courseId=unit.courseId,
            title=unit.title,
            order=unit.order,
        )


class LessonApplicationServiceImpl(LessonApplicationService):
    """Implementation of LessonApplicationService."""

    def __init__(
        self,
        lesson_repository: LessonRepository,
        unit_repository: UnitRepository,
        exercise_repository: ExerciseRepository,
    ) -> None:
        self._lesson_repo = lesson_repository
        self._unit_repo = unit_repository
        self._exercise_repo = exercise_repository

    async def createLesson(self, command: CreateLessonCommand) -> LessonDTO:
        unit = await self._unit_repo.get_by_id(command.unitId)
        if unit is None:
            raise UnitNotFoundError(f"Unit with ID '{command.unitId}' not found.")

        lesson = Lesson(
            id=uuid4(),
            unitId=command.unitId,
            title=command.title.strip(),
            description=command.description.strip(),
            order=command.order,
            status=ContentStatus.DRAFT,
        )
        await self._lesson_repo.save(lesson)
        return self._to_dto(lesson)

    async def updateLesson(self, command: UpdateLessonCommand) -> LessonDTO:
        lesson = await self._lesson_repo.get_by_id(command.lessonId)
        if lesson is None:
            raise LessonNotFoundError(f"Lesson with ID '{command.lessonId}' not found.")

        lesson.title = command.title.strip()
        lesson.description = command.description.strip()
        lesson.reorder(command.order)
        await self._lesson_repo.save(lesson)
        return self._to_dto(lesson)

    async def publishLesson(self, lesson_id: UUID) -> LessonDTO:
        lesson = await self._lesson_repo.get_by_id(lesson_id)
        if lesson is None:
            raise LessonNotFoundError(f"Lesson with ID '{lesson_id}' not found.")

        lesson.publish()
        await self._lesson_repo.save(lesson)
        return self._to_dto(lesson)

    async def deleteLesson(self, lesson_id: UUID) -> None:
        lesson = await self._lesson_repo.get_by_id(lesson_id)
        if lesson is None:
            raise LessonNotFoundError(f"Lesson with ID '{lesson_id}' not found.")
        await self._lesson_repo.delete(lesson_id)

    async def getLesson(self, lesson_id: UUID) -> LessonDTO | None:
        lesson = await self._lesson_repo.get_by_id(lesson_id)
        return self._to_dto(lesson) if lesson else None

    async def getLessonDetails(self, lesson_id: UUID) -> LessonDetailsDTO | None:
        lesson = await self._lesson_repo.get_by_id(lesson_id)
        if lesson is None:
            return None

        exercises = await self._exercise_repo.list_by_lesson(lesson.id)
        exercises_dto = [
            ExercisePublicDTO(
                id=e.id,
                lessonId=e.lessonId,
                type=e.type.value,
                difficulty=e.difficulty.value,
                points=e.points,
                content=e.content,
                media=[
                    MediaDTO(
                        id=m.id,
                        exerciseId=m.exerciseId,
                        type=m.type.value,
                        url=m.url,
                    )
                    for m in e.media
                ],
            )
            for e in exercises
        ]

        return LessonDetailsDTO(
            id=lesson.id,
            unitId=lesson.unitId,
            title=lesson.title,
            description=lesson.description,
            order=lesson.order,
            status=lesson.status.value,
            exercises=exercises_dto,
        )

    async def getLessonsByUnit(self, unit_id: UUID) -> list[LessonDTO]:
        lessons = await self._lesson_repo.list_by_unit(unit_id)
        return [self._to_dto(l) for l in lessons]

    @staticmethod
    def _to_dto(lesson: Lesson) -> LessonDTO:
        return LessonDTO(
            id=lesson.id,
            unitId=lesson.unitId,
            title=lesson.title,
            description=lesson.description,
            order=lesson.order,
            status=lesson.status.value,
        )


class ExerciseApplicationServiceImpl(ExerciseApplicationService):
    """Implementation of ExerciseApplicationService."""

    def __init__(
        self,
        exercise_repository: ExerciseRepository,
        lesson_repository: LessonRepository,
    ) -> None:
        self._exercise_repo = exercise_repository
        self._lesson_repo = lesson_repository

    async def createExercise(self, command: CreateExerciseCommand) -> ExerciseDTO:
        lesson = await self._lesson_repo.get_by_id(command.lessonId)
        if lesson is None:
            raise LessonNotFoundError(f"Lesson with ID '{command.lessonId}' not found.")

        type_vo = ExerciseType(command.type)
        difficulty_vo = Difficulty(command.difficulty)

        exercise_id = uuid4()
        media_entities = [
            Media(
                id=uuid4(),
                exerciseId=exercise_id,
                type=MediaType(m.type),
                url=m.url.strip(),
            )
            for m in command.mediaList
        ]

        exercise = Exercise(
            id=exercise_id,
            lessonId=command.lessonId,
            type=type_vo,
            difficulty=difficulty_vo,
            points=command.points,
            content=command.content.strip(),
            answer=command.answer.strip(),
            media=media_entities,
        )
        await self._exercise_repo.save(exercise)
        return self._to_dto(exercise)

    async def updateExercise(self, command: UpdateExerciseCommand) -> ExerciseDTO:
        exercise = await self._exercise_repo.get_by_id(command.exerciseId)
        if exercise is None:
            raise ExerciseNotFoundError(f"Exercise with ID '{command.exerciseId}' not found.")

        exercise.type = ExerciseType(command.type)
        exercise.difficulty = Difficulty(command.difficulty)
        exercise.points = command.points
        exercise.content = command.content.strip()
        exercise.answer = command.answer.strip()

        await self._exercise_repo.save(exercise)
        return self._to_dto(exercise)

    async def deleteExercise(self, exercise_id: UUID) -> None:
        exercise = await self._exercise_repo.get_by_id(exercise_id)
        if exercise is None:
            raise ExerciseNotFoundError(f"Exercise with ID '{exercise_id}' not found.")
        await self._exercise_repo.delete(exercise_id)

    async def getExercise(self, exercise_id: UUID) -> ExerciseDTO | None:
        exercise = await self._exercise_repo.get_by_id(exercise_id)
        return self._to_dto(exercise) if exercise else None

    async def getExercisePublic(self, exercise_id: UUID) -> ExercisePublicDTO | None:
        exercise = await self._exercise_repo.get_by_id(exercise_id)
        return self._to_public_dto(exercise) if exercise else None

    async def getExercisesByLesson(self, lesson_id: UUID) -> list[ExercisePublicDTO]:
        exercises = await self._exercise_repo.list_by_lesson(lesson_id)
        return [self._to_public_dto(e) for e in exercises]

    async def validateAnswer(self, command: ValidateAnswerCommand) -> ValidationResultDTO:
        exercise = await self._exercise_repo.get_by_id(command.exerciseId)
        if exercise is None:
            raise ExerciseNotFoundError(f"Exercise with ID '{command.exerciseId}' not found.")

        is_correct, earned_points = exercise.validate_answer(command.submittedAnswer)
        feedback = (
            "Well done! Sign matched accurately."
            if is_correct
            else f"Sign did not match. Expected: '{exercise.answer}'"
        )

        return ValidationResultDTO(
            isCorrect=is_correct,
            earnedPoints=earned_points,
            expectedAnswer=exercise.answer,
            feedback=feedback,
        )

    @staticmethod
    def _to_dto(exercise: Exercise) -> ExerciseDTO:
        return ExerciseDTO(
            id=exercise.id,
            lessonId=exercise.lessonId,
            type=exercise.type.value,
            difficulty=exercise.difficulty.value,
            points=exercise.points,
            content=exercise.content,
            answer=exercise.answer,
            media=[
                MediaDTO(
                    id=m.id,
                    exerciseId=m.exerciseId,
                    type=m.type.value,
                    url=m.url,
                )
                for m in exercise.media
            ],
        )

    @staticmethod
    def _to_public_dto(exercise: Exercise) -> ExercisePublicDTO:
        return ExercisePublicDTO(
            id=exercise.id,
            lessonId=exercise.lessonId,
            type=exercise.type.value,
            difficulty=exercise.difficulty.value,
            points=exercise.points,
            content=exercise.content,
            media=[
                MediaDTO(
                    id=m.id,
                    exerciseId=m.exerciseId,
                    type=m.type.value,
                    url=m.url,
                )
                for m in exercise.media
            ],
        )
