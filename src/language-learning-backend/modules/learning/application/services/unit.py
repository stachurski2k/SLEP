from uuid import UUID, uuid4

from ...domain.entities import Unit
from ...domain.exceptions import CourseNotFoundError, UnitNotFoundError
from ...domain.repositories import CourseRepository, UnitRepository
from ..commands import CreateUnitCommand, UpdateUnitCommand
from ..interfaces import UnitApplicationService


class UnitApplicationServiceImpl(UnitApplicationService):
    """Implementation of UnitApplicationService."""

    def __init__(
        self,
        unit_repository: UnitRepository,
        course_repository: CourseRepository,
    ) -> None:
        self._unit_repo = unit_repository
        self._course_repo = course_repository

    async def createUnit(self, command: CreateUnitCommand) -> Unit:
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
        return unit

    async def updateUnit(self, command: UpdateUnitCommand) -> Unit:
        unit = await self._unit_repo.get_by_id(command.unitId)
        if unit is None:
            raise UnitNotFoundError(f"Unit with ID '{command.unitId}' not found.")

        unit.title = command.title.strip()
        unit.reorder(command.order)
        await self._unit_repo.save(unit)
        return unit

    async def deleteUnit(self, unit_id: UUID) -> None:
        unit = await self._unit_repo.get_by_id(unit_id)
        if unit is None:
            raise UnitNotFoundError(f"Unit with ID '{unit_id}' not found.")
        await self._unit_repo.delete(unit_id)

    async def getUnit(self, unit_id: UUID) -> Unit | None:
        return await self._unit_repo.get_by_id(unit_id)

    async def getUnitsByCourse(self, course_id: UUID) -> list[Unit]:
        return await self._unit_repo.list_by_course(course_id)
