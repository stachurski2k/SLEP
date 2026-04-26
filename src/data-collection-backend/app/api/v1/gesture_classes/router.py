from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.gesture_classes.schemas import GestureClassRequest
from app.crud.gesture_class import GestureClassCrud
from app.dependencies import get_db
from app.schemas.gesture_class import GestureClassSchema

router = APIRouter(prefix="/gesture-classes", tags=["gesture-classes"])


@router.post("/", response_model=GestureClassSchema)
async def create_gesture_class(body: GestureClassRequest, db: AsyncSession = Depends(get_db)):
    return await GestureClassCrud(db).create(body.name)


@router.get("/", response_model=list[GestureClassSchema])
async def list_gesture_classes(page: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await GestureClassCrud(db).read_list(page, limit)


@router.get("/{gesture_class_id}", response_model=GestureClassSchema)
async def get_gesture_class(gesture_class_id: int, db: AsyncSession = Depends(get_db)):
    result = await GestureClassCrud(db).read(gesture_class_id)
    if not result:
        raise HTTPException(status_code=404, detail="Gesture class not found")
    return result


@router.patch("/{gesture_class_id}", response_model=GestureClassSchema)
async def update_gesture_class(gesture_class_id: int, body: GestureClassRequest, db: AsyncSession = Depends(get_db)):
    result = await GestureClassCrud(db).update(gesture_class_id, body.name)
    if not result:
        raise HTTPException(status_code=404, detail="Gesture class not found")
    return result


@router.delete("/{gesture_class_id}", status_code=204)
async def delete_gesture_class(gesture_class_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await GestureClassCrud(db).delete(gesture_class_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Gesture class not found")
