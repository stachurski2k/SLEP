from datetime import datetime, timezone
from uuid import UUID, uuid4

from ...domain.entities import Course
from ...domain.exceptions import CourseNotFoundError
from ...domain.repositories import CourseRepository, LessonRepository, UnitRepository
from ...domain.value_objects import ContentStatus, Difficulty, SignLanguage
from ..commands import CreateCourseCommand, UpdateCourseCommand
from ..dtos import CourseDetailsDTO, CourseDTO, LessonDTO, UnitDetailsDTO
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
