from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_user
from app.crud.task_config import crud_task_config
from app.schemas.task_config import TaskConfigCreate, TaskConfigUpdate, TaskConfigResponse

router = APIRouter(prefix="/task-configs", tags=["task-configs"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[TaskConfigResponse])
async def list_configs(db: AsyncSession = Depends(get_db)):
    items, _ = await crud_task_config.get_multi(db, offset=0, limit=100)
    return items


@router.get("/{config_id}", response_model=TaskConfigResponse)
async def get_config(config_id: int, db: AsyncSession = Depends(get_db)):
    obj = await crud_task_config.get(db, config_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Task config not found")
    return obj


@router.post("", response_model=TaskConfigResponse, status_code=201)
async def create_config(body: TaskConfigCreate, db: AsyncSession = Depends(get_db)):
    return await crud_task_config.create(db, obj_in=body)


@router.put("/{config_id}", response_model=TaskConfigResponse)
async def update_config(config_id: int, body: TaskConfigUpdate, db: AsyncSession = Depends(get_db)):
    obj = await crud_task_config.get(db, config_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Task config not found")
    return await crud_task_config.update(db, db_obj=obj, obj_in=body)


@router.delete("/{config_id}", status_code=204)
async def delete_config(config_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await crud_task_config.delete(db, id=config_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task config not found")
