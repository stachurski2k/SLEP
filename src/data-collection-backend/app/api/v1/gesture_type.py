from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.crud.gesture_type import GestureTypeCrud
from app.schemas.gesture_type import GestureTypeSchema
from pydantic import BaseModel

router = APIRouter(prefix="/gesture-types", tags=["gesture-types"])


class GestureTypeBody(BaseModel):
    name: str


@router.post("/", response_model=GestureTypeSchema)
async def create_gesture_type(body: GestureTypeBody, db: AsyncSession = Depends(get_db)):
    return await GestureTypeCrud(db).create(body.name)


@router.get("/", response_model=list[GestureTypeSchema])
async def list_gesture_types(page: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await GestureTypeCrud(db).read_list(page, limit)


@router.get("/{gesture_type_id}", response_model=GestureTypeSchema)
async def get_gesture_type(gesture_type_id: int, db: AsyncSession = Depends(get_db)):
    result = await GestureTypeCrud(db).read(gesture_type_id)
    if not result:
        raise HTTPException(status_code=404, detail="Gesture type not found")
    return result


@router.patch("/{gesture_type_id}", response_model=GestureTypeSchema)
async def update_gesture_type(gesture_type_id: int, body: GestureTypeBody, db: AsyncSession = Depends(get_db)):
    result = await GestureTypeCrud(db).update(gesture_type_id, body.name)
    if not result:
        raise HTTPException(status_code=404, detail="Gesture type not found")
    return result


@router.delete("/{gesture_type_id}", status_code=204)
async def delete_gesture_type(gesture_type_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await GestureTypeCrud(db).delete(gesture_type_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Gesture type not found")