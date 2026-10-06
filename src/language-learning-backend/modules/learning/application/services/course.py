from datetime import datetime, timezone
from uuid import UUID, uuid4

from ...domain.entities import Course
from ...domain.exceptions import CourseNotFoundError
from ...domain.repositories import CourseRepository, LessonRepository, UnitRepository
from ...domain.value_objects import ContentStatus, Difficulty, SignLanguage
from ..commands import CreateCourseCommand, UpdateCourseCommand
from ..interfaces import CourseApplicationService


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

    async def createCourse(self, command: CreateCourseCommand) -> Course:
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
        return course

    async def updateCourse(self, command: UpdateCourseCommand) -> Course:
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
        return course

    async def publishCourse(self, course_id: UUID) -> Course:
        course = await self._course_repo.get_by_id(course_id)
        if course is None:
            raise CourseNotFoundError(f"Course with ID '{course_id}' not found.")

        course.publish()
        await self._course_repo.save(course)
        return course

    async def archiveCourse(self, course_id: UUID) -> Course:
        course = await self._course_repo.get_by_id(course_id)
        if course is None:
            raise CourseNotFoundError(f"Course with ID '{course_id}' not found.")

        course.archive()
        await self._course_repo.save(course)
        return course

    async def deleteCourse(self, course_id: UUID) -> None:
        course = await self._course_repo.get_by_id(course_id)
        if course is None:
            raise CourseNotFoundError(f"Course with ID '{course_id}' not found.")
        await self._course_repo.delete(course_id)

    async def getCourse(self, course_id: UUID) -> Course | None:
        return await self._course_repo.get_by_id(course_id)

    async def getCourseDetails(self, course_id: UUID) -> Course | None:
        course = await self._course_repo.get_by_id(course_id)
        if course is None:
            return None

        # Ensure units and lessons hierarchy is populated if not eager loaded
        if not course.units:
            units = await self._unit_repo.list_by_course(course.id)
            for unit in units:
                if not unit.lessons:
                    unit.lessons = await self._lesson_repo.list_by_unit(unit.id)
            course.units = units
        else:
            for unit in course.units:
                if not unit.lessons:
                    unit.lessons = await self._lesson_repo.list_by_unit(unit.id)

        return course

    async def listCourses(
        self,
        language: str | None = None,
        difficulty: str | None = None,
        status: str | None = None,
    ) -> list[Course]:
        lang_vo = SignLanguage(language) if language else None
        diff_vo = Difficulty(difficulty) if difficulty else None
        stat_vo = ContentStatus(status) if status else None

        return await self._course_repo.list_all(
            language=lang_vo,
            difficulty=diff_vo,
            status=stat_vo,
        )
