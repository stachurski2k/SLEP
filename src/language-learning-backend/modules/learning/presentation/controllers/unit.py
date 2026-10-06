from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ...application.commands import CreateUnitCommand, UpdateUnitCommand
from ...application.interfaces import UnitApplicationService
from ...domain.exceptions import CourseNotFoundError, InvalidOrderError, UnitNotFoundError
from ..dependencies import get_unit_service
from ..schemas import UnitCreateRequest, UnitResponse, UnitUpdateRequest

unit_router = APIRouter(prefix="/units", tags=["Units"])


@unit_router.post("/for-course/{course_id}", response_model=UnitResponse, status_code=status.HTTP_201_CREATED)
async def create_unit(
    course_id: UUID,
    schema: UnitCreateRequest,
    service: UnitApplicationService = Depends(get_unit_service),
) -> UnitResponse:
    command = CreateUnitCommand(
        courseId=course_id,
        title=schema.title,
        order=schema.order,
    )
    try:
        unit = await service.createUnit(command)
        return UnitResponse.model_validate(unit)
    except CourseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidOrderError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@unit_router.get("/by-course/{course_id}", response_model=list[UnitResponse])
async def get_units_by_course(
    course_id: UUID,
    service: UnitApplicationService = Depends(get_unit_service),
) -> list[UnitResponse]:
    units = await service.getUnitsByCourse(course_id)
    return [UnitResponse.model_validate(u) for u in units]


@unit_router.get("/{unit_id}", response_model=UnitResponse)
async def get_unit(
    unit_id: UUID,
    service: UnitApplicationService = Depends(get_unit_service),
) -> UnitResponse:
    unit = await service.getUnit(unit_id)
    if unit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unit with ID '{unit_id}' not found.",
        )
    return UnitResponse.model_validate(unit)


@unit_router.put("/{unit_id}", response_model=UnitResponse)
async def update_unit(
    unit_id: UUID,
    schema: UnitUpdateRequest,
    service: UnitApplicationService = Depends(get_unit_service),
) -> UnitResponse:
    command = UpdateUnitCommand(
        unitId=unit_id,
        title=schema.title,
        order=schema.order,
    )
    try:
        unit = await service.updateUnit(command)
        return UnitResponse.model_validate(unit)
    except UnitNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidOrderError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@unit_router.delete("/{unit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_unit(
    unit_id: UUID,
    service: UnitApplicationService = Depends(get_unit_service),
) -> None:
    try:
        await service.deleteUnit(unit_id)
    except UnitNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
