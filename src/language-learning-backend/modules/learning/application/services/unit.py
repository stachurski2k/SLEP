from uuid import UUID, uuid4

from ...domain.entities import Unit
from ...domain.exceptions import CourseNotFoundError, UnitNotFoundError
from ...domain.repositories import CourseRepository, UnitRepository
from ..commands import CreateUnitCommand, UpdateUnitCommand
from ..dtos import UnitDTO
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
